from pptx import Presentation

from slidegen.services.presentation.design_tokens import (
    DesignTokens,
    DEFAULT_TOKENS,
    PRESET_TOKENS,
    extract_design_tokens_from_presentation,
    _hex_to_hsl,
)


class TestDesignTokens:
    def test_default_tokens_is_frozen(self):
        import dataclasses
        assert dataclasses.is_dataclass(DEFAULT_TOKENS)

    def test_preset_tokens_contain_expected_themes(self):
        assert "general" in PRESET_TOKENS
        assert "minimal" in PRESET_TOKENS
        assert "academic" in PRESET_TOKENS
        assert PRESET_TOKENS["minimal"].primary == "#2C2C2C"


class TestHexToHsl:
    def test_black(self):
        h, s, l = _hex_to_hsl("#000000")
        assert l == 0.0

    def test_white(self):
        h, s, l = _hex_to_hsl("#FFFFFF")
        assert l == 1.0

    def test_red(self):
        h, s, l = _hex_to_hsl("#FF0000")
        assert abs(h - 0) < 1 or abs(h - 360) < 1
        assert s > 0.9


class TestExtractDesignTokens:
    def test_extract_from_empty_presentation_returns_preset_tokens(self):
        prs = Presentation()
        prs.slides.add_slide(prs.slide_layouts[0])
        tokens = extract_design_tokens_from_presentation(prs, "general")
        assert tokens.primary == DEFAULT_TOKENS.primary
        assert tokens.accent == DEFAULT_TOKENS.accent

    def test_extract_respects_theme_name(self):
        prs = Presentation()
        prs.slides.add_slide(prs.slide_layouts[0])
        tokens = extract_design_tokens_from_presentation(prs, "academic")
        assert tokens.title_font == "Times New Roman"
