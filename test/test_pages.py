import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "slidegen"))

from pptx import Presentation

from slidegen.services.document import MarkdownDocument
from slidegen.services.document.markdown.elements import Heading
from slidegen.services.presentation.converter import MarkdownToPresentation
from slidegen.services.presentation.pages import CatalogPage, ChapterContentPage, ChapterHomePage, CoverPage


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
        """test MarkdownToPresentation"""
        ppt_gen = MarkdownToPresentation()
        template_prs = Presentation(os.path.join(os.path.dirname(__file__), "data", "template_0.pptx"))
        await ppt_gen.generate(template_prs, markdown_document)
        temp_output = os.path.join(os.path.dirname(__file__), "test_ppt.pptx")
        template_prs.save(temp_output)
        assert os.path.exists(temp_output)
