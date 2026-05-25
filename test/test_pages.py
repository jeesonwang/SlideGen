import os
import sys
from collections import Counter

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "slidegen"))

from pptx import Presentation

from slidegen.services.document import MarkdownDocument
from slidegen.services.document.markdown.elements import Heading
from slidegen.services.presentation.orchestrator import PresentationOrchestrator
from slidegen.services.presentation.pages import CatalogPage, ChapterContentPage, ChapterHomePage, CoverPage, Page


class TestPages:
    """test pages"""

    @pytest.fixture
    def markdown_path(self):
        """test markdown file path"""
        return os.path.join(os.path.dirname(__file__), "data", "report.md")

    @pytest.fixture
    def template_path(self):
        """test template file path"""
        return os.path.join(os.path.dirname(__file__), "data", "template_0.pptx")

    @pytest.fixture
    def presentation(self, template_path):
        """test presentation"""
        return Presentation(template_path)

    def test_markdown_document_parse(self, markdown_path):
        """test MarkdownDocument"""
        doc = MarkdownDocument(markdown_path)

        assert doc is not None
        headings = [elem for elem in doc.main.children]
        assert len(headings) > 0

    @pytest.fixture
    def markdown_document(self, markdown_path):
        doc = MarkdownDocument(markdown_path)
        return doc

    @pytest.fixture
    def heading_list(self, markdown_document):
        return [elem for elem in markdown_document.main.children]

    async def test_cover_page_generation(self, presentation):
        """test CoverPage"""
        title = Heading(level=1, text="Hello World!")

        await CoverPage.generate_slide(presentation, title, cover_page_index=0)

        temp_output = os.path.join(os.path.dirname(__file__), "test_cover.pptx")
        presentation.save(temp_output)

        assert os.path.exists(temp_output)

    async def test_catalog_page_generation(self, presentation, heading_list):
        """test CatalogPage"""

        await CatalogPage.generate_slide(presentation, heading_list, catalog_page_index=1)
        # save generated PPT file for test
        temp_output = os.path.join(os.path.dirname(__file__), "test_catalog.pptx")
        presentation.save(temp_output)

        # verify if the file is successfully saved
        assert os.path.exists(temp_output)

    async def test_catalog_page_generation_keeps_all_chapters_across_recursive_pages(self):
        """CatalogPage should keep every chapter when recursive pages are needed."""
        presentation = Presentation(os.path.join(os.path.dirname(__file__), "data", "template_0.pptx"))
        heading_list = [Heading(level=2, text=f"Chapter {i}") for i in range(1, 15)]

        last_catalog_index = await CatalogPage.generate_slide(presentation, heading_list, catalog_page_index=1)

        catalog_texts = []
        for slide_index in range(1, last_catalog_index + 1):
            catalog_texts.extend(
                shape.text.strip()
                for shape in presentation.slides[slide_index].shapes
                if shape.has_text_frame and shape.text.strip()
            )
        assert {f"Chapter {i}" for i in range(1, 15)} <= set(catalog_texts)

    async def test_catalog_page_cloned_shapes_keep_unique_ids_and_background_order(self):
        """Cloned catalog shapes should be valid and keep backgrounds under text."""
        presentation = Presentation(os.path.join(os.path.dirname(__file__), "data", "template_0.pptx"))
        catalog_slide = presentation.slides[1]
        catalog_items = CatalogPage._get_catalog_items(catalog_slide)

        for item in catalog_items[2:]:
            Page.remove_shapes(
                catalog_slide.shapes._spTree,
                [
                    item.number_shape["shape"],
                    item.text_shape["shape"],
                    *([item.background_shape["shape"]] if item.background_shape else []),
                ],
            )

        heading_list = [Heading(level=2, text=f"Chapter {i}") for i in range(1, 5)]
        await CatalogPage.generate_slide(presentation, heading_list, catalog_page_index=1)

        shape_ids = [shape.shape_id for shape in catalog_slide.shapes]
        duplicate_ids = [shape_id for shape_id, count in Counter(shape_ids).items() if count > 1]
        assert duplicate_ids == []

        refreshed_items = CatalogPage._get_catalog_items(catalog_slide)
        shape_order = {shape._element: index for index, shape in enumerate(catalog_slide.shapes)}
        for item in refreshed_items:
            if item.background_shape is None:
                continue
            background_index = shape_order[item.background_shape["shape"]._element]
            assert background_index < shape_order[item.number_shape["shape"]._element]
            assert background_index < shape_order[item.text_shape["shape"]._element]

    async def test_chapter_home_page_generation(self, presentation, heading_list):
        """test ChapterHomePage"""
        title = Heading(level=2, text="Hello World! This is a test title.")
        await ChapterHomePage.generate_slide(
            presentation, title, chapter_home_page_index=2, chapter_number=1, slide_index=2
        )
        temp_output = os.path.join(os.path.dirname(__file__), "test_chapter_home.pptx")
        presentation.save(temp_output)
        assert os.path.exists(temp_output)

    async def test_chapter_content_page_generation(self, presentation, heading_list):
        """test ChapterContentPage"""
        content = heading_list[0]
        await ChapterContentPage.generate_slide(presentation, content, chapter_page_index=4, slide_index=4)
        temp_output = os.path.join(os.path.dirname(__file__), "test_chapter_content.pptx")
        presentation.save(temp_output)
        assert os.path.exists(temp_output)

    async def test_ppt_generation(self, presentation, markdown_document):
        """test PresentationOrchestrator"""
        ppt_gen = PresentationOrchestrator()
        template_prs = Presentation(os.path.join(os.path.dirname(__file__), "data", "template_0.pptx"))
        await ppt_gen.generate(template_prs, markdown_document)
        temp_output = os.path.join(os.path.dirname(__file__), "test_ppt.pptx")
        template_prs.save(temp_output)
        assert os.path.exists(temp_output)

    async def test_nested_ppt_generation(self):
        """test PresentationOrchestrator with chapter/section/topic markdown"""
        markdown_document = MarkdownDocument(
            "# Product Strategy\n"
            "## Market Context\n"
            "### Customer Signals\n"
            "#### Demand\n"
            "Customers want faster onboarding.\n"
            "### Competitive Position\n"
            "#### Differentiation\n"
            "Workflow depth matters most.\n"
            "### Buying Motion\n"
            "#### Procurement\n"
            "Enterprise cycles are longer.\n"
            "### Expansion Path\n"
            "#### Accounts\n"
            "Existing accounts need reporting.\n"
            "### Risk Review\n"
            "#### Delivery\n"
            "Scope needs tight sequencing.\n"
        )
        ppt_gen = PresentationOrchestrator()
        template_prs = Presentation(os.path.join(os.path.dirname(__file__), "data", "template_0.pptx"))

        await ppt_gen.generate(template_prs, markdown_document)

        temp_output = os.path.join(os.path.dirname(__file__), "test_nested_ppt.pptx")
        template_prs.save(temp_output)
        assert os.path.exists(temp_output)
