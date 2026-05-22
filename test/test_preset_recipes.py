from slidegen.services.presentation.preset_recipes import PresetRecipeFallback
from slidegen.services.presentation.design_tokens import DEFAULT_TOKENS
from slidegen.services.presentation.recipes import LayoutRecipe
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

    def test_select_returns_layout_recipe(self):
        spec = _make_spec(SlideKind.CONTENT_POINTS, ["a" * 50, "b" * 50, "c" * 50, "d" * 50])
        recipe = self.fallback.select(spec, DEFAULT_TOKENS)
        assert isinstance(recipe, LayoutRecipe)
        assert recipe.name == "GridCardsRecipe"

    def test_all_regions_within_canvas(self):
        for kind in SlideKind:
            texts = ["Test content"] * 4
            spec = _make_spec(kind, texts)
            recipe = self.fallback.select(spec, DEFAULT_TOKENS)
            for region in recipe.regions:
                assert 0.0 <= region.x_frac <= 1.0, f"{kind}: x out of bounds"
                assert 0.0 <= region.y_frac <= 1.0, f"{kind}: y out of bounds"
