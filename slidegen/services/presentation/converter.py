from time import perf_counter

from loguru import logger
from pptx.presentation import Presentation

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
from slidegen.services.presentation.template_profile import TemplateRole, profile_presentation_template
from slidegen.services.slidegen.outline_structure import iter_chapter_slide_groups


class MarkdownToPresentation:
    """Generate a PPT presentation from a markdown document."""

    async def generate(
        self,
        template_prs: Presentation,
        markdown_document: MarkdownDocument,
    ) -> Presentation:
        """generate the complete PPT presentation"""
        started_at = perf_counter()
        profile = profile_presentation_template(template_prs)
        for warning in profile.warnings:
            logger.warning("PPT template profile: {}", warning)

        headings = [h for h in markdown_document.descendants if hasattr(h, "level") and h.level == 1]
        if not headings:
            raise MarkdownDocumentError("Markdown document must have at least one level 1 heading")

        main_heading = markdown_document.main
        if main_heading is None:
            raise MarkdownDocumentError("Markdown document must have a main heading")

        cover_index = profile.role_index(TemplateRole.COVER)
        if cover_index is None:
            logger.info("PPT conversion: generating native cover slide for '{}'", main_heading.element_text)
            await NativeCoverPage.generate_slide(template_prs, main_heading, slide_index=0)
        else:
            logger.info("PPT conversion: generating cover slide for '{}'", main_heading.element_text)
            await CoverPage.generate_slide(template_prs, main_heading, cover_page_index=cover_index)

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

        catalog_index = profile.role_index(TemplateRole.CATALOG)
        if catalog_index is None:
            logger.info("PPT conversion: generating native catalog slide")
            catalog_last_index = await NativeCatalogPage.generate_slide(template_prs, chapters, slide_index=1)
        else:
            logger.info("PPT conversion: generating catalog slides")
            catalog_last_index = await CatalogPage.generate_slide(
                template_prs, chapters, catalog_page_index=catalog_index
            )

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
                assert render_plan.chapter_home_template_index is not None
                await ChapterHomePage.generate_slide(
                    template_prs,
                    planned_chapter.heading,
                    chapter_home_page_index=render_plan.chapter_home_template_index,
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
                    assert render_plan.chapter_content_template_index is not None
                    await ChapterContentPage.generate_slide(
                        template_prs,
                        planned_slide.heading,
                        chapter_page_index=render_plan.chapter_content_template_index,
                        slide_index=planned_slide.slide_index,
                    )

        logger.info("PPT conversion: generating ending slide")
        if render_plan.use_native_end:
            await NativeEndPage.generate_slide(template_prs, slide_index=render_plan.end_slide_index)
        else:
            assert render_plan.end_template_index is not None
            await EndPage.generate_slide(
                template_prs,
                end_page_index=render_plan.end_template_index,
                slide_index=render_plan.end_slide_index,
            )

        self._cleanup_template_slides(template_prs, render_plan.cleanup_template_indexes)
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
            catalog_slide_count=catalog_last_index - (catalog_index or 1) + 1,
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

    def _cleanup_template_slides(self, template_prs: Presentation, template_slide_indexes: list[int]) -> None:
        # Delete slides from back to front so earlier indexes remain stable.
        for index in sorted(template_slide_indexes, reverse=True):
            CoverPage.remove_slide(template_prs, index)
