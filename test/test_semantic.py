from slidegen.services.presentation.semantic import (
    SlideKind,
    BlockKind,
    BlockSpec,
    SlideSpec,
    build_content_slide_spec,
    infer_slide_kind,
)
from slidegen.services.document.markdown import MarkdownDocument
from slidegen.services.slidegen.outline_structure import iter_chapter_slide_groups


def _first_content_slide(markdown: str):
    doc = MarkdownDocument(markdown)
    groups = list(iter_chapter_slide_groups(doc.main))
    assert groups
    assert groups[0].slides
    return groups[0].slides[0]


class TestBlockSpec:
    def test_estimated_text_length_is_character_count(self):
        block = BlockSpec(kind=BlockKind.POINT, title="Title", text="Hello World")
        assert block.estimated_text_length == 11

    def test_empty_text(self):
        block = BlockSpec(kind=BlockKind.PARAGRAPH, title="", text="")
        assert block.estimated_text_length == 0


class TestSlideSpec:
    def test_total_text_length_aggregates_blocks(self):
        blocks = (
            BlockSpec(kind=BlockKind.POINT, title="A", text="aaaa"),
            BlockSpec(kind=BlockKind.POINT, title="B", text="bb"),
        )
        spec = SlideSpec(kind=SlideKind.CONTENT_POINTS, title="Test", source_level=2, blocks=blocks)
        assert spec.total_text_length == 6

    def test_block_kinds(self):
        blocks = (
            BlockSpec(kind=BlockKind.POINT, title="A", text="a"),
            BlockSpec(kind=BlockKind.PARAGRAPH, title="B", text="b"),
        )
        spec = SlideSpec(kind=SlideKind.CONTENT_POINTS, title="Test", source_level=2, blocks=blocks)
        assert spec.block_kinds == frozenset({BlockKind.POINT, BlockKind.PARAGRAPH})

    def test_has_data_false_for_points_only(self):
        blocks = (BlockSpec(kind=BlockKind.POINT, title="A", text="a"),)
        spec = SlideSpec(kind=SlideKind.CONTENT_POINTS, title="Test", source_level=2, blocks=blocks)
        assert not spec.has_data

    def test_has_data_true_when_table_present(self):
        blocks = (BlockSpec(kind=BlockKind.TABLE, title="T", text="1,2,3"),)
        spec = SlideSpec(kind=SlideKind.DATA_TABLE, title="Test", source_level=2, blocks=blocks)
        assert spec.has_data


class TestSlideKindInference:
    def test_default_content_points(self):
        content = _first_content_slide("# Deck\n## Chapter\n### Point\nBody text")
        spec = build_content_slide_spec(content)
        assert spec.kind == SlideKind.CONTENT_POINTS

    def test_data_table_detected(self):
        content = _first_content_slide("# Deck\n## Chapter\n### Data\n\n| A | B |\n|---|---|\n| 1 | 2 |\n")
        spec = build_content_slide_spec(content)
        assert spec.kind == SlideKind.DATA_TABLE

    def test_process_detected_for_numbered_list(self):
        content = _first_content_slide("# Deck\n## Chapter\n### Steps\n1. First step\n2. Second step\n3. Third step")
        spec = build_content_slide_spec(content)
        assert spec.kind == SlideKind.PROCESS

    def test_comparison_detected_for_two_subheadings(self):
        content = _first_content_slide("# Deck\n## Chapter\n### Compare\n#### Left\nLeft body\n#### Right\nRight body")
        spec = build_content_slide_spec(content)
        assert spec.kind == SlideKind.COMPARISON

    def test_timeline_detected_for_year_pattern(self):
        content = _first_content_slide("# Deck\n## Chapter\n### History\n2020年 公司成立\n2022年 产品发布")
        spec = build_content_slide_spec(content)
        assert spec.kind == SlideKind.TIMELINE
