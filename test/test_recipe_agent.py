import asyncio

import pytest

from slidegen.services.presentation.recipe_agent import (
    RecipeAgent, RecipeAgentError, AgentRecipeOutput, AgentRegionOutput,
)
from slidegen.services.presentation.design_tokens import DEFAULT_TOKENS
from slidegen.services.presentation.recipes import LayoutRecipe
from slidegen.services.presentation.semantic import SlideSpec, SlideKind, BlockSpec, BlockKind


def _valid_output() -> AgentRecipeOutput:
    return AgentRecipeOutput(
        name="TestRecipe",
        regions=[
            AgentRegionOutput(region_id="title", x_frac=0.08, y_frac=0.05, w_frac=0.84, h_frac=0.12, z_layer=10),
            AgentRegionOutput(region_id="body", x_frac=0.08, y_frac=0.22, w_frac=0.84, h_frac=0.60, z_layer=10),
        ],
        region_roles={"title": "title", "body": "body"},
        region_block_indexes={"body": 0},
        region_text_sources={"title": "slide_title", "body": "block_text"},
    )


def _make_spec() -> SlideSpec:
    return SlideSpec(
        kind=SlideKind.CONTENT_POINTS, title="Test", source_level=2,
        blocks=(
            BlockSpec(kind=BlockKind.POINT, title="A", text="Content A"),
            BlockSpec(kind=BlockKind.POINT, title="B", text="Content B"),
        ),
    )


def _mock_arun(return_value: AgentRecipeOutput):
    """Create a mock coroutine that simulates RecipeAgent._run_agent structured output."""
    async def _mock(_prompt: str):
        return return_value
    return _mock


@pytest.mark.anyio
async def test_agent_parses_valid_response():
    agent = RecipeAgent()
    agent._run_agent = _mock_arun(_valid_output())
    recipe = await agent.generate(_make_spec(), DEFAULT_TOKENS)
    assert isinstance(recipe, LayoutRecipe)
    assert recipe.name == "TestRecipe"
    assert len(recipe.regions) == 2
    assert recipe.region_block_indexes == {"body": 0}


@pytest.mark.anyio
async def test_agent_raises_on_empty_regions():
    agent = RecipeAgent()
    empty_output = AgentRecipeOutput(name="Empty", regions=[], region_roles={})
    agent._run_agent = _mock_arun(empty_output)
    with pytest.raises(RecipeAgentError):
        await agent.generate(_make_spec(), DEFAULT_TOKENS)


@pytest.mark.anyio
async def test_agent_raises_on_timeout():
    async def _slow(_prompt: str):
        await asyncio.sleep(1.0)
    agent = RecipeAgent()
    agent._run_agent = _slow
    with pytest.raises(RecipeAgentError):
        await agent.generate(_make_spec(), DEFAULT_TOKENS, timeout=0.1)


@pytest.mark.anyio
async def test_agent_recipe_output_pydantic_validates_fields():
    """Pydantic auto-validation: z_layer must be a Literal value."""
    with pytest.raises(Exception):  # Pydantic ValidationError
        AgentRegionOutput(region_id="bad", x_frac=0.1, y_frac=0.1, w_frac=0.5, h_frac=0.5, z_layer=15)


@pytest.mark.anyio
async def test_agent_recipe_output_rejects_out_of_bounds_coords():
    """Pydantic auto-validation: x_frac must be in [0,1] range."""
    with pytest.raises(Exception):
        AgentRegionOutput(region_id="bad", x_frac=-0.1, y_frac=0.1, w_frac=0.5, h_frac=0.5, z_layer=10)


@pytest.mark.anyio
async def test_agent_recipe_output_rejects_overflow():
    """Pydantic auto-validation: w_frac must be in [0,1] range."""
    with pytest.raises(Exception):
        AgentRegionOutput(region_id="bad", x_frac=0.1, y_frac=0.1, w_frac=1.5, h_frac=0.5, z_layer=10)


from slidegen.services.presentation.recipe_agent import resolve_recipe


@pytest.mark.anyio
async def test_resolve_recipe_falls_back_on_agent_error():
    agent = RecipeAgent()
    async def _fail(_prompt: str):
        raise RecipeAgentError("mock failure")
    agent._run_agent = _fail
    spec = _make_spec()
    recipe = await resolve_recipe(spec, DEFAULT_TOKENS, agent=agent, enable_agent=True)
    assert isinstance(recipe, LayoutRecipe)
    assert recipe.name in ("TitleBodyRecipe", "GridCardsRecipe", "TwoColumnRecipe",
                           "CoverRecipe", "AgendaRecipe", "ClosingRecipe")


@pytest.mark.anyio
async def test_resolve_recipe_uses_fallback_when_agent_disabled():
    agent = RecipeAgent()
    agent._run_agent = _mock_arun(_valid_output())
    spec = _make_spec()
    recipe = await resolve_recipe(spec, DEFAULT_TOKENS, agent=agent, enable_agent=False)
    assert isinstance(recipe, LayoutRecipe)
    assert recipe.name in ("TitleBodyRecipe", "GridCardsRecipe", "TwoColumnRecipe",
                           "CoverRecipe", "AgendaRecipe", "ClosingRecipe")


from slidegen.services.presentation.recipe_agent import resolve_all_recipes


@pytest.mark.anyio
async def test_resolve_all_recipes_concurrent():
    agent = RecipeAgent()
    call_count = 0
    async def slow_agent(_prompt: str):
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.05)
        return _valid_output()
    agent._run_agent = slow_agent

    specs = [_make_spec() for _ in range(5)]
    recipes = await resolve_all_recipes(specs, DEFAULT_TOKENS, agent=agent, enable_agent=True)

    assert len(recipes) == 5
    assert call_count == 5
    for r in recipes:
        assert isinstance(r, LayoutRecipe)


@pytest.mark.anyio
async def test_resolve_all_recipes_one_failure_doesnt_block_others():
    agent = RecipeAgent()
    call_count = 0
    async def flaky_agent(_prompt: str):
        nonlocal call_count
        call_count += 1
        call_index = call_count
        await asyncio.sleep(0.01)
        if call_index == 2:
            raise RecipeAgentError("injected failure")
        return _valid_output()
    agent._run_agent = flaky_agent

    specs = [_make_spec() for _ in range(4)]
    recipes = await resolve_all_recipes(specs, DEFAULT_TOKENS, agent=agent, enable_agent=True)

    assert len(recipes) == 4
    assert call_count == 4
    assert recipes[1].name != "TestRecipe"
