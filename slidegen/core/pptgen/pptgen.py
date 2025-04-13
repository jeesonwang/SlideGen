from pptx.presentation import Presentation

from slidegen.core.docparse.markdown_parser import Heading, MarkdownDocument
from slidegen.exception import MarkdownDocumentError

from .pptpages import (
    CatalogPage,
    ChapterContentPage,
    ChapterHomePage,
    CoverPage,
    EndPage,
)


class PPTGen:
    """
    Generate a PPT presentation from a markdown document

    Template presentation object. Template presentation must have at least 5 slides
    and must be in accordance with `CoverPage`, `CatalogPage`, `ChapterHomePage`, `ChapterContentPage`, `EndPage`.
    """

    def __init__(self) -> None:
        self.slide_index = 0
        self.chapter_index = 1

    def generate(
        self,
        template_prs: Presentation,
        markdown_document: MarkdownDocument,
        cover_page_index: int = 0,
        catalog_page_index: int = 1,
    ) -> Presentation:
        """generate the complete PPT presentation"""

        headings = [h for h in markdown_document.descendants if hasattr(h, "level") and h.level == 1]

        if not headings:
            raise MarkdownDocumentError("Markdown document must have at least one level 1 heading")

        main_heading = markdown_document.main
        if main_heading is None:
            raise MarkdownDocumentError("Markdown document must have a main heading")
        CoverPage.generate_slide(template_prs, main_heading, cover_page_index=cover_page_index)

        # obtain all level 2 headings as chapters
        chapters = []
        for h in main_heading.descendants:
            if isinstance(h, Heading) and h.level == 2:
                chapters.append(h)

        if not chapters:
            raise MarkdownDocumentError("Markdown document must have at least one level 2 heading")

        catalog_last_index = CatalogPage.generate_slide(template_prs, chapters, catalog_page_index=catalog_page_index)

        chapter_home_page_index = catalog_last_index + 1
        chapter_content_page_index = chapter_home_page_index + 1
        end_page_index = chapter_content_page_index + 1
        current_slide_index = end_page_index + 1

        for chapter_index, chapter in enumerate(chapters):
            ChapterHomePage.generate_slide(
                template_prs,
                chapter,
                chapter_home_page_index=chapter_home_page_index,
                chapter_number=chapter_index + 1,
                slide_index=current_slide_index,
            )
            current_slide_index += 1

            ChapterContentPage.generate_slide(
                template_prs,
                chapter,
                chapter_page_index=chapter_content_page_index,
                slide_index=current_slide_index,
            )
            current_slide_index += 1

        EndPage.generate_slide(template_prs, end_page_index=end_page_index, slide_index=current_slide_index)

        self._cleanup_template_slides(
            template_prs, [chapter_home_page_index, chapter_content_page_index, end_page_index]
        )

        return template_prs

    def _cleanup_template_slides(self, template_prs: Presentation, be_removed_slides_index: list[int]) -> None:
        # delete slides from back to front
        be_removed_slides_index.sort(reverse=True)
        for i in be_removed_slides_index:
            CoverPage.remove_slide(template_prs, i)
