from pathlib import Path

from loguru import logger
from pptx import Presentation

from slidegen.schemas.gen_request import GeneratePresentationRequest
from slidegen.services.document.markdown import MarkdownDocument
from slidegen.services.presentation.converter import MarkdownToPresentation
from slidegen.services.slidegen.workflow import run_slidegen_workflow


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


presentation_generator = PresentationGenerator()
