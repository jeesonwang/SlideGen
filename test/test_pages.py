import asyncio
import os
import sys
import zipfile
from collections import Counter
from io import BytesIO
from types import SimpleNamespace

import pytest
from PIL import Image
from pptx.enum.shapes import PP_PLACEHOLDER
from pptx.util import Emu

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "slidegen"))

from pptx import Presentation

import slidegen.services.presentation.pages as pages_module
from slidegen.schemas.theme import PresentationTheme, ThemeColorMapping
from slidegen.services.document import MarkdownDocument
from slidegen.services.document.markdown.elements import Heading
from slidegen.services.presentation.components import ComponentContentType, CShape, Location, Style
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

    def test_cover_page_generation_keeps_title_word_wrap_disabled(self, presentation):
        """Cover title placeholders should keep the previous no-wrap behavior."""
        title = Heading(level=1, text="A Long Cover Title")

        asyncio.run(CoverPage.generate_slide(presentation, title, cover_page_index=0))

        title_placeholder = next(
            shape
            for shape in presentation.slides[0].shapes.placeholders
            if shape.placeholder_format.type in (PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE)
        )
        assert title_placeholder.text_frame.word_wrap is False

    def test_cover_page_generation_expands_narrow_title_box_first(self, presentation):
        """Long no-wrap titles should first expand their text box."""
        title_placeholder = next(
            shape
            for shape in presentation.slides[0].shapes.placeholders
            if shape.placeholder_format.type in (PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE)
        )
        title_placeholder.width = title_placeholder.width // 5
        narrow_width = title_placeholder.width

        title = Heading(level=1, text="A Very Long Strategy Report Title That Needs More Horizontal Space")

        asyncio.run(CoverPage.generate_slide(presentation, title, cover_page_index=0))

        assert title_placeholder.text_frame.word_wrap is False
        assert title_placeholder.width > narrow_width
        assert title_placeholder.left + title_placeholder.width <= presentation.slide_width

    def test_injected_page_placeholder_scales_to_current_slide_size(self, presentation, monkeypatch):
        """Fallback page placeholders from shape.json should scale to the active template size."""
        source_width = int(presentation.slide_width)
        source_height = int(presentation.slide_height)
        presentation.slide_width = Emu(source_width * 2)
        presentation.slide_height = Emu(source_height * 3)

        blank_slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        source_shape = next(shape for shape in presentation.slides[0].shapes if shape.has_text_frame)
        fallback_location = Location(x=1000, y=2000, width=3000000, height=400000)
        fallback_placeholder = SimpleNamespace(
            xml=source_shape.element.xml,
            location=fallback_location,
        )

        class FakeComponentsManager:
            metadata = {"slide_width": source_width, "slide_height": source_height}

            def get_page_placeholder(self, _page_type, _role):
                return fallback_placeholder

        monkeypatch.setattr(pages_module, "components_manager", FakeComponentsManager())

        injected = Page._find_or_inject_placeholder(
            slide=blank_slide,
            page_type="cover",
            role="title",
            text="T",
            placeholder_types=(),
        )

        assert injected is not None
        assert injected.left == 2000
        assert injected.top == 6000
        assert injected.width == 6000000
        assert injected.height == 1200000

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

    @pytest.mark.anyio
    async def test_chapter_content_page_title_is_above_imported_style_shapes(self, monkeypatch):
        """Page-level titles should be brought above shapes imported from the style."""
        presentation = Presentation()
        for _ in range(5):
            presentation.slides.add_slide(presentation.slide_layouts[6])

        xml_source_slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        xml_source_shape = xml_source_slide.shapes.add_textbox(Emu(0), Emu(0), Emu(1000000), Emu(300000))
        xml_source_shape.text = "placeholder"

        fallback_placeholder = SimpleNamespace(
            xml=xml_source_shape.element.xml,
            location=Location(x=100000, y=100000, width=2000000, height=400000),
        )
        style = Style("covering_decoration")
        style.add_shape(
            "decoration_0",
            CShape(
                xml=xml_source_shape.element.xml,
                zorder=999,
                content_type=ComponentContentType.DECORATION,
                location=[Location(x=0, y=0, width=3000000, height=1000000)],
            ),
        )

        class FakeComponentsManager:
            def get_page_placeholder(self, _page_type, _role):
                return fallback_placeholder

            def get_random_style(self, _chapter_layout):
                return style

        monkeypatch.setattr(pages_module, "components_manager", FakeComponentsManager())

        content = Heading(level=2, text="Validation Test")
        content.append(Heading(level=3, text="Point 1"))

        await ChapterContentPage.generate_slide(
            presentation,
            content,
            chapter_page_index=4,
            slide_index=4,
            style_override=style,
        )

        generated_slide = presentation.slides[4]
        assert generated_slide.shapes[-1].name == "content_title_title"

    @pytest.mark.anyio
    async def test_chapter_content_picture_uses_placeholder_when_generation_fails(self, presentation, monkeypatch):
        """Picture styles should not call add_picture with None when generation fails."""
        style = Style("picture_only")
        style.add_shape(
            "picture",
            CShape(
                xml=None,
                zorder=0,
                content_type=ComponentContentType.PICTURE,
                location=[Location(x=Emu(900000), y=Emu(1200000), width=Emu(2500000), height=Emu(1600000))],
            ),
        )

        class FakeComponentsManager:
            def get_random_style(self, _chapter_layout):
                return style

            def get_page_placeholder(self, _page_type, _role):
                return None

        class FailingImageGenerator:
            async def generate_image(self, _prompt):
                return SimpleNamespace(path=None)

        monkeypatch.setattr(pages_module, "components_manager", FakeComponentsManager())
        monkeypatch.setattr(ChapterContentPage, "image_generator", FailingImageGenerator())

        content = Heading(level=2, text="Market Context")
        content.append(Heading(level=3, text="Customer Signals"))

        await ChapterContentPage.generate_slide(presentation, content, chapter_page_index=4, slide_index=4)

        generated_slide = presentation.slides[4]
        assert any(shape.shape_type.name == "PICTURE" for shape in generated_slide.shapes)

    def test_recolor_png_icon_uses_theme_color_and_preserves_alpha(self, tmp_path):
        """Icon recoloring should replace visible RGB values while keeping the source alpha mask."""
        source_icon = tmp_path / "source.png"
        Image.new("RGBA", (2, 2), (0, 0, 0, 0)).save(source_icon)
        image = Image.open(source_icon).convert("RGBA")
        image.putpixel((0, 0), (0, 0, 0, 255))
        image.putpixel((1, 0), (0, 0, 0, 128))
        image.save(source_icon)

        recolored = ChapterContentPage._recolor_png_icon(str(source_icon), "E76F51", output_dir=tmp_path)
        recolored_image = Image.open(recolored).convert("RGBA")

        assert [pixel[3] for pixel in recolored_image.getdata()] == [255, 128, 0, 0]
        assert {pixel[:3] for pixel in recolored_image.getdata() if pixel[3] > 0} == {(231, 111, 81)}

    @pytest.mark.anyio
    async def test_chapter_content_icons_use_accent1_and_accent2_theme_colors(self, tmp_path, monkeypatch):
        """Generated icon pictures should be recolored with accent1/accent2 before insertion."""
        source_icon = tmp_path / "source.png"
        Image.new("RGBA", (8, 8), (0, 0, 0, 255)).save(source_icon)

        style = Style("icon_pair")
        style.add_shape(
            "icon",
            CShape(
                xml=None,
                zorder=0,
                content_type=ComponentContentType.ICON,
                location=[
                    Location(x=Emu(900000), y=Emu(1200000), width=Emu(250000), height=Emu(250000)),
                    Location(x=Emu(1300000), y=Emu(1200000), width=Emu(250000), height=Emu(250000)),
                ],
            ),
        )

        class FakeComponentsManager:
            def get_random_style(self, _chapter_layout):
                return style

            def get_page_placeholder(self, _page_type, _role):
                return None

        class FakeIconSearcher:
            async def search_icons(self, _query, k=1):
                return [str(source_icon)]

        monkeypatch.setattr(pages_module, "components_manager", FakeComponentsManager())
        monkeypatch.setattr(ChapterContentPage, "icon_searcher", FakeIconSearcher())

        presentation = Presentation()
        for _ in range(5):
            presentation.slides.add_slide(presentation.slide_layouts[6])

        content = Heading(level=2, text="Market Context")
        content.append(Heading(level=3, text="Customer Signals"))
        content.append(Heading(level=3, text="Competitive Position"))
        theme = PresentationTheme(
            name="Icon Theme",
            colors=ThemeColorMapping(accent1="E76F51", accent2="0066FF"),
        )

        await ChapterContentPage.generate_slide(
            presentation,
            content,
            chapter_page_index=4,
            slide_index=4,
            theme=theme,
        )

        output_path = tmp_path / "icons.pptx"
        presentation.save(output_path)
        embedded_rgbs = []
        with zipfile.ZipFile(output_path) as pptx:
            for media_name in sorted(name for name in pptx.namelist() if name.startswith("ppt/media/")):
                image = Image.open(BytesIO(pptx.read(media_name))).convert("RGBA")
                visible_rgbs = {pixel[:3] for pixel in image.getdata() if pixel[3] > 0}
                embedded_rgbs.append(next(iter(visible_rgbs)))

        assert embedded_rgbs == [(231, 111, 81), (0, 102, 255)]

    @pytest.mark.anyio
    async def test_chapter_content_shapes_scale_to_current_slide_size(self, presentation, monkeypatch):
        """Shape library locations should scale from the source canvas to the active template size."""
        source_width = int(presentation.slide_width)
        source_height = int(presentation.slide_height)
        presentation.slide_width = Emu(source_width * 2)
        presentation.slide_height = Emu(source_height * 3)

        style = Style("scaled_picture")
        style.add_shape(
            "picture",
            CShape(
                xml=None,
                zorder=0,
                content_type=ComponentContentType.PICTURE,
                location=[Location(x=1000, y=2000, width=3000, height=4000)],
            ),
        )

        class FakeComponentsManager:
            metadata = {"slide_width": source_width, "slide_height": source_height}

            def get_random_style(self, _chapter_layout):
                return style

            def get_page_placeholder(self, _page_type, _role):
                return None

        class FailingImageGenerator:
            async def generate_image(self, _prompt):
                return SimpleNamespace(path=None)

        monkeypatch.setattr(pages_module, "components_manager", FakeComponentsManager())
        monkeypatch.setattr(ChapterContentPage, "image_generator", FailingImageGenerator())

        content = Heading(level=2, text="Market Context")
        content.append(Heading(level=3, text="Customer Signals"))

        await ChapterContentPage.generate_slide(presentation, content, chapter_page_index=4, slide_index=4)

        generated_picture = next(shape for shape in presentation.slides[4].shapes if shape.shape_type.name == "PICTURE")
        assert generated_picture.left == 2000
        assert generated_picture.top == 6000
        assert generated_picture.width == 6000
        assert generated_picture.height == 12000

    @pytest.mark.anyio
    async def test_chapter_content_square_shape_scaling_keeps_square(self, presentation, monkeypatch):
        """Square shape locations should remain square when source and target slide ratios differ."""
        source_width = int(presentation.slide_width)
        source_height = int(presentation.slide_height)
        presentation.slide_width = Emu(source_width * 2)
        presentation.slide_height = Emu(source_height * 3)

        style = Style("scaled_square_picture")
        style.add_shape(
            "picture",
            CShape(
                xml=None,
                zorder=0,
                content_type=ComponentContentType.PICTURE,
                location=[Location(x=1000, y=2000, width=3000, height=3000)],
            ),
        )

        class FakeComponentsManager:
            metadata = {"slide_width": source_width, "slide_height": source_height}

            def get_random_style(self, _chapter_layout):
                return style

            def get_page_placeholder(self, _page_type, _role):
                return None

        class FailingImageGenerator:
            async def generate_image(self, _prompt):
                return SimpleNamespace(path=None)

        monkeypatch.setattr(pages_module, "components_manager", FakeComponentsManager())
        monkeypatch.setattr(ChapterContentPage, "image_generator", FailingImageGenerator())

        content = Heading(level=2, text="Market Context")
        content.append(Heading(level=3, text="Customer Signals"))

        await ChapterContentPage.generate_slide(presentation, content, chapter_page_index=4, slide_index=4)

        generated_picture = next(shape for shape in presentation.slides[4].shapes if shape.shape_type.name == "PICTURE")
        assert generated_picture.left == 2000
        assert generated_picture.top == 7500
        assert generated_picture.width == 6000
        assert generated_picture.height == 6000

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
