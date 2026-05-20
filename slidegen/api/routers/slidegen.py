import json
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, StreamingResponse
from loguru import logger
from pydantic import BaseModel, Field
from sqlmodel import select

from slidegen.api.deps import CurrentUser, SessionDep
from slidegen.core.config import settings
from slidegen.exceptions import AccessDeniedError, InsideServerError, NotFoundError, PPTTemplateError
from slidegen.middleware.rate_limiter import sse_rate_limiter
from slidegen.models.task_ownership import TaskOwnership
from slidegen.schemas.async_task import AsyncTaskResponse
from slidegen.schemas.gen_request import (
    ExportFormat,
    GenerateMarkdownRequest,
    GeneratePresentationRequest,
    MarkdownToPPTRequest,
    Tone,
    Verbosity,
)
from slidegen.schemas.template import Template
from slidegen.schemas.theme import ThemePresets
from slidegen.services import presentation_generator
from slidegen.services.presentation.thumbnail import (
    LibreOfficeNotFoundError,
    ThumbnailGenerationError,
    thumbnail_generator,
)
from slidegen.services.slidegen import run_slidegen_workflow_stream
from slidegen.tasks import celery_app
from slidegen.tasks.slidegen_tasks import generate_presentation_task

router = APIRouter()

OUTPUT_DIR = settings.OUTPUT_DIR


class SlideGenTask(BaseModel):
    """Slide generation task"""

    topic: str = Field(..., description="Slide topic")
    llm_config_id: uuid.UUID | None = Field(default=None, description="LLM config ID")
    model_id: str | None = Field(default=None, description="Model ID")
    instructions: str | None = Field(default=None, description="Instructions")
    tone: str = Field(default="default", description="Tone")
    verbosity: str = Field(default="standard", description="Verbosity")
    web_search: bool = Field(default=False, description="Web search")
    n_slides: int = Field(default=8, description="Number of slides")
    language: str = Field(default="English", description="Language")
    template: str = Field(default="general", description="Template name (e.g., 'general', 'purple')")
    include_table_of_contents: bool = Field(default=False, description="Include table of contents")
    include_title_slide: bool = Field(default=True, description="Include title slide")
    file_ids: list[str] | None = Field(default=None, description="File IDs uploaded by user")
    export_as: ExportFormat = Field(default=ExportFormat.PPTX, description="Export as")


class SlideGenResult(BaseModel):
    """Slide generation result"""

    success: bool = Field(description="Success")
    result: Any | None = Field(default=None, description="Result")
    error: str | None = Field(default=None, description="Error")
    message: str = Field(description="Message")


@router.post("/generate", response_model=SlideGenResult)
async def generate_slides(task: SlideGenTask, current_user: CurrentUser) -> Any:
    """Slide generation"""
    try:
        # Generate unique output file name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{task.topic[:30]}_{timestamp}_{uuid.uuid4().hex[:8]}.{task.export_as.value}"
        output_path = str(OUTPUT_DIR / filename)

        # Create unified presentation generation request
        # Convert enum types
        tone = Tone(task.tone) if task.tone in [t.value for t in Tone] else Tone.DEFAULT
        verbosity = Verbosity(task.verbosity) if task.verbosity in [v.value for v in Verbosity] else Verbosity.STANDARD

        request = GeneratePresentationRequest(
            content=task.topic,
            instructions=task.instructions,
            tone=tone,
            verbosity=verbosity,
            web_search=task.web_search,
            n_slides=task.n_slides,
            language=task.language,
            template=task.template,
            include_table_of_contents=task.include_table_of_contents,
            include_title_slide=task.include_title_slide,
            files=task.file_ids,
            export_as=task.export_as,
            user_id=current_user.id,
            llm_config_id=task.llm_config_id,
        )

        logger.info(f"Generating presentation for user {current_user.id}: {task.topic}")
        result_path = await presentation_generator.generate_presentation(
            request=request,
            output_path=output_path,
        )

        logger.info(f"Presentation generated successfully: {result_path}")

        return SlideGenResult(
            success=True,
            result={
                "output_path": result_path,
                "filename": filename,
                "download_url": f"/api/v1/slidegen/download/{filename}",
            },
            message="presentation generated successfully",
        )

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return SlideGenResult(success=False, error=str(e), message="template file not found")
    except Exception as e:
        logger.exception(f"Failed to generate presentation: {e}")
        return SlideGenResult(success=False, error=str(e), message="failed to generate presentation")


