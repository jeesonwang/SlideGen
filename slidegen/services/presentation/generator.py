import os
from pathlib import Path

from loguru import logger
from pptx import Presentation

from slidegen.schemas.gen_request import GeneratePresentationRequest
from slidegen.services.document.markdown import MarkdownDocument
from slidegen.services.presentation.converter import MarkdownToPresentation
from slidegen.services.slidegen.workflow import run_slidegen_workflow


class PresentationGenerator:
    """Generator for creating PowerPoint presentations from user requests"""

    def __init__(self, default_template_path: str | None = None):
        """
        Initialize the presentation generator

        Args:
            default_template_path: Default template path to use if not specified in request
        """
        if default_template_path is None:
            # Use project root to locate default template
            project_root = Path(__file__).parent.parent.parent.parent
            default_template_path = str(project_root / "test" / "data" / "template_0.pptx")

        self.default_template_path = default_template_path
        self.converter = MarkdownToPresentation()

    async def generate_presentation(
        self,
        request: GeneratePresentationRequest,
        output_path: str,
        template_path: str | None = None,
    ) -> str:
        """
        Generate a PowerPoint presentation from a request

        Args:
            request: The presentation generation request
            output_path: Path where the generated PPTX will be saved
            template_path: Optional custom template path. If not provided, uses default template

        Returns:
            Path to the generated PPTX file

        Raises:
            FileNotFoundError: If template file does not exist
            Exception: If workflow execution or presentation generation fails
        """
        try:
            # Use provided template or fall back to default
            template = template_path or self.default_template_path

            if not os.path.exists(template):
                raise FileNotFoundError(f"Template file not found: {template}")

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
