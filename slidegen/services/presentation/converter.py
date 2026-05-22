from time import perf_counter

from loguru import logger
from pptx.presentation import Presentation

import pptx

from slidegen.exceptions import MarkdownDocumentError
from slidegen.services.document.markdown import Heading, MarkdownDocument
from slidegen.services.presentation.native_pages import (
    NativeCatalogPage,
    NativeChapterContentPage,
    NativeChapterHomePage,
    NativeCoverPage,
    NativeEndPage,
)
from slidegen.services.presentation.pages import (
    CatalogPage,
    ChapterContentPage,
    ChapterHomePage,
    CoverPage,
    EndPage,
)
from slidegen.services.presentation.render_plan import (
    ConversionSummary,
    build_presentation_render_plan,
)
from slidegen.services.presentation.template_profile import READY_THRESHOLD, TemplateRole, profile_presentation_template
from slidegen.services.slidegen.outline_structure import iter_chapter_slide_groups

from slidegen.core.config import settings
from slidegen.services.presentation.design_tokens import extract_design_tokens_from_presentation
from slidegen.services.presentation.post_render_validator import PostRenderValidator
from slidegen.services.presentation.recipe_agent import RecipeAgent, resolve_recipe
from slidegen.services.presentation.semantic import BlockKind, BlockSpec, SlideKind, SlideSpec, build_content_slide_spec
from slidegen.services.presentation.slide_renderer import AssetProvider, SlideRenderer


