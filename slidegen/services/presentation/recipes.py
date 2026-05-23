from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType

from slidegen.services.presentation.region import Region, RegionRole, RepeatRule
from slidegen.services.presentation.semantic import BlockKind


def _freeze_dict(d: dict) -> MappingProxyType:
    return MappingProxyType(d)


@dataclass(frozen=True)
class LayoutRecipe:
    name: str
    regions: tuple[Region, ...]
    repeats: tuple[RepeatRule, ...] = ()
    region_roles: dict[str, RegionRole] = field(default_factory=dict)
    supported_block_kinds: frozenset[BlockKind] = field(default_factory=frozenset)
    region_block_indexes: dict[str, int] = field(default_factory=dict)
    region_text_sources: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, 'region_roles', _freeze_dict(self.region_roles))
        object.__setattr__(self, 'region_block_indexes', _freeze_dict(self.region_block_indexes))
        object.__setattr__(self, 'region_text_sources', _freeze_dict(self.region_text_sources))

    @property
    def region_ids(self) -> frozenset[str]:
        return frozenset(r.region_id for r in self.regions)

    def all_regions(self, block_count: int) -> tuple[Region, ...]:
        expanded: list[Region] = []
        for repeat_rule in self.repeats:
            expanded.extend(repeat_rule.expand(block_count))
        return self.regions + tuple(expanded)

    def role_for_region(self, region_id: str) -> RegionRole | None:
        role = self.region_roles.get(region_id)
        if role is not None:
            return role
        match = self._repeat_match(region_id)
        if match is None:
            return None
        repeat_rule, _repeat_index = match
        return repeat_rule.role

    def block_index_for_region(self, region_id: str) -> int | None:
        block_index = self.region_block_indexes.get(region_id)
        if block_index is not None:
            return block_index
        match = self._repeat_match(region_id)
        if match is None:
            return None
        repeat_rule, repeat_index = match
        seed_block_index = self.region_block_indexes.get(repeat_rule.seed.region_id)
        if seed_block_index is None:
            return repeat_index
        return seed_block_index + repeat_index

    def text_source_for_region(self, region_id: str) -> str | None:
        source = self.region_text_sources.get(region_id)
        if source is not None:
            return source
        match = self._repeat_match(region_id)
        if match is None:
            return None
        repeat_rule, _repeat_index = match
        return self.region_text_sources.get(repeat_rule.seed.region_id)

    def _repeat_match(self, region_id: str) -> tuple[RepeatRule, int] | None:
        for repeat_rule in self.repeats:
            prefix = f"{repeat_rule.seed.region_id}_"
            if not region_id.startswith(prefix):
                continue
            suffix = region_id[len(prefix):]
            if suffix.isdecimal():
                return repeat_rule, int(suffix)
        return None