@router.post("/generate-async", response_model=AsyncTaskResponse)
async def generate_slides_async(
    task: SlideGenTask, current_user: CurrentUser, db_session: SessionDep
) -> AsyncTaskResponse:
    """async generate presentation (return task ID)"""
    # Prepare task data (convert to JSON-serializable dict)
    task_data = {
        "topic": task.topic,
        "user_id": str(current_user.id),
        "llm_config_id": str(task.llm_config_id) if task.llm_config_id else None,
        "instructions": task.instructions,
        "tone": task.tone,
        "verbosity": task.verbosity,
        "web_search": task.web_search,
        "n_slides": task.n_slides,
        "language": task.language,
        "template": task.template,
        "include_table_of_contents": task.include_table_of_contents,
        "include_title_slide": task.include_title_slide,
        "file_ids": task.file_ids,
        "export_as": task.export_as.value,
    }

    logger.info(f"Submitting async presentation generation task for user {current_user.id}: {task.topic}")

    # Submit task to Celery
    celery_task = generate_presentation_task.delay(task_data)

    # Store task ownership for access control
    task_ownership = TaskOwnership(
        task_id=celery_task.id,
        user_id=current_user.id,
    )
    db_session.add(task_ownership)
    await db_session.commit()

    return AsyncTaskResponse(
        task_id=celery_task.id,
        status="pending",
        message="task submitted, please use task ID to query result",
    )


