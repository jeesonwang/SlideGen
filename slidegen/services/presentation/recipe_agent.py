from __future__ import annotations

import asyncio
import logging
from typing import Annotated, Literal

from agno.agent import Agent
from pydantic import BaseModel, Field

from slidegen.services.presentation.design_tokens import DesignTokens
from slidegen.services.presentation.recipes import LayoutRecipe
from slidegen.services.presentation.region import Region, RegionRole, RepeatRule
from slidegen.services.presentation.semantic import SlideSpec

logger = logging.getLogger(__name__)


class RecipeAgentError(Exception):
    pass


# === Pydantic models for agno structured_output ===

class AgentRegionOutput(BaseModel):
    region_id: str
    x_frac: float = Field(ge=0.0, le=1.0)
    y_frac: float = Field(ge=0.0, le=1.0)
    w_frac: float = Field(ge=0.0, le=1.0)
    h_frac: float = Field(ge=0.0, le=1.0)
    z_layer: Literal[0, 10, 20, 30] = 10
    decoration_shape: Literal["rect", "rounded_rect", "ellipse", "line"] | None = None
    fill_role: str | None = None
    line_role: str | None = None
    opacity: float = Field(default=1.0, ge=0.0, le=1.0)


class AgentRepeatRuleOutput(BaseModel):
    seed: AgentRegionOutput
    step_x: float
    step_y: float
    role: str = "card"


class AgentRecipeOutput(BaseModel):
    """agno structured output model -- directly produce LayoutRecipe JSON schema."""
    name: str
    regions: list[AgentRegionOutput] = Field(default_factory=list)
    repeats: list[AgentRepeatRuleOutput] = Field(default_factory=list)
    region_roles: dict[str, str] = Field(default_factory=dict)
    region_block_indexes: dict[str, int] = Field(default_factory=dict)
    region_text_sources: dict[str, str] = Field(default_factory=dict)


# === Agent instructions (no need to write JSON format instructions, output_model schema auto-constrains) ===

RECIPE_AGENT_INSTRUCTIONS = """You are a slide layout designer. Given content blocks and visual constraints, produce a slide LayoutRecipe.

## Canvas
Coordinates are fractions (0.0-1.0) of canvas dimensions.
Use page_margin_x, page_margin_y as minimum inset from canvas edges.
Use card_gap for spacing between adjacent cards.

## Z-layer rules
- 0 = background fills
- 10 = content (titles, body, cards)
- 20 = decorations (bars, dividers, borders)
- 30 = foreground/footer (page numbers, sources)

## Design guidelines
- Title region at top, spanning most of the width
- Content regions should fill the remaining space below the title
- For N homogeneous blocks (AGENDA, PROCESS, TIMELINE), prefer RepeatRule over N individual regions
- step_x=0, step_y=card_h+gap for vertical stacking; step_x=card_w+gap, step_y=0 for horizontal row
- Card body text should go in a separate region from card decoration
- DECORATION regions use decoration_shape, fill_role, line_role for visual embellishment

## Region roles
title, subtitle, body, card, card_body, index, icon, image, note, source, footer, decoration

## Content binding
For every text/icon/image region that renders a block, include region_block_indexes[region_id] = block_index.
For text regions, include region_text_sources[region_id] as one of slide_title, block_title, block_text, block_title_text, index."""


