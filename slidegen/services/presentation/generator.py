from collections.abc import AsyncGenerator
from pathlib import Path

from loguru import logger
from pptx import Presentation

from slidegen.schemas.gen_request import GeneratePresentationRequest
from slidegen.schemas.stream_event import (
    ContentGeneratedEvent,
    LoopProgressEvent,
    ProgressEvent,
    StepCompletedEvent,
    StepErrorEvent,
    StepStartedEvent,
    WorkflowCompletedEvent,
    WorkflowErrorEvent,
    WorkflowStartedEvent,
)
from slidegen.services.document.markdown import MarkdownDocument
from slidegen.services.presentation.converter import MarkdownToPresentation
from slidegen.services.slidegen.workflow import run_slidegen_workflow, run_slidegen_workflow_stream

# Type alias for all possible stream events
StreamEvent = (
    ProgressEvent
    | StepStartedEvent
    | StepCompletedEvent
    | StepErrorEvent
    | WorkflowStartedEvent
    | WorkflowCompletedEvent
    | WorkflowErrorEvent
    | ContentGeneratedEvent
    | LoopProgressEvent
)


class PresentationGenerator:
    """Generator for creating PowerPoint presentations from user requests"""

    def __init__(self, templates_dir: str | None = None):
        """
        Initialize the presentation generator

        Args:
            templates_dir: Directory containing template files. If not provided, uses default location.
        """
        if templates_dir is None:
            # Use project root to locate templates directory
            project_root = Path(__file__).parent.parent.parent.parent
            templates_dir = str(project_root / "components" / "templates")

        self.templates_dir = Path(templates_dir)
        self.converter = MarkdownToPresentation()

    def get_template_path(self, template_name: str) -> str:
        """
        Get the full path for a template by name.

        Args:
            template_name: Template name (e.g., "general", "purple")

        Returns:
            Full path to the template file

        Raises:
            FileNotFoundError: If template file does not exist
        """
        template_file = self.templates_dir / f"template_{template_name}.pptx"
        if not template_file.exists():
            raise FileNotFoundError(f"Template '{template_name}' not found at: {template_file}")
        return str(template_file)

    def list_templates(self) -> list[str]:
        """
        List all available template names.

        Returns:
            List of template names (without 'template_' prefix and '.pptx' suffix)
        """
        templates = []
        for file in self.templates_dir.glob("template_*.pptx"):
            # Extract template name from filename (e.g., "template_general.pptx" -> "general")
            name = file.stem.replace("template_", "")
            templates.append(name)
        return sorted(templates)

    async def generate_presentation(
        self,
        request: GeneratePresentationRequest,
        output_path: str,
    ) -> str:
        """
        Generate a PowerPoint presentation from a request

        Args:
            request: The presentation generation request (uses request.template for template selection)
            output_path: Path where the generated PPTX will be saved

        Returns:
            Path to the generated PPTX file

        Raises:
            FileNotFoundError: If template file does not exist
            Exception: If workflow execution or presentation generation fails
        """
        try:
            # Get template path from request.template field
            template = self.get_template_path(request.template)

            logger.info(f"Starting presentation generation with template: {template}")

            # Step 1: Run the slide generation workflow to get MarkdownDocument
            logger.info("Running slide generation workflow...")
            markdown_doc: MarkdownDocument = await run_slidegen_workflow(request)

            # Step 2: Load the template PPTX
            logger.info("Loading template presentation...")
            template_prs = Presentation(template)

            # Step 3: Convert Markdown to PPTX using the template
            logger.info("Converting Markdown to PowerPoint...")
            presentation = await self.converter.generate(template_prs, markdown_doc)

            # Step 4: Save the result
            logger.info(f"Saving presentation to: {output_path}")
            presentation.save(output_path)

            logger.info(f"Successfully generated presentation: {output_path}")
            return output_path

        except Exception as e:
            logger.exception(f"Failed to generate presentation: {e}")
            raise

    async def generate_presentation_stream(
        self,
        request: GeneratePresentationRequest,
        output_path: str,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Generate a PowerPoint presentation with streaming progress events

        Args:
            request: The presentation generation request
            output_path: Path where the generated PPTX will be saved

        Yields:
            Stream events for content generation and PPTX conversion progress
        """
        try:
            # Get template path
            template = self.get_template_path(request.template)
            logger.info(f"Starting streaming presentation generation with template: {template}")

            # Track the final content for PPTX generation
            final_content: str | None = None
            markdown_doc: MarkdownDocument | None = None

            # Stream content generation events
            async for event in run_slidegen_workflow_stream(request):
                # Pass through all workflow events
                yield event

                # Capture final content from WorkflowCompletedEvent
                if isinstance(event, WorkflowCompletedEvent) and event.content:
                    final_content = event.content

            # If we got content, proceed with PPTX generation
            if final_content:
                # Parse the markdown content
                markdown_doc = MarkdownDocument(final_content)

                # Emit PPTX conversion start event
                yield StepStartedEvent(
                    step_name="PPTX Conversion",
                    message="Converting content to PowerPoint format...",
                )

                yield ProgressEvent(
                    stage="pptx_conversion",
                    progress=0.0,
                    message="Loading template...",
                )

                # Load template
                template_prs = Presentation(template)

                yield ProgressEvent(
                    stage="pptx_conversion",
                    progress=30.0,
                    message="Converting markdown to slides...",
                )

                # Convert to PPTX
                presentation = await self.converter.generate(template_prs, markdown_doc)

                yield ProgressEvent(
                    stage="pptx_conversion",
                    progress=80.0,
                    message="Saving presentation file...",
                )

                # Save the presentation
                presentation.save(output_path)

                yield ProgressEvent(
                    stage="pptx_conversion",
                    progress=100.0,
                    message="Presentation saved successfully",
                )

                # Emit completion event with file info
                yield StepCompletedEvent(
                    step_name="PPTX Conversion",
                    content=output_path,
                    message="PowerPoint file generated successfully",
                )

                logger.info(f"Successfully generated presentation: {output_path}")

            else:
                yield WorkflowErrorEvent(
                    error="No content generated from workflow",
                    message="Content generation failed",
                )

        except Exception as e:
            logger.exception(f"Failed to generate presentation: {e}")
            yield WorkflowErrorEvent(
                error=str(e),
                message="Presentation generation failed",
            )


presentation_generator = PresentationGenerator()