@router.post(
    "/generate-stream",
    description="Stream content generation with SSE (without PPTX)",
    dependencies=[Depends(sse_rate_limiter)],
)
async def generate_slides_stream(task: SlideGenTask, current_user: CurrentUser) -> StreamingResponse:
    """Stream content generation progress via Server-Sent Events (SSE)

    This endpoint streams the content generation progress in real-time.
    Note: This only streams the content generation, not the PPTX file creation.
    Use /generate-stream-full for complete streaming including PPTX generation.

    Events sent:
    - workflow_started: Generation started
    - step_started/step_completed: Individual step progress
    - loop_iteration_completed: Section generation progress with content
    - progress: Progress percentage updates
    - content_generated: Generated content (outline, sections)
    - workflow_completed: Final generated content
    - workflow_error: Error occurred

    Example SSE event format:
    ```
    event: step_started
    data: {"event": "step_started", "step_name": "Outline generation", "message": "..."}
    ```
    """

    # Convert task to GeneratePresentationRequest
    tone = Tone(task.tone) if task.tone in [t.value for t in Tone] else Tone.DEFAULT
    verbosity = Verbosity(task.verbosity) if task.verbosity in [v.value for v in Verbosity] else Verbosity.STANDARD

    request = GeneratePresentationRequest(
        content=task.topic,
        instructions=task.instructions,
        tone=tone,
        verbosity=verbosity,
        web_search=task.web_search,
        n_slides=task.n_slides,
        language=task.language,
        template=task.template,
        include_table_of_contents=task.include_table_of_contents,
        include_title_slide=task.include_title_slide,
        files=task.file_ids,
        export_as=task.export_as,
        user_id=current_user.id,
        llm_config_id=task.llm_config_id,
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events from workflow stream"""
        try:
            async for event in run_slidegen_workflow_stream(request):
                # Convert Pydantic model to dict and then to JSON
                event_data = event.model_dump()
                event_type = event_data.get("event", "message")

                # Format as SSE: event: <type>\ndata: <json>\n\n
                yield f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"

        except Exception as e:
            logger.exception(f"Error in SSE stream: {e}")
            error_event = {
                "event": "workflow_error",
                "error": str(e),
                "message": "Stream error occurred",
            }
            yield f"event: workflow_error\ndata: {json.dumps(error_event)}\n\n"

    logger.info(f"Starting streaming generation for user {current_user.id}: {task.topic}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        },
    )


@router.post(
    "/generate-markdown-stream",
    description="Stream markdown content generation only (no PPT conversion)",
    dependencies=[Depends(sse_rate_limiter)],
)
async def generate_markdown_stream(request: GenerateMarkdownRequest, current_user: CurrentUser) -> StreamingResponse:
    """Stream markdown content generation via Server-Sent Events (SSE).

    This endpoint ONLY generates markdown content without converting to PPT.
    Use this endpoint when you want to:
    1. Generate markdown content
    2. Allow user to edit the markdown
    3. Then call /generate-pptx-from-markdown to create PPT from the edited markdown

    The final event (workflow_completed) contains the complete markdown content
    that can be displayed to the user for editing.

    Events sent:
    - workflow_started: Generation started
    - step_started/step_completed: Individual step progress
    - loop_progress: Section generation progress with content
    - progress: Progress percentage updates
    - content_generated: Generated content (outline, sections)
    - workflow_completed: Final event with complete markdown content
    - workflow_error: Error occurred

    Example SSE event format:
    ```
    event: workflow_completed
    data: {"event": "workflow_completed", "content": "# Title\\n## Section 1\\n..."}
    ```
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events from workflow stream"""
        try:
            async for event in run_slidegen_workflow_stream(request):
                # Convert Pydantic model to dict and then to JSON
                event_data = event.model_dump()
                event_type = event_data.get("event", "message")

                # Format as SSE: event: <type>\ndata: <json>\n\n
                yield f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"

        except Exception as e:
            logger.exception(f"Error in SSE stream: {e}")
            error_event = {
                "event": "workflow_error",
                "error": str(e),
                "message": "Stream error occurred",
            }
            yield f"event: workflow_error\ndata: {json.dumps(error_event)}\n\n"

    logger.info(f"Starting markdown generation stream for user {current_user.id}: {request.content[:50]}...")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        },
    )


@router.post(
    "/generate-stream-full",
    description="Stream full presentation generation with SSE",
    dependencies=[Depends(sse_rate_limiter)],
)
async def generate_slides_stream_full(task: SlideGenTask, current_user: CurrentUser) -> StreamingResponse:
    """Stream full presentation generation progress via Server-Sent Events (SSE)

    This endpoint streams the complete generation progress including:
    1. Content generation (outline, sections)
    2. PPTX file conversion and saving

    The final event will include the download URL for the generated presentation.

    Events sent:
    - workflow_started: Generation started
    - step_started/step_completed: Individual step progress
    - loop_iteration_completed: Section generation progress with content
    - progress: Progress percentage updates
    - content_generated: Generated content (outline, sections)
    - workflow_completed: Content generation completed
    - pptx_conversion: PPTX conversion progress
    - generation_completed: Final event with download URL
    - workflow_error: Error occurred

    Example SSE event format:
    ```
    event: generation_completed
    data: {"event": "generation_completed", "download_url": "/api/v1/slidegen/download/xxx.pptx"}
    ```
    """

    # Generate unique output file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{task.topic[:30]}_{timestamp}_{uuid.uuid4().hex[:8]}.{task.export_as.value}"
    output_path = str(OUTPUT_DIR / filename)

    # Convert task to GeneratePresentationRequest
    tone = Tone(task.tone) if task.tone in [t.value for t in Tone] else Tone.DEFAULT
    verbosity = Verbosity(task.verbosity) if task.verbosity in [v.value for v in Verbosity] else Verbosity.STANDARD

    request = GeneratePresentationRequest(
        content=task.topic,
        instructions=task.instructions,
        tone=tone,
        verbosity=verbosity,
        web_search=task.web_search,
        n_slides=task.n_slides,
        language=task.language,
        template=task.template,
        include_table_of_contents=task.include_table_of_contents,
        include_title_slide=task.include_title_slide,
        files=task.file_ids,
        export_as=task.export_as,
        user_id=current_user.id,
        llm_config_id=task.llm_config_id,
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events from full presentation generation stream"""
        try:
            async for event in presentation_generator.generate_presentation_stream(request, output_path):
                # Convert Pydantic model to dict and then to JSON
                event_data = event.model_dump()
                event_type = event_data.get("event", "message")

                # Format as SSE: event: <type>\ndata: <json>\n\n
                yield f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"

                # Check if this is the final PPTX conversion completion
                if event_type == "step_completed" and event_data.get("step_name") == "Presentation Export":
                    # Emit final completion event with download URL
                    final_event = {
                        "event": "generation_completed",
                        "output_path": output_path,
                        "filename": filename,
                        "download_url": f"/api/v1/slidegen/download/{filename}",
                        "message": "Presentation generated successfully",
                    }
                    yield f"event: generation_completed\ndata: {json.dumps(final_event)}\n\n"

        except Exception as e:
            logger.exception(f"Error in SSE stream: {e}")
            error_event = {
                "event": "workflow_error",
                "error": str(e),
                "message": "Stream error occurred",
            }
            yield f"event: workflow_error\ndata: {json.dumps(error_event)}\n\n"

    logger.info(f"Starting full streaming generation for user {current_user.id}: {task.topic}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        },
    )


@router.post("/generate-pptx-from-markdown", response_model=SlideGenResult)
async def generate_pptx_from_markdown(request: MarkdownToPPTRequest, current_user: CurrentUser) -> SlideGenResult:
    """Generate PPT directly from user-provided markdown content.

    This endpoint allows users to:
    1. First use /generate-stream to get AI-generated markdown content
    2. Edit the markdown content as needed
    3. Then use this endpoint to convert the final markdown to PPT

    Args:
        request: MarkdownToPPTRequest containing the markdown content and template

    Returns:
        SlideGenResult with download URL for the generated presentation
    """
    try:
        # Generate unique output file name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"presentation_{timestamp}_{uuid.uuid4().hex[:8]}.{request.export_as.value}"
        output_path = str(OUTPUT_DIR / filename)

        logger.info(f"Generating PPT from markdown for user {current_user.id}")
        result_path = await presentation_generator.generate_from_markdown(
            markdown_content=request.markdown_content,
            template_name=request.template,
            output_path=output_path,
            export_as=request.export_as,
            theme_preset=request.theme_preset,
            user_id=current_user.id,
        )

        logger.info(f"Presentation generated successfully: {result_path}")

        return SlideGenResult(
            success=True,
            result={
                "output_path": result_path,
                "filename": filename,
                "download_url": f"/api/v1/slidegen/download/{filename}",
            },
            message="presentation generated successfully from markdown",
        )

    except FileNotFoundError as e:
        logger.error(f"Template file not found: {e}")
        return SlideGenResult(success=False, error=str(e), message="template file not found")
    except ValueError as e:
        logger.error(f"Unsupported export format: {e}")
        return SlideGenResult(success=False, error=str(e), message="unsupported export format")
    except Exception as e:
        logger.exception(f"Failed to generate presentation from markdown: {e}")
        return SlideGenResult(success=False, error=str(e), message="failed to generate presentation")


@router.post(
    "/generate-pptx-from-markdown-stream",
    description="Generate PPT from markdown with SSE progress updates",
    dependencies=[Depends(sse_rate_limiter)],
)
async def generate_pptx_from_markdown_stream(
    request: MarkdownToPPTRequest, current_user: CurrentUser
) -> StreamingResponse:
    """Generate PPT from user-provided markdown content with streaming progress.

    This endpoint provides real-time progress updates during PPT generation.
    Use this when you want to show the user the conversion progress.

    Events sent:
    - step_started: Conversion started
    - progress: Progress percentage updates
    - step_completed: Conversion completed
    - generation_completed: Final event with download URL
    - workflow_error: Error occurred

    Example SSE event format:
    ```
    event: generation_completed
    data: {"event": "generation_completed", "download_url": "/api/v1/slidegen/download/xxx.pptx"}
    ```
    """

    # Generate unique output file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"presentation_{timestamp}_{uuid.uuid4().hex[:8]}.{request.export_as.value}"
    output_path = str(OUTPUT_DIR / filename)

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events from markdown to PPT conversion"""
        try:
            async for event in presentation_generator.generate_from_markdown_stream(
                markdown_content=request.markdown_content,
                template_name=request.template,
                output_path=output_path,
                export_as=request.export_as,
                theme_preset=request.theme_preset,
                user_id=current_user.id,
            ):
                # Convert Pydantic model to dict and then to JSON
                event_data = event.model_dump()
                event_type = event_data.get("event", "message")

                # Format as SSE: event: <type>\ndata: <json>\n\n
                yield f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"

                # Check if this is the final PPTX conversion completion
                if event_type == "step_completed" and event_data.get("step_name") == "Presentation Export":
                    # Emit final completion event with download URL
                    final_event = {
                        "event": "generation_completed",
                        "output_path": output_path,
                        "filename": filename,
                        "download_url": f"/api/v1/slidegen/download/{filename}",
                        "message": "Presentation generated successfully from markdown",
                    }
                    yield f"event: generation_completed\ndata: {json.dumps(final_event)}\n\n"

        except Exception as e:
            logger.exception(f"Error in SSE stream: {e}")
            error_event = {
                "event": "workflow_error",
                "error": str(e),
                "message": "Stream error occurred",
            }
            yield f"event: workflow_error\ndata: {json.dumps(error_event)}\n\n"

    logger.info(f"Starting streaming PPT generation from markdown for user {current_user.id}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        },
    )


@router.get("/task/{task_id}", response_model=AsyncTaskResponse)
async def get_task_status(task_id: str, current_user: CurrentUser, db_session: SessionDep) -> AsyncTaskResponse:
    """query async task status"""

    task_ownership_stmt = select(TaskOwnership).where(
        TaskOwnership.task_id == task_id, TaskOwnership.user_id == current_user.id
    )
    task_ownership = (await db_session.execute(task_ownership_stmt)).scalar_one_or_none()

    if not task_ownership:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Task not found")

    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.state == "PENDING":
        return AsyncTaskResponse(
            task_id=task_id,
            status="pending",
            message="task waiting",
        )
    elif task_result.state == "STARTED":
        return AsyncTaskResponse(
            task_id=task_id,
            status="processing",
            message="task processing",
        )
    elif task_result.state == "SUCCESS":
        result = task_result.result
        if result and result.get("success"):
            return AsyncTaskResponse(
                task_id=task_id,
                status="completed",
                message="task completed",
                result=result,
            )
        else:
            return AsyncTaskResponse(
                task_id=task_id,
                status="failed",
                message=result.get("error", "task execution failed") if result else "task execution failed",
                result=result,
            )
    elif task_result.state == "FAILURE":
        return AsyncTaskResponse(
            task_id=task_id,
            status="failed",
            message=str(task_result.info),
        )
    else:
        return AsyncTaskResponse(
            task_id=task_id,
            status=task_result.state.lower(),
            message=f"task status: {task_result.state}",
        )


@router.get("/templates", response_model=list[Template], description="get available templates")
async def get_available_templates() -> list[Template]:
    try:
        template_names = presentation_generator.list_templates()
        templates = [
            Template(
                id=name,
                name=name.replace("_", " ").title(),
                thumbnail=f"/api/v1/slidegen/templates/{name}/thumbnail",
            )
            for name in template_names
        ]
        logger.info(f"Found {len(templates)} templates")
        return templates

    except Exception as e:
        logger.exception(f"Failed to list templates: {e}")
        raise PPTTemplateError(message=f"failed to list templates: {str(e)}")


@router.get("/theme-presets", description="get available theme presets")
def get_theme_presets() -> dict[str, list[dict[str, str]]]:
    presets: list[dict[str, str]] = []
    for preset_id in ThemePresets.list_presets():
        preset = ThemePresets.get_preset(preset_id)
        if preset is None:
            logger.warning(f"Theme preset listed but not found: {preset_id}")
            continue
        presets.append({"id": preset_id, "name": preset.name})
    return {"presets": presets}


@router.get("/download/{filename}", description="download generated presentation")
async def download_presentation(filename: str) -> FileResponse:
    """download generated presentation"""
    try:
        file_path = OUTPUT_DIR / filename

        if not file_path.exists():
            raise NotFoundError(message="file not found")

        if not str(file_path.resolve()).startswith(str(OUTPUT_DIR.resolve())):
            raise AccessDeniedError(message="access denied")

        if filename.endswith(".pdf"):
            media_type = "application/pdf"
        else:
            media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type=media_type,
        )

    except (NotFoundError, AccessDeniedError):
        raise
    except Exception as e:
        logger.exception(f"Failed to download file {filename}: {e}")
        raise InsideServerError(message=f"failed to download file: {str(e)}")


@router.get("/templates/{template_name}/thumbnail", description="get template thumbnail")
async def get_template_thumbnail(template_name: str) -> FileResponse:
    """Get template thumbnail.

    Generates a high-quality thumbnail using LibreOffice to convert PPTX to PDF,
    then PyMuPDF to render the first page as PNG. Thumbnails are cached in the
    thumbnails directory and regenerated when the template is modified.
    """
    try:
        # Validate template name to prevent directory traversal
        if not template_name.replace("_", "").isalnum():
            raise AccessDeniedError(message="invalid template name")

        # Generate or retrieve cached thumbnail
        thumbnail_path = thumbnail_generator.generate_thumbnail(template_name)

        return FileResponse(
            path=str(thumbnail_path),
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=3600"},
        )

    except FileNotFoundError:
        raise NotFoundError(message="template not found")
    except LibreOfficeNotFoundError as e:
        logger.warning(f"LibreOffice not installed: {e}")
        raise InsideServerError(message="LibreOffice is required for thumbnail generation but is not installed")
    except ThumbnailGenerationError as e:
        logger.error(f"Thumbnail generation failed for {template_name}: {e}")
        raise InsideServerError(message=f"failed to generate thumbnail: {str(e)}")
    except AccessDeniedError:
        raise
    except Exception as e:
        logger.exception(f"Failed to get thumbnail for {template_name}: {e}")
        raise InsideServerError(message=f"failed to get thumbnail: {str(e)}")
