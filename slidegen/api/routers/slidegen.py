import json
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter
from fastapi.responses import FileResponse, StreamingResponse
from loguru import logger
from pydantic import BaseModel, Field

from slidegen.api.deps import CurrentUser
from slidegen.core.config import settings
from slidegen.exceptions import AccessDeniedError, InsideServerError, NotFoundError, PPTTemplateError
from slidegen.schemas.async_task import AsyncTaskResponse
from slidegen.schemas.gen_request import GeneratePresentationRequest, Tone, Verbosity
from slidegen.schemas.template import Template
from slidegen.services import presentation_generator

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
    export_as: str = Field(default="pptx", description="Export as")


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
        # Ensure output directory exists
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Generate unique output file name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{task.topic[:30]}_{timestamp}_{uuid.uuid4().hex[:8]}.pptx"
        output_path = str(OUTPUT_DIR / filename)

        # Create unified presentation generation request
        # Convert enum types
        tone = Tone(task.tone) if task.tone in [t.value for t in Tone] else Tone.DEFAULT
        verbosity = Verbosity(task.verbosity) if task.verbosity in [v.value for v in Verbosity] else Verbosity.STANDARD
        export_format: Literal["pptx", "pdf"] = "pptx" if task.export_as == "pptx" else "pdf"

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
            export_as=export_format,
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
async def generate_slides_async(task: SlideGenTask, current_user: CurrentUser) -> AsyncTaskResponse:
    """async generate presentation (return task ID)"""
    from slidegen.tasks.slidegen_tasks import generate_presentation_task

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
        "export_as": task.export_as,
    }

    logger.info(f"Submitting async presentation generation task for user {current_user.id}: {task.topic}")

    # Submit task to Celery
    celery_task = generate_presentation_task.delay(task_data)

    return AsyncTaskResponse(
        task_id=celery_task.id,
        status="pending",
        message="task submitted, please use task ID to query result",
    )


@router.post("/generate-stream", description="Stream content generation with SSE (without PPTX)")
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
    from slidegen.services.slidegen.workflow import run_slidegen_workflow_stream

    # Convert task to GeneratePresentationRequest
    tone = Tone(task.tone) if task.tone in [t.value for t in Tone] else Tone.DEFAULT
    verbosity = Verbosity(task.verbosity) if task.verbosity in [v.value for v in Verbosity] else Verbosity.STANDARD
    export_format: Literal["pptx", "pdf"] = "pptx" if task.export_as == "pptx" else "pdf"

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
        export_as=export_format,
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


@router.post("/generate-stream-full", description="Stream full presentation generation with SSE")
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
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Generate unique output file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{task.topic[:30]}_{timestamp}_{uuid.uuid4().hex[:8]}.pptx"
    output_path = str(OUTPUT_DIR / filename)

    # Convert task to GeneratePresentationRequest
    tone = Tone(task.tone) if task.tone in [t.value for t in Tone] else Tone.DEFAULT
    verbosity = Verbosity(task.verbosity) if task.verbosity in [v.value for v in Verbosity] else Verbosity.STANDARD
    export_format: Literal["pptx", "pdf"] = "pptx" if task.export_as == "pptx" else "pdf"

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
        export_as=export_format,
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
                if event_type == "step_completed" and event_data.get("step_name") == "PPTX Conversion":
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


@router.get("/task/{task_id}", response_model=AsyncTaskResponse)
async def get_task_status(task_id: str) -> AsyncTaskResponse:
    """query async task status"""
    from celery.result import AsyncResult

    from slidegen.tasks import celery_app

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
            )
            for name in template_names
        ]
        logger.info(f"Found {len(templates)} templates")
        return templates

    except Exception as e:
        logger.exception(f"Failed to list templates: {e}")
        raise PPTTemplateError(message=f"failed to list templates: {str(e)}")


@router.get("/download/{filename}", description="download generated presentation")
async def download_presentation(filename: str) -> FileResponse:
    """download generated presentation"""
    try:
        file_path = OUTPUT_DIR / filename

        if not file_path.exists():
            raise NotFoundError(message="file not found")

        if not str(file_path.resolve()).startswith(str(OUTPUT_DIR.resolve())):
            raise AccessDeniedError(message="access denied")

        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

    except (NotFoundError, AccessDeniedError):
        raise
    except Exception as e:
        logger.exception(f"Failed to download file {filename}: {e}")
        raise InsideServerError(message=f"failed to download file: {str(e)}")
