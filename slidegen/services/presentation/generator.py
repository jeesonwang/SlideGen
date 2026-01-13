import asyncio
from collections.abc import AsyncGenerator
from functools import partial
from pathlib import Path

from loguru import logger
from pptx import Presentation

from slidegen.schemas.gen_request import GeneratePresentationRequest
from slidegen.schemas.stream_event import (
    ProgressEvent,
    StepCompletedEvent,
    StepStartedEvent,
    StreamEventT,
    WorkflowCompletedEvent,
    WorkflowErrorEvent,
)
from slidegen.services.document.markdown import MarkdownDocument
from slidegen.services.presentation.converter import MarkdownToPresentation
from slidegen.services.slidegen.workflow import run_slidegen_workflow, run_slidegen_workflow_stream


class PresentationGenerator:
    """Generator for creating PowerPoint presentations from user requests"""

    def __init__(self, templates_dir: str | None = None) -> None:
        """Initialize the presentation generator."""
        if templates_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            templates_dir = str(project_root / "components" / "templates")

        self.templates_dir = Path(templates_dir)
        self.converter = MarkdownToPresentation()

    def get_template_path(self, template_name: str) -> str:
        """Get the full path for a template by name."""
        template_file = self.templates_dir / f"template_{template_name}.pptx"
        if not template_file.exists():
            raise FileNotFoundError(f"Template '{template_name}' not found at: {template_file}")
        return str(template_file)

    def list_templates(self) -> list[str]:
        """List all available template names."""
        return sorted(
            file.stem.replace("template_", "")
            for file in self.templates_dir.glob("template_*.pptx")
        )

    async def generate_presentation(
        self,
        request: GeneratePresentationRequest,
        output_path: str,
    ) -> str:
        """Generate a PowerPoint presentation from a request."""
        template = self.get_template_path(request.template)
        logger.info(f"Starting presentation generation with template: {template}")

        logger.info("Running slide generation workflow...")
        markdown_doc: MarkdownDocument = await run_slidegen_workflow(request)

        logger.info("Loading template presentation...")
        loop = asyncio.get_event_loop()
        template_prs = await loop.run_in_executor(None, Presentation, template)

        logger.info("Converting Markdown to PowerPoint...")
        presentation = await self.converter.generate(template_prs, markdown_doc)

        logger.info(f"Saving presentation to: {output_path}")
        await loop.run_in_executor(None, partial(presentation.save, output_path))

        logger.info(f"Successfully generated presentation: {output_path}")
        return output_path

    async def generate_presentation_stream(
        self,
        request: GeneratePresentationRequest,
        output_path: str,
    ) -> AsyncGenerator[StreamEventT, None]:
        """Generate a PowerPoint presentation with streaming progress events."""
        try:
            template = self.get_template_path(request.template)
            logger.info(f"Starting streaming presentation generation with template: {template}")

            final_content: str | None = None

            async for event in run_slidegen_workflow_stream(request):
                yield event
                if isinstance(event, WorkflowCompletedEvent) and event.content:
                    final_content = event.content

            if not final_content:
                yield WorkflowErrorEvent(
                    error="No content generated from workflow",
                    message="Content generation failed",
                )
                return

            markdown_doc = MarkdownDocument(final_content)

            yield StepStartedEvent(
                step_name="PPTX Conversion",
                message="Converting content to PowerPoint format...",
            )

            yield ProgressEvent(
                stage="pptx_conversion",
                progress=0.0,
                message="Loading template...",
            )

            loop = asyncio.get_event_loop()
            template_prs = await loop.run_in_executor(None, Presentation, template)

            yield ProgressEvent(
                stage="pptx_conversion",
                progress=30.0,
                message="Converting markdown to slides...",
            )

            presentation = await self.converter.generate(template_prs, markdown_doc)

            yield ProgressEvent(
                stage="pptx_conversion",
                progress=80.0,
                message="Saving presentation file...",
            )

            await loop.run_in_executor(None, partial(presentation.save, output_path))

            yield ProgressEvent(
                stage="pptx_conversion",
                progress=100.0,
                message="Presentation saved successfully",
            )

            yield StepCompletedEvent(
                step_name="PPTX Conversion",
                content=output_path,
                message="PowerPoint file generated successfully",
            )

            logger.info(f"Successfully generated presentation: {output_path}")

        except Exception as e:
            logger.exception(f"Failed to generate presentation: {e}")
            yield WorkflowErrorEvent(
                error=str(e),
                message="Presentation generation failed",
            )


presentation_generator = PresentationGenerator()
