import uuid
from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter
from fastapi.responses import FileResponse
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
async def generate_slides_async(_task: SlideGenTask, _current_user: CurrentUser) -> AsyncTaskResponse:
    """异步生成幻灯片（返回任务ID）"""
    # TODO: 这里可以集成Celery来实现异步任务处理
    # 现在先返回一个简单的响应
    return AsyncTaskResponse(task_id=str(uuid.uuid4()), status="pending", message="任务已提交，请稍后查询结果")


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