class RecipeAgent:
    """LLM-driven layout recipe generation using agno Agent with structured outputs.

    Uses agno's structured_outputs + output_model to guarantee valid JSON schema
    without manual parsing. The Pydantic AgentRecipeOutput model constrains all
    field types and ranges (x_frac in [0,1], z_layer in {0,10,20,30}, etc.).
    """

    def __init__(self, model: "Model | None" = None):
        self._model = model

    async def generate(
        self,
        spec: SlideSpec,
        tokens: DesignTokens,
        timeout: float = 5.0,
    ) -> LayoutRecipe:
        prompt = self._build_prompt(spec, tokens)
        try:
            agent_output: AgentRecipeOutput = await asyncio.wait_for(
                self._run_agent(prompt),
                timeout=timeout,
            )
            recipe = self._to_layout_recipe(agent_output)
            self._validate_recipe(recipe, tokens)
            return recipe
        except (RecipeAgentError, asyncio.TimeoutError, ValueError) as e:
            raise RecipeAgentError(f"RecipeAgent failed: {e}") from e

    def _build_prompt(self, spec: SlideSpec, tokens: DesignTokens) -> str:
        blocks_lines = []
        for i, block in enumerate(spec.blocks):
            blocks_lines.append(
                f"  {i}. kind={block.kind.value}, title='{block.title[:60]}', "
                f"text_length={block.estimated_text_length}"
            )
        return (
            f"## Canvas\n"
            f"- Width: {tokens.slide_width} inches, Height: {tokens.slide_height} inches\n"
            f"- page_margin_x: {tokens.page_margin_x} inches\n"
            f"- page_margin_y: {tokens.page_margin_y} inches\n"
            f"- card_gap: {tokens.card_gap} inches\n"
            f"\n"
            f"## Content\n"
            f"- Slide kind: {spec.kind.value}\n"
            f"- Title: {spec.title}\n"
            f"- Blocks ({len(spec.blocks)} total):\n"
            f"{chr(10).join(blocks_lines)}\n"
        )

    async def _run_agent(self, prompt: str) -> AgentRecipeOutput:
        agent = Agent(
            name="Slide layout designer",
            description=(
                "You are a slide layout designer. You produce LayoutRecipe objects "
                "with Region coordinates, z_layer values, and optional RepeatRules."
            ),
            instructions=[RECIPE_AGENT_INSTRUCTIONS],
            model=self._model,
            # agno structured output: auto-parse LLM output into AgentRecipeOutput
            structured_outputs=True,
            output_model=AgentRecipeOutput,
        )
        response = await agent.arun(prompt)
        # When structured_outputs is enabled, response.content is directly an AgentRecipeOutput instance
        if isinstance(response.content, AgentRecipeOutput):
            return response.content
        # fallback: if agno didn't auto-parse, try manual construction from dict
        if isinstance(response.content, dict):
            return AgentRecipeOutput.model_validate(response.content)
        raise RecipeAgentError(f"Unexpected agent output type: {type(response.content)}")

    def _to_layout_recipe(self, output: AgentRecipeOutput) -> LayoutRecipe:
        """Convert agno structured output to internal LayoutRecipe dataclass."""
        regions = tuple(
            Region(
                region_id=r.region_id,
                x_frac=r.x_frac,
                y_frac=r.y_frac,
                w_frac=r.w_frac,
                h_frac=r.h_frac,
                z_layer=r.z_layer,
                decoration_shape=r.decoration_shape,
                fill_role=r.fill_role,
                line_role=r.line_role,
                opacity=r.opacity,
            )
            for r in output.regions
        )

        repeats = tuple(
            RepeatRule(
                seed=Region(
                    region_id=rr.seed.region_id,
                    x_frac=rr.seed.x_frac,
                    y_frac=rr.seed.y_frac,
                    w_frac=rr.seed.w_frac,
                    h_frac=rr.seed.h_frac,
                    z_layer=rr.seed.z_layer,
                    decoration_shape=rr.seed.decoration_shape,
                    fill_role=rr.seed.fill_role,
                    line_role=rr.seed.line_role,
                ),
                step_x=rr.step_x,
                step_y=rr.step_y,
                role=RegionRole(rr.role),
            )
            for rr in output.repeats
        )

        region_roles = {
            rid: RegionRole(role)
            for rid, role in output.region_roles.items()
        }

        return LayoutRecipe(
            name=output.name,
            regions=regions,
            repeats=repeats,
            region_roles=region_roles,
            region_block_indexes=output.region_block_indexes,
            region_text_sources=output.region_text_sources,
            supported_block_kinds=frozenset(),
        )

    def _validate_recipe(self, recipe: LayoutRecipe, tokens: DesignTokens) -> None:
        """Secondary validation: Pydantic does basic validation, but business logic (non-empty etc.) is checked here."""
        if not recipe.regions and not recipe.repeats:
            raise RecipeAgentError("LayoutRecipe must have at least one region or repeat rule")
        for region in recipe.regions:
            if region.x_frac + region.w_frac > 1.01:
                raise RecipeAgentError(f"Region {region.region_id}: right edge out of canvas")
            if region.y_frac + region.h_frac > 1.01:
                raise RecipeAgentError(f"Region {region.region_id}: bottom edge out of canvas")


from slidegen.services.presentation.preset_recipes import PresetRecipeFallback


async def resolve_recipe(
    spec: SlideSpec,
    tokens: DesignTokens,
    *,
    agent: RecipeAgent | None = None,
    fallback: PresetRecipeFallback | None = None,
    enable_agent: bool = True,
    agent_timeout: float = 5.0,
) -> LayoutRecipe:
    fallback = fallback or PresetRecipeFallback()

    if not enable_agent or agent is None:
        logger.info("RecipeAgent disabled — using PresetRecipeFallback for '%s'", spec.title)
        return fallback.select(spec, tokens)

    try:
        recipe = await agent.generate(spec, tokens, timeout=agent_timeout)
        logger.info("RecipeAgent generated recipe '%s' for '%s'", recipe.name, spec.title)
        return recipe
    except RecipeAgentError as e:
        logger.warning("RecipeAgent failed for '%s': %s — falling back to preset", spec.title, e)
        return fallback.select(spec, tokens)
