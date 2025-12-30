import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from loguru import logger
from pydantic import BaseModel, Field

from slidegen.api.deps import CurrentUser
from slidegen.factories.presentation_factory import PresentationController
from slidegen.schemas.gen_request import GeneratePresentationRequest, Tone, Verbosity

router = APIRouter(tags=["SlideGen"])

# 配置输出目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "presentations"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 初始化PresentationController
presentation_controller = PresentationController()


class SlideGenTask(BaseModel):
    """Slide generation task"""

    topic: str = Field(..., description="Slide topic")
    template_path: str = Field(..., description="Template path")
    output_path: str = Field(..., description="Output path")
    slides: int = Field(default=6, ge=3, le=20, description="Number of slides")
    llm_config_id: uuid.UUID | None = Field(default=None, description="LLM config ID")
    model_id: str | None = Field(default=None, description="Model ID")
    instructions: str | None = Field(default=None, description="Instructions")
    tone: str = Field(default="default", description="Tone")
    verbosity: str = Field(default="standard", description="Verbosity")
    web_search: bool = Field(default=False, description="Web search")
    n_slides: int = Field(default=8, description="Number of slides")
    language: str = Field(default="English", description="Language")
    template: str = Field(default="general", description="Template")
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
        # Generate unique output file name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{task.topic[:30]}_{timestamp}_{uuid.uuid4().hex[:8]}.pptx"
        output_path = str(OUTPUT_DIR / filename)

        # Determine template path
        template_path: str | None
        if task.template_path:
            template_path = task.template_path
        else:
            # Use default template
            template_path = str(PROJECT_ROOT / "test" / "data" / "template_0.pptx")

        # Verify template file exists
        if not os.path.exists(template_path):
            logger.warning(f"Template not found: {template_path}, using default")
            template_path = None  # Use default template from controller

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
            files=task.file_ids,  # Map file_ids to files
            export_as=export_format,
            user_id=current_user.id,
            llm_config_id=task.llm_config_id,
        )

        # 使用PresentationController生成PPTX
        logger.info(f"Generating presentation for user {current_user.id}: {task.topic}")
        result_path = await presentation_controller.generate_presentation(
            request=request,
            output_path=output_path,
            template_path=template_path,
        )

        logger.info(f"Presentation generated successfully: {result_path}")

        return SlideGenResult(
            success=True,
            result={
                "output_path": result_path,
                "filename": filename,
                "download_url": f"/api/v1/slidegen/download/{filename}",
            },
            message="幻灯片生成成功",
        )

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return SlideGenResult(success=False, error=str(e), message="模板文件未找到")
    except Exception as e:
        logger.exception(f"Failed to generate presentation: {e}")
        return SlideGenResult(success=False, error=str(e), message="幻灯片生成失败")


@router.post("/generate-async", response_model=dict[str, str])
async def generate_slides_async(_task: SlideGenTask, _current_user: CurrentUser) -> Any:
    """异步生成幻灯片（返回任务ID）"""
    # TODO: 这里可以集成Celery来实现异步任务处理
    # 现在先返回一个简单的响应
    return {"task_id": str(uuid.uuid4()), "status": "pending", "message": "任务已提交，请稍后查询结果"}


@router.get("/templates", response_model=list[dict[str, Any]])
async def get_available_templates() -> Any:
    """获取可用的PPT模板列表"""
    try:
        templates_dir = PROJECT_ROOT / "test" / "data"
        if not templates_dir.exists():
            logger.warning(f"Templates directory not found: {templates_dir}")
            return []

        templates = []
        for pptx_file in templates_dir.glob("*.pptx"):
            # 跳过临时文件和隐藏文件
            if pptx_file.name.startswith("~") or pptx_file.name.startswith("."):
                continue

            templates.append(
                {
                    "id": pptx_file.stem,  # 文件名（不含扩展名）
                    "name": pptx_file.stem,  # 使用文件名作为显示名称
                    "path": str(pptx_file),
                    "filename": pptx_file.name,
                    "size_bytes": pptx_file.stat().st_size,
                    "description": f"模板文件: {pptx_file.name}",
                }
            )

        logger.info(f"Found {len(templates)} templates in {templates_dir}")
        return templates

    except Exception as e:
        logger.exception(f"Failed to scan templates: {e}")
        raise HTTPException(status_code=500, detail=f"获取模板列表失败: {str(e)}")


@router.get("/download/{filename}")
async def download_presentation(filename: str) -> FileResponse:
    """下载生成的演示文稿"""
    try:
        file_path = OUTPUT_DIR / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件未找到")

        # 确保文件在允许的输出目录中，防止路径遍历攻击
        if not str(file_path.resolve()).startswith(str(OUTPUT_DIR.resolve())):
            raise HTTPException(status_code=403, detail="拒绝访问")

        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to download file {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"下载文件失败: {str(e)}")
