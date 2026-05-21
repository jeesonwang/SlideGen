import os

import pytest
from pptx import Presentation
from pptx.util import Inches

from slidegen.exceptions import PPTTemplateError
from slidegen.services.document import MarkdownDocument
from slidegen.services.presentation.template_profile import (
    TemplateRole,
    _has_keyword_match,
    profile_presentation_template,
)


def _template_path() -> str:
    return os.path.join(os.path.dirname(__file__), "data", "template_0.pptx")


def _markdown_document(markdown: str) -> MarkdownDocument:
    return MarkdownDocument(markdown)


def _add_text_slide(presentation: Presentation, lines: list[str], *, layout_index: int = 6) -> None:
    slide = presentation.slides.add_slide(presentation.slide_layouts[layout_index])
    if layout_index == 0:
        slide.shapes.title.text = lines[0]
        if len(lines) > 1 and len(slide.placeholders) > 1:
            slide.placeholders[1].text = lines[1]
        return

    textbox = slide.shapes.add_textbox(Inches(0.8), Inches(0.8), Inches(8.0), Inches(4.5))
    frame = textbox.text_frame
    frame.text = lines[0]
    for line in lines[1:]:
        paragraph = frame.add_paragraph()
        paragraph.text = line


def test_profile_curated_template_detects_legacy_roles():
    presentation = Presentation(_template_path())

    profile = profile_presentation_template(presentation)

    assert profile.slide_count >= 5
    assert profile.role_index(TemplateRole.COVER) == 0
    assert profile.role_index(TemplateRole.CATALOG) == 1
    assert profile.role_index(TemplateRole.CHAPTER) == 2
    assert profile.role_index(TemplateRole.CONTENT) == 3
    assert profile.role_index(TemplateRole.END) == 4
    assert profile.has_role(TemplateRole.CONTENT)
    assert profile.status == "ready"
    assert profile.missing_roles == []
    assert profile.warnings == []


def test_profile_one_slide_template_warns_missing_roles_without_rejecting():
    presentation = Presentation()
    presentation.slides.add_slide(presentation.slide_layouts[0])

    profile = profile_presentation_template(presentation)

    assert profile.slide_count == 1
    assert profile.role_index(TemplateRole.COVER) == 0
    assert profile.role_index(TemplateRole.CATALOG) is None
    assert profile.role_index(TemplateRole.CHAPTER) is None
    assert profile.role_index(TemplateRole.CONTENT) is None
    assert profile.role_index(TemplateRole.END) is None
    assert profile.status == "review_required"
    assert TemplateRole.CATALOG.value in profile.missing_roles
    assert TemplateRole.CONTENT.value in profile.missing_roles
    assert "catalog role not detected" in " ".join(profile.warnings)
    assert "content role not detected" in " ".join(profile.warnings)


def test_profile_empty_presentation_rejects_as_unusable():
    presentation = Presentation()

    with pytest.raises(PPTTemplateError, match="must contain at least one slide"):
        profile_presentation_template(presentation)


def test_keyword_matching_avoids_english_substring_false_positives():
    text = "department partnership discovery recovery coverage"

    assert not _has_keyword_match(text, ("part", "cover"))
    assert _has_keyword_match("Part 1: Market landscape", ("part",))
    assert _has_keyword_match("封面设计", ("封面",))


def test_profile_uses_global_assignment_when_cover_and_catalog_compete():
    presentation = Presentation()
    _add_text_slide(presentation, ["Agenda", "1. Market", "2. Product", "3. Finance"])
    _add_text_slide(presentation, ["Title", "Annual Business Review"], layout_index=0)
    _add_text_slide(presentation, ["Chapter 1", "Market Landscape"])
    _add_text_slide(
        presentation,
        [
            "Market analysis",
            "Revenue grew 18 percent year over year.",
            "Enterprise demand remains strongest in regulated industries.",
            "Retention stays above target.",
        ],
    )
    _add_text_slide(presentation, ["Thank You", "Questions"])

    profile = profile_presentation_template(presentation)

    assert profile.role_index(TemplateRole.CATALOG) == 0
    assert profile.role_index(TemplateRole.COVER) == 1
    assert profile.status == "ready"
