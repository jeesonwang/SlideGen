# SlideGen background tasks
import asyncio
import uuid
from datetime import datetime
from typing import Any, Literal

from celery import shared_task
from loguru import logger

from slidegen.core.celery_config import generate_presentation as task_name
from slidegen.core.config import settings
from slidegen.schemas.gen_request import GeneratePresentationRequest, Tone, Verbosity
from slidegen.services import presentation_generator

OUTPUT_DIR = settings.OUTPUT_DIR

# Shared event loop for Celery tasks to avoid creating/destroying loops repeatedly
_event_loop: asyncio.AbstractEventLoop | None = None


def get_event_loop() -> asyncio.AbstractEventLoop:
    """Get or create a shared event loop for Celery tasks"""
    global _event_loop
    if _event_loop is None or _event_loop.is_closed():
        _event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_event_loop)
    return _event_loop


@shared_task(name=task_name, bind=True)  # type: ignore
def generate_presentation_task(self: Any, task_data: dict[str, Any]) -> dict[str, Any]:
    """
    Celery task for generating presentations asynchronously.

    Args:
        task_data: Dictionary containing:
            - topic: Slide topic
            - user_id: User ID
            - llm_config_id: LLM config ID (optional)
            - instructions: Instructions (optional)
            - tone: Tone
            - verbosity: Verbosity
            - web_search: Whether to use web search
            - n_slides: Number of slides
            - language: Language
            - template: Template name
            - include_table_of_contents: Whether to include TOC
            - include_title_slide: Whether to include title slide
            - file_ids: File IDs (optional)
            - export_as: Export format

    Returns:
        Dictionary containing:
            - success: Whether the task succeeded
            - output_path: Path to generated file (if successful)
            - filename: Generated filename (if successful)
            - download_url: Download URL (if successful)
            - error: Error message (if failed)
    """
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Generate unique output file name
        topic = task_data.get("topic", "presentation")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_as = task_data.get("export_as", "pptx")
        ext = export_as if export_as in ("pptx", "pdf") else "pptx"
        filename = f"{topic[:30]}_{timestamp}_{uuid.uuid4().hex[:8]}.{ext}"
        output_path = str(OUTPUT_DIR / filename)

        # Convert enum types
        tone_str = task_data.get("tone", "default")
        verbosity_str = task_data.get("verbosity", "standard")
        tone = Tone(tone_str) if tone_str in [t.value for t in Tone] else Tone.DEFAULT
        verbosity = Verbosity(verbosity_str) if verbosity_str in [v.value for v in Verbosity] else Verbosity.STANDARD
        export_format: Literal["pptx", "pdf"] = "pptx" if task_data.get("export_as") == "pptx" else "pdf"

        # Convert llm_config_id string back to UUID if present
        llm_config_id = None
        if task_data.get("llm_config_id"):
            llm_config_id = uuid.UUID(task_data["llm_config_id"])

        request = GeneratePresentationRequest(
            content=task_data["topic"],
            instructions=task_data.get("instructions"),
            tone=tone,
            verbosity=verbosity,
            web_search=task_data.get("web_search", False),
            n_slides=task_data.get("n_slides", 8),
            language=task_data.get("language", "English"),
            template=task_data.get("template", "general"),
            include_table_of_contents=task_data.get("include_table_of_contents", False),
            include_title_slide=task_data.get("include_title_slide", True),
            files=task_data.get("file_ids"),
            export_as=export_format,
            user_id=task_data["user_id"],
            llm_config_id=llm_config_id,
        )

        logger.info(f"[Celery Task {self.request.id}] Generating presentation: {topic}")

        # Run async function using shared event loop to avoid resource leaks
        loop = get_event_loop()
        result_path = loop.run_until_complete(
            presentation_generator.generate_presentation(
                request=request,
                output_path=output_path,
            )
        )

        logger.info(f"[Celery Task {self.request.id}] Presentation generated successfully: {result_path}")

        return {
            "success": True,
            "output_path": result_path,
            "filename": filename,
            "download_url": f"/api/v1/slidegen/download/{filename}",
        }

    except Exception as e:
        logger.exception(f"[Celery Task {self.request.id}] Failed to generate presentation: {e}")
        return {
            "success": False,
            "error": str(e),
        }
