from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RegionRole(str, Enum):
    TITLE = "title"
    SUBTITLE = "subtitle"
    BODY = "body"
    CARD = "card"
    CARD_BODY = "card_body"
    INDEX = "index"
    ICON = "icon"
    IMAGE = "image"
    NOTE = "note"
    SOURCE = "source"
    FOOTER = "footer"
    DECORATION = "decoration"


@dataclass(frozen=True)
class Region:
    region_id: str
    x_frac: float
    y_frac: float
    w_frac: float
    h_frac: float
    z_layer: int = 10
    decoration_shape: str | None = None
    fill_role: str | None = None
    line_role: str | None = None
    opacity: float = 1.0

    def to_absolute(self, slide_w: float, slide_h: float) -> tuple[float, float, float, float]:
        return (
            round(self.x_frac * slide_w, 2),
            round(self.y_frac * slide_h, 2),
            round(self.w_frac * slide_w, 2),
            round(self.h_frac * slide_h, 2),
        )


@dataclass(frozen=True)
class RepeatRule:
    seed: Region
    step_x: float
    step_y: float
    role: RegionRole = RegionRole.CARD

    def expand(self, count: int) -> tuple[Region, ...]:
        return tuple(
            Region(
                region_id=f"{self.seed.region_id}_{i}",
                x_frac=self.seed.x_frac + self.step_x * i,
                y_frac=self.seed.y_frac + self.step_y * i,
                w_frac=self.seed.w_frac,
                h_frac=self.seed.h_frac,
                z_layer=self.seed.z_layer,
                decoration_shape=self.seed.decoration_shape,
                fill_role=self.seed.fill_role,
                line_role=self.seed.line_role,
                opacity=self.seed.opacity,
            )
            for i in range(count)
        )
