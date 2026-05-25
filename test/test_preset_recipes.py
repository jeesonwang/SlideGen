from slidegen.services.presentation.design_tokens import DEFAULT_TOKENS
from slidegen.services.presentation.preset_recipes import PresetRecipeFallback
from slidegen.services.presentation.recipes import LayoutRecipe
from slidegen.services.presentation.semantic import (
    BlockKind,
    BlockSpec,
    SlideKind,
    SlideSpec,
)


def _make_spec(kind: SlideKind, texts: list[str]) -> SlideSpec:
    blocks = tuple(BlockSpec(kind=BlockKind.POINT, title=t[:20], text=t) for t in texts)
    return SlideSpec(kind=kind, title="Test", source_level=2, blocks=blocks)


class TestPresetRecipeFallback:
    def setup_method(self):
        self.fallback = PresetRecipeFallback()

    def test_select_returns_layout_recipe(self):
        spec = _make_spec(SlideKind.CONTENT_POINTS, ["a" * 50, "b" * 50, "c" * 50, "d" * 50])
        recipe = self.fallback.select(spec, DEFAULT_TOKENS)
        assert isinstance(recipe, LayoutRecipe)
        assert recipe.name == "ClassicFourPointsRecipe"

    def test_content_points_use_classic_shape_json_migrated_recipes(self):
        expected = {
            1: "ClassicOnePointRecipe",
            2: "ClassicTwoPointsRecipe",
            3: "ClassicThreePointsRecipe",
            4: "ClassicFourPointsRecipe",
        }
        for count, recipe_name in expected.items():
            spec = _make_spec(SlideKind.CONTENT_POINTS, [f"Point {i}" for i in range(count)])
            assert self.fallback.select(spec, DEFAULT_TOKENS).name == recipe_name

    def test_section_cover_has_dedicated_preset_recipe(self):
        spec = _make_spec(SlideKind.SECTION_COVER, ["Chapter title"])
        recipe = self.fallback.select(spec, DEFAULT_TOKENS)
        assert recipe.name == "SectionCoverRecipe"

    def test_comparison_uses_classic_two_point_recipe_without_agent(self):
        spec = _make_spec(SlideKind.COMPARISON, ["Left side", "Right side"])
        recipe = self.fallback.select(spec, DEFAULT_TOKENS)
        assert recipe.name == "ClassicTwoPointsRecipe"

    def test_all_regions_within_canvas(self):
        for kind in SlideKind:
            texts = ["Test content"] * 4
            spec = _make_spec(kind, texts)
            recipe = self.fallback.select(spec, DEFAULT_TOKENS)
            for region in recipe.regions:
                assert 0.0 <= region.x_frac <= 1.0, f"{kind}: x out of bounds"
                assert 0.0 <= region.y_frac <= 1.0, f"{kind}: y out of bounds"
