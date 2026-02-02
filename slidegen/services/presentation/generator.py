import asyncio
from collections.abc import AsyncGenerator
from functools import partial
from pathlib import Path
from typing import Literal

from loguru import logger
from lxml.etree import Element, fromstring, tostring
from pptx import Presentation
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.presentation import Presentation as PresentationType

from slidegen.schemas.gen_request import GeneratePresentationRequest
from slidegen.schemas.stream_event import (
    ProgressEvent,
    StepCompletedEvent,
    StepStartedEvent,
    StreamEventT,
    WorkflowCompletedEvent,
    WorkflowErrorEvent,
)
from slidegen.schemas.theme import PresentationTheme, ThemePresets
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
        return sorted(file.stem.replace("template_", "") for file in self.templates_dir.glob("template_*.pptx"))

    def _resolve_theme(
        self, theme: PresentationTheme | None = None, theme_preset: str | None = None
    ) -> PresentationTheme | None:
        """
        Resolve theme from either direct theme object or preset name.

        Args:
            theme: Direct theme object (takes priority)
            theme_preset: Theme preset name

        Returns:
            Resolved theme or None if neither is provided
        """
        if theme:
            return theme
        if theme_preset:
            preset_theme = ThemePresets.get_preset(theme_preset)
            if preset_theme:
                logger.info(f"Using theme preset: {theme_preset}")
                return preset_theme
            else:
                logger.warning(f"Theme preset '{theme_preset}' not found, available: {ThemePresets.list_presets()}")
        return None

    def apply_theme_colors(self, presentation: PresentationType, theme: PresentationTheme) -> None:
        """
        Apply theme colors to a PowerPoint presentation.

        This method modifies the presentation's theme XML directly, ensuring that
        all elements using theme colors are automatically updated.

        Args:
            presentation: The PowerPoint presentation object
            theme: The theme configuration with color mappings

        Example:
            >>> from slidegen.schemas.theme import ThemePresets
            >>> generator = PresentationGenerator()
            >>> prs = Presentation("template.pptx")
            >>> generator.apply_theme_colors(prs, ThemePresets.SUNSET_BOULEVARD)
            >>> prs.save("themed.pptx")
        """
        try:
            # Get the slide master and theme part
            slide_master = presentation.slide_master
            slide_master_part = slide_master.part
            theme_part = slide_master_part.part_related_by(RT.THEME)

            # Parse the theme XML
            theme_xml = fromstring(theme_part.blob)

            # Get the color mappings (only non-None values)
            theme_colors = theme.colors.model_dump_colors()

            # Define the XML namespace
            nsmap = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}

            # Update each color in the theme
            for color_name, hex_value in theme_colors.items():
                if color_name:
                    try:
                        # Clean hex value first
                        hex_value_clean = hex_value.replace("0x", "").replace("#", "").upper()

                        # Find the color container element (e.g., <a:dk1>, <a:accent1>)
                        color_container = theme_xml.xpath(
                            f"a:themeElements/a:clrScheme/a:{color_name}",
                            namespaces=nsmap,
                        )

                        if not color_container:
                            logger.warning(f"Color container not found for {color_name}")
                            continue

                        color_container = color_container[0]

                        # Try to find srgbClr element first (RGB colors)
                        srgb_elements = color_container.xpath("a:srgbClr", namespaces=nsmap)

                        if srgb_elements:
                            # Update existing srgbClr element
                            srgb_elements[0].set("val", hex_value_clean)
                            logger.debug(f"Updated srgbClr for {color_name} to {hex_value_clean}")
                        else:
                            # Check if it's a sysClr element (system colors like dk1, lt1)
                            sys_elements = color_container.xpath("a:sysClr", namespaces=nsmap)

                            if sys_elements:
                                # Remove the sysClr element
                                color_container.remove(sys_elements[0])
                                logger.debug(f"Removed sysClr for {color_name}")

                            # Create new srgbClr element
                            srgb_element = Element(
                                f"{{{nsmap['a']}}}srgbClr",
                                val=hex_value_clean,
                            )
                            color_container.append(srgb_element)
                            logger.debug(f"Created srgbClr for {color_name} with value {hex_value_clean}")

                    except IndexError:
                        logger.warning(f"Could not find color element for {color_name}")
                    except Exception as e:
                        logger.error(f"Error updating color {color_name}: {e}")

            # Save the modified theme XML back to the theme part
            theme_part._blob = tostring(theme_xml)
            logger.info(f"Successfully applied theme '{theme.name}' with {len(theme_colors)} colors")

        except Exception as e:
            logger.error(f"Failed to apply theme colors: {e}")
            raise

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

        # Apply theme if provided
        theme = self._resolve_theme(request.theme, request.theme_preset)
        if theme:
            logger.info(f"Applying theme: {theme.name}")
            self.apply_theme_colors(template_prs, theme)

        logger.info("Converting Markdown to PowerPoint...")
        presentation = await self.converter.generate(template_prs, markdown_doc)

        logger.info(f"Saving presentation to: {output_path}")
        await loop.run_in_executor(None, partial(presentation.save, output_path))

        logger.info(f"Successfully generated presentation: {output_path}")
        return output_path

    async def generate_from_markdown(
        self,
        markdown_content: str,
        template_name: str,
        output_path: str,
        export_as: Literal["pptx", "pdf"] = "pptx",
        theme: PresentationTheme | None = None,
    ) -> str:
        """Generate a PowerPoint presentation directly from markdown content.

        Args:
            markdown_content: The markdown content to convert to PPT
            template_name: Name of the template to use
            output_path: Path to save the generated PPT
            export_as: Export format ("pptx" supported, "pdf" not yet supported)
            theme: Optional theme to apply to the presentation

        Returns:
            The output path of the generated presentation
        """
        if export_as != "pptx":
            raise ValueError(f"Unsupported export_as={export_as!r}; only 'pptx' is currently supported")

        template = self.get_template_path(template_name)
        logger.info(f"Starting presentation generation from markdown with template: {template}")

        # Parse markdown content
        markdown_doc = MarkdownDocument(markdown_content)

        # Load template
        loop = asyncio.get_event_loop()
        template_prs = await loop.run_in_executor(None, Presentation, template)

        # Apply theme colors if provided
        if theme:
            logger.info(f"Applying theme: {theme.name}")
            self.apply_theme_colors(template_prs, theme)

        # Convert to PPT
        logger.info("Converting Markdown to PowerPoint...")
        presentation = await self.converter.generate(template_prs, markdown_doc)

        # Save
        logger.info(f"Saving presentation to: {output_path}")
        await loop.run_in_executor(None, partial(presentation.save, output_path))

        logger.info(f"Successfully generated presentation from markdown: {output_path}")
        return output_path

    async def generate_from_markdown_stream(
        self,
        markdown_content: str,
        template_name: str,
        output_path: str,
        export_as: Literal["pptx", "pdf"] = "pptx",
        theme: PresentationTheme | None = None,
    ) -> AsyncGenerator[StreamEventT, None]:
        """Generate a PowerPoint presentation from markdown with streaming progress events.

        Args:
            markdown_content: The markdown content to convert to PPT
            template_name: Name of the template to use
            output_path: Path to save the generated PPT
            export_as: Export format ("pptx" supported, "pdf" not yet supported)
            theme: Optional theme to apply to the presentation

        Yields:
            Stream events containing conversion progress
        """
        try:
            if export_as != "pptx":
                yield WorkflowErrorEvent(
                    error=f"Unsupported export_as={export_as!r}; only 'pptx' is currently supported",
                    message="Unsupported export format",
                )
                return

            template = self.get_template_path(template_name)
            logger.info(f"Starting streaming presentation generation from markdown with template: {template}")

            yield StepStartedEvent(
                step_name="PPTX Conversion",
                message="Converting markdown to PowerPoint format...",
            )

            yield ProgressEvent(
                stage="pptx_conversion",
                progress=0.0,
                message="Loading template...",
            )

            # Load template
            loop = asyncio.get_event_loop()
            template_prs = await loop.run_in_executor(None, Presentation, template)

            # Apply theme if provided
            if theme:
                yield ProgressEvent(
                    stage="pptx_conversion",
                    progress=10.0,
                    message=f"Applying theme: {theme.name}...",
                )
                self.apply_theme_colors(template_prs, theme)

            yield ProgressEvent(
                stage="pptx_conversion",
                progress=20.0,
                message="Parsing markdown content...",
            )

            # Parse markdown
            markdown_doc = MarkdownDocument(markdown_content)

            yield ProgressEvent(
                stage="pptx_conversion",
                progress=40.0,
                message="Converting markdown to slides...",
            )

            # Convert to PPT
            presentation = await self.converter.generate(template_prs, markdown_doc)

            yield ProgressEvent(
                stage="pptx_conversion",
                progress=80.0,
                message="Saving presentation file...",
            )

            # Save
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

            logger.info(f"Successfully generated presentation from markdown: {output_path}")

        except Exception as e:
            logger.exception(f"Failed to generate presentation from markdown: {e}")
            yield WorkflowErrorEvent(
                error=str(e),
                message="Presentation generation from markdown failed",
            )

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

            # Apply theme if provided
            theme = self._resolve_theme(request.theme, request.theme_preset)
            if theme:
                yield ProgressEvent(
                    stage="pptx_conversion",
                    progress=10.0,
                    message=f"Applying theme: {theme.name}...",
                )
                self.apply_theme_colors(template_prs, theme)

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