class MarkdownToPresentation:
    """Generate a PPT presentation from a markdown document."""

    def __init__(self, *, recipe_model: object | None = None, asset_provider: AssetProvider | None = None) -> None:
        self.recipe_model = recipe_model
        self.asset_provider = asset_provider

    async def generate(
        self,
        template_prs: Presentation,
        markdown_document: MarkdownDocument,
    ) -> Presentation:
        """generate the complete PPT presentation"""
        if settings.ENABLE_RECIPE_RENDERER:
            return await self._generate_with_recipe_renderer(template_prs, markdown_document)

        started_at = perf_counter()
        profile = profile_presentation_template(template_prs)
        for warning in profile.warnings:
            logger.warning("PPT template profile: {}", warning)
        original_template_slide_ids = [slide.slide_id for slide in template_prs.slides]
        template_slide_id_by_role = {
            role: template_prs.slides[index].slide_id
            for role in TemplateRole
            if (index := profile.role_index(role, min_confidence=READY_THRESHOLD)) is not None
        }
        reused_template_slide_ids: set[int] = set()

        def current_template_index(role: TemplateRole) -> int | None:
            slide_id = template_slide_id_by_role.get(role)
            if slide_id is None:
                return None
            return self._slide_index_by_id(template_prs, slide_id)

        headings = [h for h in markdown_document.descendants if hasattr(h, "level") and h.level == 1]
        if not headings:
            raise MarkdownDocumentError("Markdown document must have at least one level 1 heading")

        main_heading = markdown_document.main
        if main_heading is None:
            raise MarkdownDocumentError("Markdown document must have a main heading")

        cover_index = current_template_index(TemplateRole.COVER)
        if cover_index is None:
            logger.info("PPT conversion: generating native cover slide for '{}'", main_heading.element_text)
            await NativeCoverPage.generate_slide(template_prs, main_heading, slide_index=0)
        else:
            logger.info("PPT conversion: generating cover slide for '{}'", main_heading.element_text)
            await CoverPage.generate_slide(template_prs, main_heading, cover_page_index=cover_index)
            reused_template_slide_ids.add(template_slide_id_by_role[TemplateRole.COVER])

        chapter_slide_groups = list(iter_chapter_slide_groups(main_heading))
        chapters: list[Heading] = [group.chapter for group in chapter_slide_groups]
        total_content_slides = sum(len(group.slides) for group in chapter_slide_groups)

        if not chapters:
            raise MarkdownDocumentError("Markdown document must have at least one level 2 heading")
        logger.info(
            "PPT conversion: markdown parsed into {} chapters and {} content slides",
            len(chapters),
            total_content_slides,
        )

        catalog_index = current_template_index(TemplateRole.CATALOG)
        if catalog_index is None:
            logger.info("PPT conversion: generating native catalog slide")
            catalog_first_index = 1
            catalog_last_index = await NativeCatalogPage.generate_slide(template_prs, chapters, slide_index=1)
        else:
            logger.info("PPT conversion: generating catalog slides")
            catalog_first_index = catalog_index
            catalog_last_index = await CatalogPage.generate_slide(
                template_prs, chapters, catalog_page_index=catalog_index
            )
            reused_template_slide_ids.add(template_slide_id_by_role[TemplateRole.CATALOG])

        render_plan = build_presentation_render_plan(
            chapter_slide_groups,
            profile=profile,
            catalog_last_index=catalog_last_index,
        )

        for planned_chapter in render_plan.chapters:
            logger.info(
                "PPT conversion: generating chapter {}/{} home slide: {}",
                planned_chapter.chapter_number,
                render_plan.total_chapters,
                planned_chapter.heading.element_text,
            )
            if render_plan.use_native_chapter:
                await NativeChapterHomePage.generate_slide(
                    template_prs,
                    planned_chapter.heading,
                    chapter_number=planned_chapter.chapter_number,
                    slide_index=planned_chapter.home_slide_index,
                )
            else:
                chapter_home_template_index = current_template_index(TemplateRole.CHAPTER)
                assert chapter_home_template_index is not None
                await ChapterHomePage.generate_slide(
                    template_prs,
                    planned_chapter.heading,
                    chapter_home_page_index=chapter_home_template_index,
                    chapter_number=planned_chapter.chapter_number,
                    slide_index=planned_chapter.home_slide_index,
                )

            for planned_slide in planned_chapter.content_slides:
                logger.info(
                    "PPT conversion: generating content slide {}/{}: {}",
                    planned_slide.sequence_number,
                    planned_slide.total_content_slides,
                    planned_slide.heading.element_text,
                )
                if render_plan.use_native_content:
                    await NativeChapterContentPage.generate_slide(
                        template_prs,
                        planned_slide.heading,
                        slide_index=planned_slide.slide_index,
                    )
                else:
                    chapter_content_template_index = current_template_index(TemplateRole.CONTENT)
                    assert chapter_content_template_index is not None
                    await ChapterContentPage.generate_slide(
                        template_prs,
                        planned_slide.heading,
                        chapter_page_index=chapter_content_template_index,
                        slide_index=planned_slide.slide_index,
                    )

        logger.info("PPT conversion: generating ending slide")
        if render_plan.use_native_end:
            await NativeEndPage.generate_slide(template_prs, slide_index=render_plan.end_slide_index)
        else:
            end_template_index = current_template_index(TemplateRole.END)
            assert end_template_index is not None
            await EndPage.generate_slide(
                template_prs,
                end_page_index=end_template_index,
                slide_index=render_plan.end_slide_index,
            )

        cleanup_template_slide_ids = [
            slide_id for slide_id in original_template_slide_ids if slide_id not in reused_template_slide_ids
        ]
        self._cleanup_template_slides(template_prs, cleanup_template_slide_ids)
        native_fallback_roles = tuple(
            role
            for role, used in {
                "catalog": render_plan.use_native_catalog,
                "chapter": render_plan.use_native_chapter,
                "content": render_plan.use_native_content,
                "end": render_plan.use_native_end,
            }.items()
            if used
        )
        elapsed_seconds = perf_counter() - started_at
        summary = ConversionSummary(
            title=main_heading.element_text,
            total_slides=len(template_prs.slides),
            total_chapters=render_plan.total_chapters,
            total_content_slides=render_plan.total_content_slides,
            catalog_slide_count=catalog_last_index - catalog_first_index + 1,
            native_fallback_roles=native_fallback_roles,
            elapsed_seconds=elapsed_seconds,
        )
        logger.info(
            "PPT conversion summary: title='{}', slides={}, chapters={}, content_slides={}, native_fallbacks={}, elapsed={:.2f}s",
            summary.title,
            summary.total_slides,
            summary.total_chapters,
            summary.total_content_slides,
            ",".join(summary.native_fallback_roles) or "none",
            summary.elapsed_seconds,
        )

        return template_prs

    def _slide_index_by_id(self, template_prs: Presentation, slide_id: int) -> int:
        for index, slide in enumerate(template_prs.slides):
            if slide.slide_id == slide_id:
                return index
        raise ValueError(f"Slide id {slide_id} no longer exists in presentation")

    def _cleanup_template_slides(self, template_prs: Presentation, template_slide_ids: list[int]) -> None:
        template_slide_indexes = []
        for slide_id in template_slide_ids:
            try:
                template_slide_indexes.append(self._slide_index_by_id(template_prs, slide_id))
            except ValueError:
                continue
        # Delete slides from back to front so earlier indexes remain stable.
        for index in sorted(template_slide_indexes, reverse=True):
            CoverPage.remove_slide(template_prs, index)

    async def _generate_with_recipe_renderer(
        self,
        template_prs: Presentation,
        markdown_document: MarkdownDocument,
    ) -> Presentation:
        main_heading = markdown_document.main
        if main_heading is None:
            raise MarkdownDocumentError("Markdown document must have a main heading")

        chapter_slide_groups = list(iter_chapter_slide_groups(main_heading))
        chapters: list[Heading] = [group.chapter for group in chapter_slide_groups]
        if not chapters:
            raise MarkdownDocumentError("Markdown document must have at least one level 2 heading")

        output_prs = pptx.Presentation()
        output_prs.slide_width = template_prs.slide_width
        output_prs.slide_height = template_prs.slide_height
        tokens = extract_design_tokens_from_presentation(template_prs, "general")
        renderer = SlideRenderer(tokens, asset_provider=self.asset_provider)
        agent = RecipeAgent(model=self.recipe_model) if settings.ENABLE_RECIPE_AGENT and self.recipe_model is not None else None

        async def render_spec(spec: SlideSpec) -> None:
            recipe = await resolve_recipe(spec, tokens, agent=agent, enable_agent=agent is not None)
            slide = output_prs.slides.add_slide(output_prs.slide_layouts[6])
            await renderer.render(slide, recipe, spec)

        await render_spec(self._cover_spec(main_heading))
        await render_spec(self._agenda_spec(chapters))
        for group in chapter_slide_groups:
            await render_spec(self._chapter_home_spec(group.chapter))
            for content_heading in group.slides:
                await render_spec(build_content_slide_spec(content_heading))
        await render_spec(self._closing_spec())

        issues = PostRenderValidator(mode="fail").validate(output_prs)
        if issues:
            messages = "; ".join(issue.message for issue in issues if issue.level == "error")
            if messages:
                raise MarkdownDocumentError(f"Recipe-rendered presentation failed geometry validation: {messages}")
        return output_prs

    def _cover_spec(self, main_heading: Heading) -> SlideSpec:
        return SlideSpec(
            kind=SlideKind.COVER,
            title=main_heading.element_text,
            source_level=1,
            blocks=(BlockSpec(kind=BlockKind.SUBTITLE, title="", text=""),),
        )

    def _agenda_spec(self, chapters: list[Heading]) -> SlideSpec:
        return SlideSpec(
            kind=SlideKind.AGENDA,
            title="目录",
            source_level=1,
            blocks=tuple(BlockSpec(kind=BlockKind.POINT, title=chapter.element_text, text="") for chapter in chapters),
        )

    def _chapter_home_spec(self, chapter: Heading) -> SlideSpec:
        return SlideSpec(
            kind=SlideKind.SECTION_COVER,
            title=chapter.element_text,
            source_level=2,
            blocks=(BlockSpec(kind=BlockKind.TITLE, title=chapter.element_text, text=""),),
        )

    def _closing_spec(self) -> SlideSpec:
        return SlideSpec(
            kind=SlideKind.CLOSING,
            title="谢谢",
            source_level=1,
            blocks=(BlockSpec(kind=BlockKind.TITLE, title="谢谢", text=""),),
        )
