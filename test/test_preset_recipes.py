from slidegen.services.presentation.preset_recipes import PresetRecipeFallback
from slidegen.services.presentation.semantic import (
    SlideSpec, SlideKind, BlockSpec, BlockKind,
)


def _make_spec(kind: SlideKind, texts: list[str]) -> SlideSpec:
    blocks = tuple(
        BlockSpec(kind=BlockKind.POINT, title=t[:20], text=t)
        for t in texts
    )
    return SlideSpec(kind=kind, title="Test", source_level=2, blocks=blocks)


class TestPresetRecipeFallback:
    def setup_method(self):
        self.fallback = PresetRecipeFallback()

    def test_cover_returns_cover_recipe(self):
        spec = _make_spec(SlideKind.COVER, ["Cover text"])
        assert self.fallback.select_name(spec) == "CoverRecipe"

    def test_agenda_returns_agenda_recipe(self):
        spec = _make_spec(SlideKind.AGENDA, ["Item 1", "Item 2", "Item 3"])
        assert self.fallback.select_name(spec) == "AgendaRecipe"

    def test_closing_returns_closing_recipe(self):
        spec = _make_spec(SlideKind.CLOSING, ["Thank you"])
        assert self.fallback.select_name(spec) == "ClosingRecipe"

    def test_comparison_returns_two_column(self):
        spec = _make_spec(SlideKind.COMPARISON, ["Left side", "Right side"])
        assert self.fallback.select_name(spec) == "TwoColumnRecipe"

    def test_few_short_points_returns_grid_cards(self):
        spec = _make_spec(SlideKind.CONTENT_POINTS, ["a" * 50, "b" * 50, "c" * 50, "d" * 50])
        assert self.fallback.select_name(spec) == "GridCardsRecipe"

    def test_few_long_points_returns_title_body(self):
        spec = _make_spec(SlideKind.CONTENT_POINTS, ["a" * 300, "b" * 300])
        assert self.fallback.select_name(spec) == "TitleBodyRecipe"

    def test_deterministic_same_input_same_output(self):
        spec = _make_spec(SlideKind.CONTENT_POINTS, ["Point A", "Point B", "Point C"])
        assert self.fallback.select_name(spec) == self.fallback.select_name(spec)

    def test_unknown_kind_fallback(self):
        spec = _make_spec(SlideKind.SECTION_COVER, ["Some text"])
        name = self.fallback.select_name(spec)
        assert name in ("TitleBodyRecipe", "GridCardsRecipe", "CoverRecipe", "AgendaRecipe", "ClosingRecipe", "TwoColumnRecipe")
