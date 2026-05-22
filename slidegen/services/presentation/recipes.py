from __future__ import annotations

from dataclasses import dataclass, field

from slidegen.services.presentation.region import Region, RegionRole, RepeatRule
from slidegen.services.presentation.semantic import BlockKind


@dataclass(frozen=True)
class LayoutRecipe:
    name: str
    regions: tuple[Region, ...]
    repeats: tuple[RepeatRule, ...] = ()
    region_roles: dict[str, RegionRole] = field(default_factory=dict)
    supported_block_kinds: frozenset[BlockKind] = field(default_factory=frozenset)
    region_block_indexes: dict[str, int] = field(default_factory=dict)
    region_text_sources: dict[str, str] = field(default_factory=dict)

    @property
    def region_ids(self) -> frozenset[str]:
        return frozenset(r.region_id for r in self.regions)

    def all_regions(self, block_count: int) -> tuple[Region, ...]:
        expanded: list[Region] = []
        for repeat_rule in self.repeats:
            expanded.extend(repeat_rule.expand(block_count))
        return self.regions + tuple(expanded)
