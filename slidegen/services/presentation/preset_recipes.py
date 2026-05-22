from __future__ import annotations

import logging

from slidegen.services.presentation.design_tokens import DesignTokens
from slidegen.services.presentation.recipes import LayoutRecipe
from slidegen.services.presentation.default_recipes import RECIPE_FACTORIES, title_body_recipe
from slidegen.services.presentation.semantic import SlideSpec, SlideKind

logger = logging.getLogger(__name__)


class PresetRecipeFallback:
    def select(self, spec: SlideSpec, tokens: DesignTokens) -> LayoutRecipe:
        n = len(spec.blocks)
        short_blocks = all(b.estimated_text_length < 200 for b in spec.blocks)
        kind = spec.kind

        if kind == SlideKind.COVER:
            return RECIPE_FACTORIES["CoverRecipe"](tokens)
        elif kind == SlideKind.AGENDA:
            return RECIPE_FACTORIES["AgendaRecipe"](tokens, n_blocks=n)
        elif kind == SlideKind.CLOSING:
            return RECIPE_FACTORIES["ClosingRecipe"](tokens)
        elif kind == SlideKind.COMPARISON:
            return RECIPE_FACTORIES["TwoColumnRecipe"](tokens, n_blocks=n)
        elif kind in (SlideKind.CONTENT_POINTS, SlideKind.PROCESS, SlideKind.TIMELINE):
            if n <= 2 and not short_blocks:
                return RECIPE_FACTORIES["TitleBodyRecipe"](tokens, n_blocks=n)
            elif n <= 6 and short_blocks:
                return RECIPE_FACTORIES["GridCardsRecipe"](tokens, n_blocks=n)
            else:
                return RECIPE_FACTORIES["TitleBodyRecipe"](tokens, n_blocks=n)
        elif kind == SlideKind.DATA_TABLE:
            return RECIPE_FACTORIES["TitleBodyRecipe"](tokens, n_blocks=n)
        else:
            logger.warning("No preset recipe for slide kind %s, falling back", kind)
            return RECIPE_FACTORIES["TitleBodyRecipe"](tokens, n_blocks=n)
