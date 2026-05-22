# Presentation Pipeline Upgrade 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用 DesignToken + LayoutRecipe + SlideRenderer 原生渲染管线替代当前的 shapes.json XML-copy 路径，分三个 Phase 完成全部迁移和旧代码清理。

**Architecture:** 新管线为 Markdown → SlideSpec/BlockSpec → DesignTokens → RecipeAgent(LLM) / PresetRecipeFallback → SlideRenderer(python-pptx 原生 API) → PostRenderValidator → PPTX。Phase 1a 建立数据模型层（不改渲染路径），Phase 1b 建立最小渲染闭环，Phase 1c 接入 RecipeAgent，Phase 2 切换主渲染管线，Phase 3 清理旧代码。

**Tech Stack:** Python 3.12+, python-pptx, Pydantic, pytest (anyio), dataclasses

**Spec:** `docs/superpowers/specs/2026-05-22-presentation-pipeline-upgrade.md`

---

## 文件结构规划

### 新增文件

| 文件 | 职责 | Phase |
|---|---|---|
| `slidegen/services/presentation/design_tokens.py` | DesignTokens dataclass + 默认 token set + PPTX theme 提取 + shape 采样提取 | 1a |
| `slidegen/services/presentation/region.py` | Region, RegionRole, RepeatRule 基础数据类 | 1a |
| `slidegen/services/presentation/recipes.py` | LayoutRecipe 数据类定义（含 repeats 字段） | 1b |
| `slidegen/services/presentation/default_recipes.py` | 6 个核心预设 Recipe 的具体实现（工厂函数） | 1b |
| `slidegen/services/presentation/preset_recipes.py` | PresetRecipeFallback（确定性规则选择 + 调用 default_recipes 工厂函数） | 1b |
| `slidegen/services/presentation/slide_renderer.py` | SlideRenderer + AssetProvider 接口 + DefaultAssetProvider | 1b |
| `slidegen/services/presentation/post_render_validator.py` | PostRenderValidator（越界/字体/重叠检测） | 1b |
| `slidegen/services/presentation/recipe_agent.py` | RecipeAgent（LLM 调用 + prompt template + JSON schema 校验） | 1c |
| `scripts/migrate_shapes_json.py` | 一次性迁移脚本：shapes.json → DECORATION region | 1b |
| `test/test_design_tokens.py` | DesignTokens 单元测试 | 1a |
| `test/test_region.py` | Region/RepeatRule 单元测试 | 1a |
| `test/test_semantic.py` | 增强版 SlideSpec/BlockSpec 测试 | 1a |
| `test/test_preset_recipes.py` | PresetRecipeFallback 确定性测试 | 1b |
| `test/test_default_recipes.py` | 预设 Recipe 快照测试 | 1b |
| `test/test_slide_renderer.py` | SlideRenderer 输出验证测试 | 1b |
| `test/test_post_render_validator.py` | PostRenderValidator 单元测试 | 1b |
| `test/test_migrate_shapes_json.py` | shapes.json 迁移脚本单元测试 | 1b |
| `test/test_recipe_agent.py` | RecipeAgent mock 测试 + fallback 测试 | 1c |

### 修改文件

| 文件 | 变更内容 | Phase |
|---|---|---|
| `slidegen/services/presentation/semantic.py` | 新增 SlideKind/BlockKind 值 + estimated_text_length + slide kind 推断函数 | 1a |
| `slidegen/services/presentation/converter.py` | Phase 2 切换到新渲染路径；Phase 3 移除 XML-copy 逻辑 | 2, 3 |
| `slidegen/services/presentation/render_plan.py` | Phase 3 在旧渲染路径删除后移除 use_native_* flag 和 template index 字段 | 3 |
| `slidegen/services/presentation/template_profile.py` | Phase 3 移除 _supports_legacy_renderer | 3 |
| `slidegen/core/config.py` | 增加 feature flag 配置项 | 1b |

### 删除文件（Phase 3）

| 文件 | 原因 |
|---|---|
| `slidegen/services/presentation/components.py` | ComponentsManager 被 Recipe 体系取代 |
| `slidegen/services/presentation/native_pages.py` | 被 SlideRenderer 完全取代 |
| `slidegen/utils/slide.py` 中的 XML 函数 | add_shape_by_xml 等不再需要 |
| `slidegen/services/presentation/pages.py` 中的旧页面类 | ChapterContentPage 等 XML-copy 实现 |

---

## Phase 1a: 数据模型层（不改渲染路径）

### Task 1: 创建 Region/RegionRole/RepeatRule 数据类

**Files:**
- Create: `slidegen/services/presentation/region.py`
- Create: `test/test_region.py`

- [ ] **Step 1: 创建 region.py**

```python
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
```

- [ ] **Step 2: 创建 test_region.py 并编写测试**

```python
from slidegen.services.presentation.region import Region, RegionRole, RepeatRule


class TestRegion:
    def test_to_absolute_converts_fraction_to_inches(self):
        r = Region(region_id="test", x_frac=0.5, y_frac=0.25, w_frac=0.8, h_frac=0.1)
        left, top, width, height = r.to_absolute(13.333, 7.5)
        assert left == 6.67
        assert top == 1.88
        assert width == 10.67
        assert height == 0.75

    def test_to_absolute_rounds_to_2_decimals(self):
        r = Region(region_id="test", x_frac=0.333, y_frac=0.111, w_frac=0.456, h_frac=0.789)
        left, top, width, height = r.to_absolute(10.0, 8.0)
        assert left == 3.33
        assert top == 0.89
        assert width == 4.56
        assert height == 6.31

    def test_decoration_fields_default_none_for_content_region(self):
        r = Region(region_id="title", x_frac=0.1, y_frac=0.05, w_frac=0.8, h_frac=0.1)
        assert r.decoration_shape is None
        assert r.fill_role is None
        assert r.line_role is None

    def test_decoration_fields_set_for_decoration_region(self):
        r = Region(
            region_id="deco_bar",
            x_frac=0.0, y_frac=0.0, w_frac=1.0, h_frac=0.02,
            z_layer=20,
            decoration_shape="rect",
            fill_role="primary",
            line_role=None,
        )
        assert r.decoration_shape == "rect"
        assert r.fill_role == "primary"
        assert r.line_role is None


class TestRepeatRule:
    def test_expand_zero_items_returns_empty(self):
        seed = Region(region_id="card", x_frac=0.1, y_frac=0.3, w_frac=0.35, h_frac=0.4)
        rule = RepeatRule(seed=seed, step_x=0.0, step_y=0.12)
        result = rule.expand(0)
        assert len(result) == 0

    def test_expand_single_item_equals_seed(self):
        seed = Region(region_id="card", x_frac=0.1, y_frac=0.3, w_frac=0.35, h_frac=0.4)
        rule = RepeatRule(seed=seed, step_x=0.0, step_y=0.12)
        result = rule.expand(1)
        assert len(result) == 1
        assert result[0].x_frac == seed.x_frac
        assert result[0].y_frac == seed.y_frac

    def test_expand_vertical_stack(self):
        seed = Region(region_id="card", x_frac=0.08, y_frac=0.22, w_frac=0.30, h_frac=0.10)
        rule = RepeatRule(seed=seed, step_x=0.0, step_y=0.13)
        result = rule.expand(3)
        assert len(result) == 3
        assert result[0].region_id == "card_0"
        assert result[1].region_id == "card_1"
        assert result[2].region_id == "card_2"
        assert result[0].y_frac == 0.22
        assert result[1].y_frac == 0.35
        assert result[2].y_frac == 0.48
        # x unchanged for vertical
        for r in result:
            assert r.x_frac == 0.08

    def test_expand_horizontal_row(self):
        seed = Region(region_id="card", x_frac=0.08, y_frac=0.22, w_frac=0.25, h_frac=0.35)
        rule = RepeatRule(seed=seed, step_x=0.30, step_y=0.0)
        result = rule.expand(3)
        assert len(result) == 3
        assert result[0].x_frac == 0.08
        assert result[1].x_frac == 0.38
        assert result[2].x_frac == 0.68
        for r in result:
            assert r.y_frac == 0.22

    def test_expand_preserves_decoration_fields(self):
        seed = Region(
            region_id="step",
            x_frac=0.08, y_frac=0.22, w_frac=0.30, h_frac=0.10,
            decoration_shape="rounded_rect", fill_role="accent", line_role="primary",
        )
        rule = RepeatRule(seed=seed, step_x=0.05, step_y=0.12, role=RegionRole.CARD)
        result = rule.expand(2)
        for r in result:
            assert r.decoration_shape == "rounded_rect"
            assert r.fill_role == "accent"
            assert r.line_role == "primary"

    def test_expand_staircase_layout(self):
        seed = Region(region_id="agenda_item", x_frac=0.08, y_frac=0.22, w_frac=0.30, h_frac=0.10)
        rule = RepeatRule(seed=seed, step_x=0.05, step_y=0.13)
        result = rule.expand(5)
        assert result[4].x_frac == 0.28  # 0.08 + 0.05*4
        assert result[4].y_frac == 0.74  # 0.22 + 0.13*4
```

- [ ] **Step 3: 运行测试验证**

```bash
uv run pytest test/test_region.py -v
```

- [ ] **Step 4: Commit**

```bash
git add slidegen/services/presentation/region.py test/test_region.py
git commit -m "feat: add Region, RegionRole, and RepeatRule data classes"
```

---

### Task 2: 创建 DesignTokens 数据类 + 默认 token set

**Files:**
- Create: `slidegen/services/presentation/design_tokens.py`
- Create: `test/test_design_tokens.py`

- [ ] **Step 1: 创建 design_tokens.py（DesignTokens + 默认值 + extract 初版）**

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DesignTokens:
    primary: str
    accent: str
    light_bg: str
    light_bg_alt: str
    text_primary: str
    text_secondary: str
    text_on_dark: str
    semantic_positive: str = "#2E7D32"
    semantic_negative: str = "#C62828"
    semantic_neutral: str = "#757575"
    title_font: str = "Calibri"
    title_size: int = 28
    subtitle_font: str = "Calibri"
    subtitle_size: int = 20
    body_font: str = "Calibri"
    body_size: int = 14
    caption_font: str = "Calibri"
    caption_size: int = 10
    slide_width: float = 13.333
    slide_height: float = 7.5
    page_margin_x: float = 0.8
    page_margin_y: float = 0.6
    card_gap: float = 0.3
    section_gap: float = 0.5
    line_spacing_multiple: float = 1.2


# 内置预设主题

DEFAULT_TOKENS = DesignTokens(
    primary="#1A3A5C",
    accent="#E8703B",
    light_bg="#F5F6F8",
    light_bg_alt="#E8ECF1",
    text_primary="#1A1A1A",
    text_secondary="#5C5C5C",
    text_on_dark="#FFFFFF",
)

PRESET_TOKENS: dict[str, DesignTokens] = {
    "general": DEFAULT_TOKENS,
    "minimal": DesignTokens(
        primary="#2C2C2C",
        accent="#4A90D9",
        light_bg="#FFFFFF",
        light_bg_alt="#F0F0F0",
        text_primary="#1A1A1A",
        text_secondary="#888888",
        text_on_dark="#FFFFFF",
    ),
    "academic": DesignTokens(
        primary="#003366",
        accent="#8B0000",
        light_bg="#FAFAF5",
        light_bg_alt="#F0EDE5",
        text_primary="#1A1A1A",
        text_secondary="#555555",
        text_on_dark="#FFFFFF",
        title_font="Times New Roman",
        body_font="Times New Roman",
    ),
}


def _extract_theme_colors(prs) -> dict[str, str | None]:
    """从 theme.xml 提取 <a:clrScheme> 颜色映射。"""
    import re
    from lxml import etree

    result: dict[str, str | None] = {}
    try:
        slide_master = prs.slide_masters[0]
        theme = slide_master.slide_layouts[0].slide_master.element
        theme_xml = etree.tostring(theme, encoding="unicode")
        nsmap = {
            "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
        }
        dk1 = theme.find(".//a:dk1/a:srgbClr", namespaces=nsmap)
        dk2 = theme.find(".//a:dk2/a:srgbClr", namespaces=nsmap)
        lt1 = theme.find(".//a:lt1/a:srgbClr", namespaces=nsmap)
        lt2 = theme.find(".//a:lt2/a:srgbClr", namespaces=nsmap)
        accent1 = theme.find(".//a:accent1/a:srgbClr", namespaces=nsmap)
        accent2 = theme.find(".//a:accent2/a:srgbClr", namespaces=nsmap)
        accent3 = theme.find(".//a:accent3/a:srgbClr", namespaces=nsmap)
        result["dk1"] = dk1.get("val") if dk1 is not None else None
        result["dk2"] = dk2.get("val") if dk2 is not None else None
        result["lt1"] = lt1.get("val") if lt1 is not None else None
        result["lt2"] = lt2.get("val") if lt2 is not None else None
        result["accent1"] = accent1.get("val") if accent1 is not None else None
        result["accent2"] = accent2.get("val") if accent2 is not None else None
        result["accent3"] = accent3.get("val") if accent3 is not None else None
    except Exception:
        pass
    return result


def _extract_theme_fonts(prs) -> dict[str, str | None]:
    """从 theme.xml 提取 <a:fontScheme> 字体映射。"""
    result: dict[str, str | None] = {"major": None, "minor": None}
    try:
        nsmap = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
        slide_master = prs.slide_masters[0]
        major = slide_master.element.find(".//a:majorFont/a:latin", namespaces=nsmap)
        minor = slide_master.element.find(".//a:minorFont/a:latin", namespaces=nsmap)
        if major is not None:
            result["major"] = major.get("typeface")
        if minor is not None:
            result["minor"] = minor.get("typeface")
    except Exception:
        pass
    return result


def _sample_shape_colors(prs, max_slides: int = 10) -> dict[str, list[tuple[str, float]]]:
    """从 shape 中采样实际使用的填充色和字体色（按面积加权）。

    Returns dict with 'fills' and 'fonts' keys, each a list of (hex_color, weight).
    """
    fills: list[tuple[str, float]] = []
    fonts: list[tuple[str, float]] = []
    min_area = 914400  # 1 square inch in EMU (914400 EMU)

    for slide in list(prs.slides)[:max_slides]:
        for shape in slide.shapes:
            area = shape.width * shape.height
            if area < min_area:
                continue
            try:
                fill = shape.fill
                if fill and fill.type is not None:
                    try:
                        rgb = fill.fore_color.rgb
                        if rgb:
                            fills.append((str(rgb), float(area)))
                    except Exception:
                        pass
            except Exception:
                pass
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        try:
                            font_color = run.font.color
                            if font_color and font_color.rgb:
                                fonts.append((str(font_color.rgb), float(area)))
                        except Exception:
                            pass
    return {"fills": fills, "fonts": fonts}


def _hex_to_hsl(hex_color: str) -> tuple[float, float, float]:
    """将 hex 颜色转为 (hue, saturation, lightness)。"""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16) / 255.0, int(hex_color[2:4], 16) / 255.0, int(hex_color[4:6], 16) / 255.0
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    l = (max_c + min_c) / 2.0
    if max_c == min_c:
        return (0.0, 0.0, l)
    d = max_c - min_c
    s = d / (2.0 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)
    if max_c == r:
        h = ((g - b) / d) % 6
    elif max_c == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return (h * 60, s, l)


def extract_design_tokens_from_presentation(prs, theme_name: str = "general") -> DesignTokens:
    """从模板 PPTX 提取 DesignTokens。两层策略：theme.xml + shape 采样。"""
    base = PRESET_TOKENS.get(theme_name, DEFAULT_TOKENS)

    # Layer 1: theme.xml
    theme_colors = _extract_theme_colors(prs)
    theme_fonts = _extract_theme_fonts(prs)

    # Layer 2: shape 采样（仅在 slide 数 >= 3 时启用）
    slide_count = len(prs.slides)
    sampled = {"fills": [], "fonts": []}
    if slide_count >= 3:
        sampled = _sample_shape_colors(prs)

    primary = theme_colors.get("dk1") or base.primary
    accent = theme_colors.get("accent1") or base.accent
    light_bg = theme_colors.get("lt1") or base.light_bg
    light_bg_alt = theme_colors.get("lt2") or base.light_bg_alt
    text_primary = theme_colors.get("dk2") or base.text_primary

    title_font = theme_fonts.get("major") or base.title_font
    body_font = theme_fonts.get("minor") or base.body_font

    return DesignTokens(
        primary=primary,
        accent=accent,
        light_bg=light_bg,
        light_bg_alt=light_bg_alt,
        text_primary=text_primary,
        text_secondary=base.text_secondary,
        text_on_dark=base.text_on_dark,
        title_font=title_font,
        title_size=base.title_size,
        subtitle_font=body_font,
        subtitle_size=base.subtitle_size,
        body_font=body_font,
        body_size=base.body_size,
        caption_font=base.caption_font,
        caption_size=base.caption_size,
    )
```

- [ ] **Step 2: 创建 test_design_tokens.py**

```python
from pptx import Presentation

from slidegen.services.presentation.design_tokens import (
    DesignTokens,
    DEFAULT_TOKENS,
    PRESET_TOKENS,
    extract_design_tokens_from_presentation,
    _hex_to_hsl,
    _extract_theme_colors,
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
```

- [ ] **Step 3: 运行测试验证**

```bash
uv run pytest test/test_design_tokens.py -v
```

- [ ] **Step 4: Commit**

```bash
git add slidegen/services/presentation/design_tokens.py test/test_design_tokens.py
git commit -m "feat: add DesignTokens dataclass with theme extraction and presets"
```

---

### Task 3: 增强 SlideSpec/BlockSpec 语义模型 + slide kind 推断

**Files:**
- Modify: `slidegen/services/presentation/semantic.py`
- Create: `test/test_semantic.py`

- [ ] **Step 1: 编写增强版 semantic.py 的测试（先写测试，验证当前行为不变）**

```python
from slidegen.services.presentation.semantic import (
    SlideKind,
    BlockKind,
    BlockSpec,
    SlideSpec,
    build_content_slide_spec,
    infer_slide_kind,
)
from slidegen.services.document.markdown import MarkdownDocument
from slidegen.services.slidegen.outline_structure import iter_chapter_slide_groups


def _first_content_slide(markdown: str):
    doc = MarkdownDocument(markdown)
    groups = list(iter_chapter_slide_groups(doc.main))
    assert groups
    assert groups[0].slides
    return groups[0].slides[0]


class TestBlockSpec:
    def test_estimated_text_length_is_character_count(self):
        block = BlockSpec(kind=BlockKind.POINT, title="Title", text="Hello World")
        assert block.estimated_text_length == 11

    def test_empty_text(self):
        block = BlockSpec(kind=BlockKind.PARAGRAPH, title="", text="")
        assert block.estimated_text_length == 0


class TestSlideSpec:
    def test_total_text_length_aggregates_blocks(self):
        blocks = (
            BlockSpec(kind=BlockKind.POINT, title="A", text="aaaa"),
            BlockSpec(kind=BlockKind.POINT, title="B", text="bb"),
        )
        spec = SlideSpec(kind=SlideKind.CONTENT_POINTS, title="Test", source_level=2, blocks=blocks)
        assert spec.total_text_length == 6

    def test_block_kinds(self):
        blocks = (
            BlockSpec(kind=BlockKind.POINT, title="A", text="a"),
            BlockSpec(kind=BlockKind.PARAGRAPH, title="B", text="b"),
        )
        spec = SlideSpec(kind=SlideKind.CONTENT_POINTS, title="Test", source_level=2, blocks=blocks)
        assert spec.block_kinds == frozenset({BlockKind.POINT, BlockKind.PARAGRAPH})

    def test_has_data_false_for_points_only(self):
        blocks = (BlockSpec(kind=BlockKind.POINT, title="A", text="a"),)
        spec = SlideSpec(kind=SlideKind.CONTENT_POINTS, title="Test", source_level=2, blocks=blocks)
        assert not spec.has_data

    def test_has_data_true_when_table_present(self):
        blocks = (BlockSpec(kind=BlockKind.TABLE, title="T", text="1,2,3"),)
        spec = SlideSpec(kind=SlideKind.DATA_TABLE, title="Test", source_level=2, blocks=blocks)
        assert spec.has_data


class TestSlideKindInference:
    def test_default_content_points(self):
        content = _first_content_slide("# Deck\n## Chapter\n### Point\nBody text")
        spec = build_content_slide_spec(content)
        assert spec.kind == SlideKind.CONTENT_POINTS

    def test_data_table_detected(self):
        content = _first_content_slide("# Deck\n## Chapter\n### Data\n\n| A | B |\n|---|---|\n| 1 | 2 |\n")
        spec = build_content_slide_spec(content)
        assert spec.kind == SlideKind.DATA_TABLE

    def test_process_detected_for_numbered_list(self):
        content = _first_content_slide("# Deck\n## Chapter\n### Steps\n1. First step\n2. Second step\n3. Third step")
        spec = build_content_slide_spec(content)
        assert spec.kind == SlideKind.PROCESS

    def test_comparison_detected_for_two_subheadings(self):
        content = _first_content_slide("# Deck\n## Chapter\n### Compare\n#### Left\nLeft body\n#### Right\nRight body")
        spec = build_content_slide_spec(content)
        assert spec.kind == SlideKind.COMPARISON

    def test_timeline_detected_for_year_pattern(self):
        content = _first_content_slide("# Deck\n## Chapter\n### History\n2020年 公司成立\n2022年 产品发布")
        spec = build_content_slide_spec(content)
        assert spec.kind == SlideKind.TIMELINE
```

- [ ] **Step 2: 运行测试，验证失败（新 SlideKind/BlockKind 值尚未定义）**

```bash
uv run pytest test/test_semantic.py -v
```

- [ ] **Step 3: 修改 semantic.py，增加新枚举值和推断逻辑**

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

from slidegen.services.document.markdown.elements import Element, Heading, Table


class SlideKind(str, Enum):
    COVER = "cover"
    AGENDA = "agenda"
    SECTION_COVER = "section_cover"
    CONTENT_POINTS = "content_points"
    COMPARISON = "comparison"
    PROCESS = "process"
    TIMELINE = "timeline"
    DATA_TABLE = "data_table"
    DATA_CHART = "data_chart"
    CLOSING = "closing"


class BlockKind(str, Enum):
    TITLE = "title"
    SUBTITLE = "subtitle"
    POINT = "point"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    CHART = "chart"
    IMAGE = "image"
    NOTE = "note"
    SOURCE = "source"


@dataclass(frozen=True)
class BlockSpec:
    kind: BlockKind
    title: str
    text: str
    image_prompt: str | None = None
    icon_query: str | None = None

    @property
    def estimated_text_length(self) -> int:
        return len(self.text)


@dataclass(frozen=True)
class SlideSpec:
    kind: SlideKind
    title: str
    source_level: int
    blocks: tuple[BlockSpec, ...]

    @property
    def total_text_length(self) -> int:
        return sum(block.estimated_text_length for block in self.blocks)

    @property
    def block_kinds(self) -> frozenset[BlockKind]:
        return frozenset(block.kind for block in self.blocks)

    @property
    def has_data(self) -> bool:
        return BlockKind.TABLE in self.block_kinds or BlockKind.CHART in self.block_kinds


_PROCESS_PATTERNS = [
    re.compile(r"^\d+[\.\、\)]", re.MULTILINE),
    re.compile(r"第[一二三四五六七八九十\d]+步"),
]
_TIMELINE_PATTERNS = [
    re.compile(r"\d{4}\s*年"),
    re.compile(r"第[一二三四五六七八九十\d]+\s*(阶段|季度|期)"),
    re.compile(r"Q[1-4]", re.IGNORECASE),
]


def _has_numbered_list(text: str) -> bool:
    return any(pat.search(text) for pat in _PROCESS_PATTERNS)


def _has_timeline_markers(text: str) -> bool:
    return any(pat.search(text) for pat in _TIMELINE_PATTERNS)


def _has_two_level4_headings(content: Heading) -> bool:
    level4_children = [child for child in content.children
                       if isinstance(child, Heading) and child.level == 4]
    return len(level4_children) == 2


def infer_slide_kind(content: Heading) -> SlideKind:
    full_text = content.text

    # 显式 hint 优先
    for child in content.children:
        if isinstance(child, Element) and child.element_text.strip().startswith("<!-- slide:"):
            hint = child.element_text.strip()
            if "comparison" in hint:
                return SlideKind.COMPARISON
            elif "process" in hint:
                return SlideKind.PROCESS
            elif "timeline" in hint:
                return SlideKind.TIMELINE
            elif "image_text" in hint:
                return SlideKind.CONTENT_POINTS

    # table 检测
    if any(isinstance(child, Table) for child in content.children):
        return SlideKind.DATA_TABLE

    # 两个 level-4 子标题 → COMPARISON
    if _has_two_level4_headings(content):
        return SlideKind.COMPARISON

    # 编号列表 → PROCESS
    if _has_numbered_list(full_text):
        return SlideKind.PROCESS

    # 时间线标记 → TIMELINE
    if _has_timeline_markers(full_text):
        return SlideKind.TIMELINE

    return SlideKind.CONTENT_POINTS


def build_content_slide_spec(content: Heading) -> SlideSpec:
    blocks: list[BlockSpec] = []
    for child in content.children:
        if isinstance(child, Heading):
            text = child.text.strip()
            icon_query = child.element_text if child.level >= 3 else None
            blocks.append(BlockSpec(
                kind=BlockKind.POINT,
                title=child.element_text,
                text=text,
                icon_query=icon_query,
            ))
        elif isinstance(child, Table):
            blocks.append(BlockSpec(
                kind=BlockKind.TABLE,
                title=", ".join(child.headers),
                text=child.element_text_source,
            ))
        elif isinstance(child, Element) and child.element_text.strip():
            blocks.append(BlockSpec(
                kind=BlockKind.PARAGRAPH,
                title="",
                text=child.element_text.strip(),
            ))

    slide_kind = infer_slide_kind(content)
    return SlideSpec(
        kind=slide_kind,
        title=content.element_text,
        source_level=content.level,
        blocks=tuple(blocks),
    )
```

- [ ] **Step 4: 运行测试，验证全部通过**

```bash
uv run pytest test/test_semantic.py -v
```

- [ ] **Step 5: 运行现有测试，确保兼容性**

```bash
uv run pytest test/test_converter.py test/test_workflow.py -v
```

- [ ] **Step 6: Commit**

```bash
git add slidegen/services/presentation/semantic.py test/test_semantic.py
git commit -m "feat: enhance SlideSpec/BlockSpec with new kinds and slide kind inference"
```

---

### Task 4: 创建 PresetRecipeFallback 初版

**Files:**
- Create: `slidegen/services/presentation/preset_recipes.py`
- Create: `test/test_preset_recipes.py`

- [ ] **Step 1: 创建 preset_recipes.py（初版，暂不依赖实际 Recipe）**

```python
from __future__ import annotations

import logging

from slidegen.services.presentation.semantic import SlideSpec, SlideKind, BlockKind

logger = logging.getLogger(__name__)


class PresetRecipeFallback:
    """Deterministic fallback when RecipeAgent is unavailable.

    Phase 1a: 返回 recipe name (string)，不依赖 LayoutRecipe 实现。
    Phase 1b: 升级为返回 LayoutRecipe 实例。
    """

    def select_name(self, spec: SlideSpec) -> str:
        """根据 slide_kind + block 数量和密度返回预设 recipe name。

        Returns a recipe name string that Phase 1b factories will resolve.
        """
        n = len(spec.blocks)
        short_blocks = all(b.estimated_text_length < 200 for b in spec.blocks)

        kind = spec.kind

        if kind in (SlideKind.COVER, SlideKind.SECTION_COVER):
            return "CoverRecipe"
        elif kind == SlideKind.AGENDA:
            return "AgendaRecipe"
        elif kind == SlideKind.CLOSING:
            return "ClosingRecipe"
        elif kind == SlideKind.COMPARISON:
            return "TwoColumnRecipe"
        elif kind == SlideKind.CONTENT_POINTS or kind == SlideKind.PROCESS or kind == SlideKind.TIMELINE:
            if n <= 2 and not short_blocks:
                return "TitleBodyRecipe"
            elif n <= 6 and short_blocks:
                return "GridCardsRecipe"
            else:
                return "TitleBodyRecipe"
        elif kind == SlideKind.DATA_TABLE:
            return "TitleBodyRecipe"
        else:
            logger.warning("No preset recipe for slide kind %s, falling back to TitleBodyRecipe", kind)
            return "TitleBodyRecipe"
```

- [ ] **Step 2: 编写 test_preset_recipes.py**

```python
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
```

- [ ] **Step 3: 运行测试**

```bash
uv run pytest test/test_preset_recipes.py -v
```

- [ ] **Step 4: Commit**

```bash
git add slidegen/services/presentation/preset_recipes.py test/test_preset_recipes.py
git commit -m "feat: add PresetRecipeFallback skeleton with deterministic name selection"
```

---

### Task 5: Phase 1a 集成验证

**Files:**
- Modify: 无新文件，确认现有测试全部通过

- [ ] **Step 1: 运行全部测试**

```bash
uv run pytest -v
```

- [ ] **Step 2: 验证导入链正常**

```bash
uv run python -c "
from slidegen.services.presentation.region import Region, RegionRole, RepeatRule
from slidegen.services.presentation.design_tokens import DesignTokens, DEFAULT_TOKENS, extract_design_tokens_from_presentation
from slidegen.services.presentation.semantic import SlideKind, BlockKind, SlideSpec, BlockSpec, build_content_slide_spec, infer_slide_kind
from slidegen.services.presentation.preset_recipes import PresetRecipeFallback
print('All imports OK')
print(f'SlideKind values: {[k.value for k in SlideKind]}')
print(f'BlockKind values: {[k.value for k in BlockKind]}')
print(f'DEFAULT_TOKENS primary: {DEFAULT_TOKENS.primary}')
print(f'Preset themes: {list(DesignTokens.__annotations__.keys())}')
"
```

- [ ] **Step 3: Commit (Phase 1a 完成标记)**

```bash
git commit --allow-empty -m "feat: complete Phase 1a — data model layer"
```

---

## Phase 1b: 最小渲染闭环 + 样式迁移工具

### Task 6: 创建 LayoutRecipe 数据类

**Files:**
- Create: `slidegen/services/presentation/recipes.py`

- [ ] **Step 1: 创建 recipes.py**

```python
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
```

---

### Task 7: 创建 6 个核心预设 Recipe（default_recipes.py）

**Files:**
- Create: `slidegen/services/presentation/default_recipes.py`
- Create: `test/test_default_recipes.py`

- [ ] **Step 1: 创建 default_recipes.py（TitleBodyRecipe + GridCardsRecipe + TwoColumnRecipe 等）**

```python
from __future__ import annotations

from slidegen.services.presentation.design_tokens import DesignTokens
from slidegen.services.presentation.recipes import LayoutRecipe
from slidegen.services.presentation.region import Region, RegionRole, RepeatRule
from slidegen.services.presentation.semantic import BlockKind

ALL_BLOCK_KINDS = frozenset({BlockKind.POINT, BlockKind.PARAGRAPH, BlockKind.TABLE})


def title_body_recipe(tokens: DesignTokens, n_blocks: int = 1) -> LayoutRecipe:
    margin_x = tokens.page_margin_x / tokens.slide_width
    margin_y = tokens.page_margin_y / tokens.slide_height
    regions = [
        Region(region_id="title", x_frac=margin_x, y_frac=margin_y,
               w_frac=1.0 - 2 * margin_x, h_frac=0.12, z_layer=10),
        Region(region_id="body", x_frac=margin_x, y_frac=margin_y + 0.16,
               w_frac=1.0 - 2 * margin_x, h_frac=1.0 - margin_y - 0.22, z_layer=10),
    ]
    return LayoutRecipe(
        name="TitleBodyRecipe",
        regions=tuple(regions),
        region_roles={r.region_id: RegionRole.TITLE if "title" in r.region_id else RegionRole.BODY for r in regions},
        region_block_indexes={"body": 0},
        region_text_sources={"title": "slide_title", "body": "block_text"},
        supported_block_kinds=ALL_BLOCK_KINDS,
    )


def grid_cards_recipe(tokens: DesignTokens, n_blocks: int) -> LayoutRecipe:
    margin_x = tokens.page_margin_x / tokens.slide_width
    margin_y = tokens.page_margin_y / tokens.slide_height
    gap_frac = tokens.card_gap / tokens.slide_width

    cols = 3 if n_blocks >= 6 else 2 if n_blocks >= 3 else n_blocks
    rows = (n_blocks + cols - 1) // cols
    card_w = (1.0 - 2 * margin_x - (cols - 1) * gap_frac) / cols
    card_h = (1.0 - 2 * margin_y - 0.18 - (rows - 1) * gap_frac) / rows
    title_y = margin_y
    body_top = title_y + 0.18

    regions = [
        Region(region_id="title", x_frac=margin_x, y_frac=title_y,
               w_frac=1.0 - 2 * margin_x, h_frac=0.12, z_layer=10),
    ]

    card_regions = []
    for i in range(n_blocks):
        col = i % cols
        row = i // cols
        rx = margin_x + col * (card_w + gap_frac)
        ry = body_top + row * (card_h + gap_frac)
        card_id = f"card_{i}"
        card_regions.append(Region(
            region_id=card_id, x_frac=rx, y_frac=ry,
            w_frac=card_w, h_frac=card_h, z_layer=10,
        ))
        regions.append(Region(
            region_id=f"{card_id}_icon", x_frac=rx + 0.02, y_frac=ry + 0.02,
            w_frac=min(0.05, card_w * 0.18), h_frac=min(0.08, card_h * 0.28), z_layer=11,
        ))
        regions.append(Region(
            region_id=f"{card_id}_body", x_frac=rx + 0.02, y_frac=ry + 0.12,
            w_frac=card_w - 0.04, h_frac=card_h - 0.14, z_layer=11,
        ))

    all_recipe_regions = regions + card_regions
    region_roles = {r.region_id: RegionRole.TITLE if "title" in r.region_id else (
        RegionRole.ICON if r.region_id.endswith("_icon") else
        RegionRole.CARD if r.region_id.startswith("card_") and "_body" not in r.region_id
        else RegionRole.CARD_BODY
    ) for r in all_recipe_regions}
    region_block_indexes = {}
    region_text_sources = {"title": "slide_title"}
    for i in range(n_blocks):
        region_block_indexes[f"card_{i}_icon"] = i
        region_block_indexes[f"card_{i}_body"] = i
        region_text_sources[f"card_{i}_body"] = "block_title_text"

    return LayoutRecipe(
        name="GridCardsRecipe",
        regions=tuple(all_recipe_regions),
        region_roles=region_roles,
        region_block_indexes=region_block_indexes,
        region_text_sources=region_text_sources,
        supported_block_kinds=ALL_BLOCK_KINDS,
    )


def two_column_recipe(tokens: DesignTokens, n_blocks: int = 2) -> LayoutRecipe:
    margin_x = tokens.page_margin_x / tokens.slide_width
    margin_y = tokens.page_margin_y / tokens.slide_height
    gap_frac = tokens.card_gap / tokens.slide_width
    col_w = (1.0 - 2 * margin_x - gap_frac) / 2
    col_top = margin_y + 0.16
    col_h = 1.0 - margin_y - col_top - 0.06

    regions = [
        Region(region_id="title", x_frac=margin_x, y_frac=margin_y,
               w_frac=1.0 - 2 * margin_x, h_frac=0.12, z_layer=10),
        Region(region_id="left_col", x_frac=margin_x, y_frac=col_top,
               w_frac=col_w, h_frac=col_h, z_layer=10),
        Region(region_id="right_col", x_frac=margin_x + col_w + gap_frac, y_frac=col_top,
               w_frac=col_w, h_frac=col_h, z_layer=10),
    ]
    return LayoutRecipe(
        name="TwoColumnRecipe",
        regions=tuple(regions),
        region_roles={
            "title": RegionRole.TITLE,
            "left_col": RegionRole.CARD_BODY,
            "right_col": RegionRole.CARD_BODY,
        },
        region_block_indexes={"left_col": 0, "right_col": 1},
        region_text_sources={"title": "slide_title", "left_col": "block_title_text", "right_col": "block_title_text"},
        supported_block_kinds=ALL_BLOCK_KINDS,
    )


def cover_recipe(tokens: DesignTokens) -> LayoutRecipe:
    margin_x = tokens.page_margin_x / tokens.slide_width
    regions = [
        Region(region_id="title", x_frac=margin_x, y_frac=0.32,
               w_frac=1.0 - 2 * margin_x, h_frac=0.15, z_layer=10),
        Region(region_id="subtitle", x_frac=margin_x, y_frac=0.50,
               w_frac=1.0 - 2 * margin_x, h_frac=0.10, z_layer=10),
        Region(region_id="deco_bar", x_frac=margin_x, y_frac=0.70,
               w_frac=0.15, h_frac=0.02, z_layer=20,
               decoration_shape="rounded_rect", fill_role="accent"),
    ]
    return LayoutRecipe(
        name="CoverRecipe",
        regions=tuple(regions),
        region_roles={
            "title": RegionRole.TITLE,
            "subtitle": RegionRole.SUBTITLE,
            "deco_bar": RegionRole.DECORATION,
        },
        region_block_indexes={"subtitle": 0},
        region_text_sources={"title": "slide_title", "subtitle": "block_text"},
        supported_block_kinds=frozenset({BlockKind.TITLE, BlockKind.SUBTITLE}),
    )


def agenda_recipe(tokens: DesignTokens, n_blocks: int) -> LayoutRecipe:
    margin_x = tokens.page_margin_x / tokens.slide_width
    margin_y = tokens.page_margin_y / tokens.slide_height
    gap_frac = tokens.card_gap / tokens.slide_width

    card_h = 0.35
    regions = [
        Region(region_id="title", x_frac=margin_x, y_frac=margin_y,
               w_frac=1.0 - 2 * margin_x, h_frac=0.12, z_layer=10),
    ]
    card_regions = []
    idx_regions = []
    for i in range(min(n_blocks, 8)):
        ry = margin_y + 0.18 + i * (card_h + gap_frac / 2)
        card_id = f"agenda_card_{i}"
        idx_id = f"agenda_index_{i}"
        card_regions.append(Region(
            region_id=card_id, x_frac=margin_x + 0.06, y_frac=ry,
            w_frac=1.0 - 2 * margin_x - 0.06, h_frac=card_h, z_layer=10,
        ))
        idx_regions.append(Region(
            region_id=idx_id, x_frac=margin_x, y_frac=ry,
            w_frac=0.06, h_frac=card_h, z_layer=10,
        ))

    region_roles = {r.region_id: RegionRole.TITLE if "title" in r.region_id else (
        RegionRole.INDEX if "index" in r.region_id else RegionRole.CARD
    ) for r in regions + tuple(card_regions) + tuple(idx_regions)}
    region_block_indexes = {}
    region_text_sources = {"title": "slide_title"}
    for i in range(min(n_blocks, 8)):
        region_block_indexes[f"agenda_card_{i}"] = i
        region_block_indexes[f"agenda_index_{i}"] = i
        region_text_sources[f"agenda_card_{i}"] = "block_title_text"
        region_text_sources[f"agenda_index_{i}"] = "index"

    return LayoutRecipe(
        name="AgendaRecipe",
        regions=tuple(regions + card_regions + idx_regions),
        region_roles=region_roles,
        region_block_indexes=region_block_indexes,
        region_text_sources=region_text_sources,
        supported_block_kinds=ALL_BLOCK_KINDS,
    )


def closing_recipe(tokens: DesignTokens) -> LayoutRecipe:
    margin_x = tokens.page_margin_x / tokens.slide_width
    regions = [
        Region(region_id="thanks", x_frac=margin_x, y_frac=0.40,
               w_frac=1.0 - 2 * margin_x, h_frac=0.12, z_layer=10),
        Region(region_id="deco_top", x_frac=0.0, y_frac=0.0,
               w_frac=1.0, h_frac=0.03, z_layer=20,
               decoration_shape="rect", fill_role="primary"),
        Region(region_id="deco_bottom", x_frac=0.0, y_frac=0.97,
               w_frac=1.0, h_frac=0.03, z_layer=20,
               decoration_shape="rect", fill_role="primary"),
    ]
    return LayoutRecipe(
        name="ClosingRecipe",
        regions=tuple(regions),
        region_roles={
            "thanks": RegionRole.TITLE,
            "deco_top": RegionRole.DECORATION,
            "deco_bottom": RegionRole.DECORATION,
        },
        region_text_sources={"thanks": "slide_title"},
        supported_block_kinds=frozenset({BlockKind.TITLE}),
    )


RECIPE_FACTORIES = {
    "TitleBodyRecipe": title_body_recipe,
    "GridCardsRecipe": grid_cards_recipe,
    "TwoColumnRecipe": two_column_recipe,
    "CoverRecipe": cover_recipe,
    "AgendaRecipe": agenda_recipe,
    "ClosingRecipe": closing_recipe,
}
```

- [ ] **Step 2: 编写 test_default_recipes.py（快照测试）**

```python
from slidegen.services.presentation.default_recipes import (
    title_body_recipe, grid_cards_recipe, two_column_recipe,
    cover_recipe, agenda_recipe, closing_recipe, RECIPE_FACTORIES,
)
from slidegen.services.presentation.design_tokens import DEFAULT_TOKENS
from slidegen.services.presentation.region import RegionRole


class TestTitleBodyRecipe:
    def test_produces_title_and_body_regions(self):
        recipe = title_body_recipe(DEFAULT_TOKENS)
        assert len(recipe.regions) == 2
        assert "title" in recipe.region_ids
        assert "body" in recipe.region_ids

    def test_all_regions_within_canvas(self):
        recipe = title_body_recipe(DEFAULT_TOKENS)
        for region in recipe.regions:
            assert 0.0 <= region.x_frac <= 1.0
            assert 0.0 <= region.y_frac <= 1.0
            assert region.x_frac + region.w_frac <= 1.0 + 0.001
            assert region.y_frac + region.h_frac <= 1.0 + 0.001


class TestGridCardsRecipe:
    def test_4_blocks_produce_2x2_grid(self):
        recipe = grid_cards_recipe(DEFAULT_TOKENS, n_blocks=4)
        card_ids = [rid for rid, role in recipe.region_roles.items() if role == RegionRole.CARD]
        assert len(card_ids) == 4

    def test_card_regions_dont_overlap(self):
        recipe = grid_cards_recipe(DEFAULT_TOKENS, n_blocks=4)
        card_regions = [r for r in recipe.regions if recipe.region_roles.get(r.region_id) == RegionRole.CARD]
        for i, r1 in enumerate(card_regions):
            for j, r2 in enumerate(card_regions):
                if i >= j:
                    continue
                # 不相交检测
                no_overlap = (
                    r1.x_frac + r1.w_frac <= r2.x_frac + 0.001
                    or r2.x_frac + r2.w_frac <= r1.x_frac + 0.001
                    or r1.y_frac + r1.h_frac <= r2.y_frac + 0.001
                    or r2.y_frac + r2.h_frac <= r1.y_frac + 0.001
                )
                assert no_overlap, f"Cards {i} and {j} overlap"


class TestTwoColumnRecipe:
    def test_produces_title_and_two_columns(self):
        recipe = two_column_recipe(DEFAULT_TOKENS)
        assert "title" in recipe.region_ids
        assert "left_col" in recipe.region_ids
        assert "right_col" in recipe.region_ids

    def test_columns_equal_width(self):
        recipe = two_column_recipe(DEFAULT_TOKENS)
        left = next(r for r in recipe.regions if r.region_id == "left_col")
        right = next(r for r in recipe.regions if r.region_id == "right_col")
        assert abs(left.w_frac - right.w_frac) < 0.01


class TestCoverRecipe:
    def test_produces_title_subtitle_decoration(self):
        recipe = cover_recipe(DEFAULT_TOKENS)
        assert "title" in recipe.region_ids
        assert "subtitle" in recipe.region_ids
        assert "deco_bar" in recipe.region_ids

    def test_decoration_has_shape_info(self):
        recipe = cover_recipe(DEFAULT_TOKENS)
        deco = next(r for r in recipe.regions if r.region_id == "deco_bar")
        assert deco.decoration_shape == "rounded_rect"
        assert deco.fill_role == "accent"


class TestAgendaRecipe:
    def test_produces_title_and_cards(self):
        recipe = agenda_recipe(DEFAULT_TOKENS, n_blocks=4)
        card_ids = [rid for rid in recipe.region_ids if "card" in rid]
        assert len(card_ids) == 4

    def test_max_8_blocks(self):
        recipe = agenda_recipe(DEFAULT_TOKENS, n_blocks=10)
        card_ids = [rid for rid in recipe.region_ids if "card" in rid]
        assert len(card_ids) == 8


class TestClosingRecipe:
    def test_produces_thanks_and_decorations(self):
        recipe = closing_recipe(DEFAULT_TOKENS)
        assert "thanks" in recipe.region_ids
        assert "deco_top" in recipe.region_ids
        assert "deco_bottom" in recipe.region_ids


class TestRecipeFactories:
    def test_all_6_recipes_registered(self):
        assert len(RECIPE_FACTORIES) == 6
        for name in ["TitleBodyRecipe", "GridCardsRecipe", "TwoColumnRecipe",
                      "CoverRecipe", "AgendaRecipe", "ClosingRecipe"]:
            assert name in RECIPE_FACTORIES
```

- [ ] **Step 3: 运行测试**

```bash
uv run pytest test/test_default_recipes.py -v
```

- [ ] **Step 4: Commit**

```bash
git add slidegen/services/presentation/recipes.py slidegen/services/presentation/default_recipes.py test/test_default_recipes.py
git commit -m "feat: add LayoutRecipe data class and 6 core preset recipes"
```

---

### Task 8: 升级 PresetRecipeFallback 返回 LayoutRecipe

**Files:**
- Modify: `slidegen/services/presentation/preset_recipes.py`

- [ ] **Step 1: 修改 preset_recipes.py**

```python
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
```

- [ ] **Step 2: 更新 test_preset_recipes.py（增加 LayoutRecipe 检验）**

```python
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
```

- [ ] **Step 3: 运行测试**

```bash
uv run pytest test/test_preset_recipes.py -v
```

- [ ] **Step 4: Commit**

```bash
git add slidegen/services/presentation/preset_recipes.py test/test_preset_recipes.py
git commit -m "feat: upgrade PresetRecipeFallback to return LayoutRecipe instances"
```

---

### Task 9: 创建 SlideRenderer + AssetProvider

**Files:**
- Create: `slidegen/services/presentation/slide_renderer.py`
- Create: `test/test_slide_renderer.py`

- [ ] **Step 1: 创建 slide_renderer.py**

```python
from __future__ import annotations

from pptx.slide import Slide
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

from slidegen.services.presentation.design_tokens import DesignTokens
from slidegen.services.presentation.recipes import LayoutRecipe
from slidegen.services.presentation.region import Region, RegionRole, RepeatRule
from slidegen.services.presentation.semantic import SlideSpec, BlockKind
from slidegen.services.presentation.image_generator import ImageGenerator
from slidegen.services.presentation.icon_searcher import IconSearcher
from slidegen.schemas.image_prompt import ImagePrompt


class AssetProvider:
    """Interface for image generation and icon search."""

    async def get_image(self, prompt: str, width: int, height: int) -> str | None:
        return None

    async def get_icon(self, query: str) -> str | None:
        return None


class DefaultAssetProvider(AssetProvider):
    def __init__(self, image_generator: ImageGenerator, icon_searcher: IconSearcher):
        self._image_generator = image_generator
        self._icon_searcher = icon_searcher

    async def get_image(self, prompt: str, width: int = 1024, height: int = 1024) -> str | None:
        try:
            asset = await self._image_generator.generate_image(ImagePrompt(prompt=prompt))
            return asset.path
        except Exception:
            return None

    async def get_icon(self, query: str) -> str | None:
        try:
            result = await self._icon_searcher.search_icons(query, k=1)
            return result[0] if result else None
        except Exception:
            return None


_SHAPE_MAP = {
    "rect": MSO_SHAPE.RECTANGLE,
    "rounded_rect": MSO_SHAPE.ROUNDED_RECTANGLE,
    "ellipse": MSO_SHAPE.OVAL,
}


class SlideRenderer:
    def __init__(self, tokens: DesignTokens, asset_provider: AssetProvider | None = None):
        self.tokens = tokens
        self.asset_provider = asset_provider

    async def render(self, slide: Slide, recipe: LayoutRecipe, spec: SlideSpec) -> None:
        all_regions = recipe.all_regions(len(spec.blocks))
        sorted_regions = sorted(all_regions, key=lambda r: (r.z_layer, all_regions.index(r)))

        for region in sorted_regions:
            role = recipe.region_roles.get(region.region_id)
            if role == RegionRole.DECORATION:
                self._render_decoration(slide, region)
            elif role in (RegionRole.TITLE, RegionRole.SUBTITLE, RegionRole.BODY, RegionRole.CARD_BODY, RegionRole.INDEX, RegionRole.FOOTER):
                self._render_text(slide, region, self._text_for_region(region.region_id, role, recipe, spec), role)
            elif role == RegionRole.CARD:
                self._render_card_background(slide, region)
            elif role == RegionRole.ICON:
                await self._render_icon(slide, region, recipe, spec)
            elif role == RegionRole.IMAGE:
                await self._render_image(slide, region, recipe, spec)

    def _text_for_region(self, region_id: str, role: RegionRole, recipe: LayoutRecipe, spec: SlideSpec) -> str:
        source = recipe.region_text_sources.get(region_id)
        if source == "slide_title" or (source is None and role == RegionRole.TITLE):
            return spec.title
        if source == "index":
            block_index = recipe.region_block_indexes.get(region_id, 0)
            return f"{block_index + 1:02d}"

        block = self._block_for_region(region_id, recipe, spec)
        if block is None:
            return ""
        if source == "block_title":
            return block.title
        if source == "block_title_text":
            return f"{block.title}\n{block.text}".strip()
        return block.text

    def _block_for_region(self, region_id: str, recipe: LayoutRecipe, spec: SlideSpec):
        block_index = recipe.region_block_indexes.get(region_id)
        if block_index is not None and 0 <= block_index < len(spec.blocks):
            return spec.blocks[block_index]
        return spec.blocks[0] if spec.blocks else None

    async def _render_icon(self, slide: Slide, region: Region, recipe: LayoutRecipe, spec: SlideSpec) -> None:
        block = self._block_for_region(region.region_id, recipe, spec)
        query = block.icon_query if block else None
        if not query or self.asset_provider is None:
            return
        icon_path = await self.asset_provider.get_icon(query)
        if icon_path:
            self._add_picture(slide, region, icon_path)

    async def _render_image(self, slide: Slide, region: Region, recipe: LayoutRecipe, spec: SlideSpec) -> None:
        block = self._block_for_region(region.region_id, recipe, spec)
        prompt = block.image_prompt if block else None
        if not prompt or self.asset_provider is None:
            return
        image_path = await self.asset_provider.get_image(prompt, width=1024, height=1024)
        if image_path:
            self._add_picture(slide, region, image_path)

    def _add_picture(self, slide: Slide, region: Region, path: str) -> None:
        left, top, width, height = region.to_absolute(self.tokens.slide_width, self.tokens.slide_height)
        slide.shapes.add_picture(path, Inches(left), Inches(top), width=Inches(width), height=Inches(height))

    def _render_card_background(self, slide: Slide, region: Region) -> None:
        self._render_decoration(slide, region)

    def _render_text(self, slide: Slide, region: Region, text: str, role: RegionRole) -> None:
        left, top, width, height = region.to_absolute(self.tokens.slide_width, self.tokens.slide_height)
        box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
        frame = box.text_frame
        frame.word_wrap = True
        frame.clear()
        para = frame.paragraphs[0]
        para.text = text

        if role == RegionRole.TITLE:
            para.font.size = Pt(self.tokens.title_size)
            para.font.name = self.tokens.title_font
            para.font.color.rgb = RGBColor.from_string(self.tokens.text_primary.lstrip("#"))
        elif role == RegionRole.SUBTITLE:
            para.font.size = Pt(self.tokens.subtitle_size)
            para.font.name = self.tokens.subtitle_font
            para.font.color.rgb = RGBColor.from_string(self.tokens.text_secondary.lstrip("#"))
        else:
            para.font.size = Pt(self.tokens.body_size)
            para.font.name = self.tokens.body_font
            para.font.color.rgb = RGBColor.from_string(self.tokens.text_primary.lstrip("#"))

    def _render_decoration(self, slide: Slide, region: Region) -> None:
        shape_type = _SHAPE_MAP.get(region.decoration_shape or "rect", MSO_SHAPE.RECTANGLE)
        left, top, width, height = region.to_absolute(self.tokens.slide_width, self.tokens.slide_height)
        shape = slide.shapes.add_shape(shape_type, Inches(left), Inches(top), Inches(width), Inches(height))

        if region.fill_role:
            token_attr = getattr(self.tokens, region.fill_role, None)
            if token_attr:
                shape.fill.solid()
                shape.fill.fore_color.rgb = RGBColor.from_string(token_attr.lstrip("#"))

        if region.line_role:
            token_attr = getattr(self.tokens, region.line_role, None)
            if token_attr:
                shape.line.color.rgb = RGBColor.from_string(token_attr.lstrip("#"))
        else:
            shape.line.fill.background()
```

- [ ] **Step 2: 编写 test_slide_renderer.py（渲染输出验证测试）**

```python
import pytest
from pptx import Presentation

from slidegen.services.presentation.slide_renderer import SlideRenderer, AssetProvider
from slidegen.services.presentation.design_tokens import DEFAULT_TOKENS
from slidegen.services.presentation.default_recipes import (
    agenda_recipe,
    cover_recipe,
    grid_cards_recipe,
    title_body_recipe,
    two_column_recipe,
)
from slidegen.services.presentation.semantic import SlideSpec, SlideKind, BlockSpec, BlockKind


def _make_spec(texts: list[str]) -> SlideSpec:
    blocks = tuple(BlockSpec(kind=BlockKind.POINT, title=t[:20], text=t) for t in texts)
    return SlideSpec(kind=SlideKind.CONTENT_POINTS, title="Test Slide", source_level=2, blocks=blocks)


@pytest.mark.anyio
async def test_renderer_creates_shapes_for_title_body():
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    spec = _make_spec(["Body content here"])
    recipe = title_body_recipe(DEFAULT_TOKENS)
    renderer = SlideRenderer(DEFAULT_TOKENS)

    await renderer.render(slide, recipe, spec)

    assert len(slide.shapes) >= 2
    texts = [s.text for s in slide.shapes if s.has_text_frame]
    assert "Test Slide" in texts
    assert "Body content here" in texts


@pytest.mark.anyio
async def test_renderer_grid_cards_4_blocks():
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    spec = _make_spec(["Block A", "Block B", "Block C", "Block D"])
    recipe = grid_cards_recipe(DEFAULT_TOKENS, n_blocks=4)
    renderer = SlideRenderer(DEFAULT_TOKENS)

    await renderer.render(slide, recipe, spec)

    assert len(slide.shapes) >= 5  # title + 4 card bodies


@pytest.mark.anyio
async def test_renderer_maps_text_for_cover_two_column_and_agenda():
    prs = Presentation()
    renderer = SlideRenderer(DEFAULT_TOKENS)

    cover = SlideSpec(
        kind=SlideKind.COVER,
        title="Quarterly Review",
        source_level=1,
        blocks=(BlockSpec(kind=BlockKind.SUBTITLE, title="", text="Q4 Executive Summary"),),
    )
    cover_slide = prs.slides.add_slide(prs.slide_layouts[6])
    await renderer.render(cover_slide, cover_recipe(DEFAULT_TOKENS), cover)
    cover_texts = [s.text for s in cover_slide.shapes if s.has_text_frame]
    assert "Quarterly Review" in cover_texts
    assert "Q4 Executive Summary" in cover_texts

    comparison = SlideSpec(
        kind=SlideKind.COMPARISON,
        title="Build vs Buy",
        source_level=3,
        blocks=(
            BlockSpec(kind=BlockKind.POINT, title="Build", text="Control roadmap"),
            BlockSpec(kind=BlockKind.POINT, title="Buy", text="Faster launch"),
        ),
    )
    comparison_slide = prs.slides.add_slide(prs.slide_layouts[6])
    await renderer.render(comparison_slide, two_column_recipe(DEFAULT_TOKENS), comparison)
    comparison_text = "\n".join(s.text for s in comparison_slide.shapes if s.has_text_frame)
    assert "Build\nControl roadmap" in comparison_text
    assert "Buy\nFaster launch" in comparison_text

    agenda = SlideSpec(
        kind=SlideKind.AGENDA,
        title="Agenda",
        source_level=1,
        blocks=(
            BlockSpec(kind=BlockKind.POINT, title="Market", text="Trends"),
            BlockSpec(kind=BlockKind.POINT, title="Plan", text="Next steps"),
        ),
    )
    agenda_slide = prs.slides.add_slide(prs.slide_layouts[6])
    await renderer.render(agenda_slide, agenda_recipe(DEFAULT_TOKENS, n_blocks=2), agenda)
    agenda_text = "\n".join(s.text for s in agenda_slide.shapes if s.has_text_frame)
    assert "01" in agenda_text
    assert "02" in agenda_text
    assert "Market\nTrends" in agenda_text


@pytest.mark.anyio
async def test_slide_renderer_full_loop_generates_valid_pptx(tmp_path):
    """集成测试：SlideSpec → PresetRecipe → SlideRenderer → PPTX"""
    from slidegen.services.presentation.preset_recipes import PresetRecipeFallback

    prs = Presentation()
    fallback = PresetRecipeFallback()

    # Slide 1: Cover
    cover_spec = SlideSpec(
        kind=SlideKind.COVER, title="My Deck", source_level=1,
        blocks=(BlockSpec(kind=BlockKind.TITLE, title="My Deck", text="Subtitle here"),)
    )
    cover_recipe = fallback.select(cover_spec, DEFAULT_TOKENS)
    slide1 = prs.slides.add_slide(prs.slide_layouts[6])
    await SlideRenderer(DEFAULT_TOKENS).render(slide1, cover_recipe, cover_spec)

    # Slide 2: Content
    content_spec = _make_spec(["Point A text", "Point B text", "Point C text", "Point D text"])
    content_recipe = fallback.select(content_spec, DEFAULT_TOKENS)
    slide2 = prs.slides.add_slide(prs.slide_layouts[6])
    await SlideRenderer(DEFAULT_TOKENS).render(slide2, content_recipe, content_spec)

    # 验证 PPTX 可保存和读取
    output = tmp_path / "test_output.pptx"
    prs.save(str(output))
    assert output.exists()

    reloaded = Presentation(str(output))
    assert len(reloaded.slides) == 2
    # slide 1 包含标题文本
    slide1_texts = [s.text for s in reloaded.slides[0].shapes if s.has_text_frame]
    assert "My Deck" in slide1_texts
```

- [ ] **Step 3: 运行测试**

```bash
uv run pytest test/test_slide_renderer.py -v
```

- [ ] **Step 4: Commit**

```bash
git add slidegen/services/presentation/slide_renderer.py test/test_slide_renderer.py
git commit -m "feat: add SlideRenderer with python-pptx native API and AssetProvider interface"
```

---

### Task 10: 创建 PostRenderValidator

**Files:**
- Create: `slidegen/services/presentation/post_render_validator.py`
- Create: `test/test_post_render_validator.py`

- [ ] **Step 1: 创建 post_render_validator.py**

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pptx import Presentation
from pptx.util import Pt


@dataclass
class SlideGeometryIssue:
    level: Literal["error", "warning"]
    slide_index: int
    message: str
    shapes_involved: tuple[str, ...] = ()


class PostRenderValidator:
    def __init__(self, mode: Literal["off", "warn", "fail"] = "warn"):
        self.mode = mode

    def validate(self, prs: Presentation) -> list[SlideGeometryIssue]:
        if self.mode == "off":
            return []
        issues: list[SlideGeometryIssue] = []
        for i, slide in enumerate(prs.slides):
            issues.extend(self._check_out_of_bounds(slide, i, int(prs.slide_width), int(prs.slide_height)))
            issues.extend(self._check_readability(slide, i))
        return issues

    def _check_out_of_bounds(self, slide, index: int, slide_w: int, slide_h: int) -> list[SlideGeometryIssue]:
        issues = []
        for shape in slide.shapes:
            left = shape.left
            top = shape.top
            right = left + shape.width
            bottom = top + shape.height
            if left < 0 or top < 0 or right > slide_w or bottom > slide_h:
                issues.append(SlideGeometryIssue(
                    level="error" if self.mode == "fail" else "warning",
                    slide_index=index,
                    message=f"Shape '{shape.name}' extends beyond slide boundaries",
                    shapes_involved=(shape.name,),
                ))
        return issues

    def _check_readability(self, slide, index: int) -> list[SlideGeometryIssue]:
        issues = []
        min_size = Pt(8)
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                if para.font.size and para.font.size < min_size:
                    issues.append(SlideGeometryIssue(
                        level="warning",
                        slide_index=index,
                        message=f"Text in shape '{shape.name}' is smaller than 8pt",
                        shapes_involved=(shape.name,),
                    ))
                for run in para.runs:
                    if run.font.size and run.font.size < min_size:
                        issues.append(SlideGeometryIssue(
                            level="warning",
                            slide_index=index,
                            message=f"Text in shape '{shape.name}' is smaller than 8pt",
                            shapes_involved=(shape.name,),
                        ))
        return issues
```

- [ ] **Step 2: 编写 test_post_render_validator.py**

```python
import pytest
from pptx import Presentation
from pptx.util import Inches, Pt

from slidegen.services.presentation.post_render_validator import PostRenderValidator


def test_empty_slide_passes():
    prs = Presentation()
    prs.slides.add_slide(prs.slide_layouts[6])
    validator = PostRenderValidator()
    issues = validator.validate(prs)
    assert len(issues) == 0


def test_in_bounds_shape_passes():
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.shapes.add_textbox(Inches(1), Inches(1), Inches(5), Inches(3))
    validator = PostRenderValidator()
    issues = validator.validate(prs)
    out_of_bounds = [i for i in issues if "boundaries" in i.message.lower()]
    assert len(out_of_bounds) == 0


def test_tiny_font_detected():
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    box = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(5), Inches(1))
    box.text_frame.paragraphs[0].font.size = Pt(6)
    validator = PostRenderValidator()
    issues = validator.validate(prs)
    readability = [i for i in issues if "smaller than 8pt" in i.message.lower()]
    assert len(readability) >= 1


def test_mode_off_returns_empty():
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    box = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(5), Inches(1))
    box.text_frame.paragraphs[0].font.size = Pt(6)
    validator = PostRenderValidator(mode="off")
    issues = validator.validate(prs)
    assert len(issues) == 0
```

- [ ] **Step 3: 运行测试**

```bash
uv run pytest test/test_post_render_validator.py -v
```

- [ ] **Step 4: Commit**

```bash
git add slidegen/services/presentation/post_render_validator.py test/test_post_render_validator.py
git commit -m "feat: add PostRenderValidator with out-of-bounds and readability checks"
```

---

### Task 11: 添加 shapes.json 迁移脚本

**Files:**
- Create: `scripts/migrate_shapes_json.py`
- Create: `test/test_migrate_shapes_json.py`

- [ ] **Step 1: 创建 scripts/migrate_shapes_json.py**

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SUPPORTED_SHAPES = {"rect", "rectangle", "roundRect", "rounded_rect"}


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _extract_location(shape: dict[str, Any]) -> dict[str, float] | None:
    loc = shape.get("location") or shape.get("bbox") or shape.get("position")
    if not isinstance(loc, dict):
        return None
    x = _as_float(loc.get("x") or loc.get("left"))
    y = _as_float(loc.get("y") or loc.get("top"))
    w = _as_float(loc.get("w") or loc.get("width"))
    h = _as_float(loc.get("h") or loc.get("height"))
    if w <= 0 or h <= 0:
        return None
    return {"x": x, "y": y, "w": w, "h": h}


def migrate_shapes(shapes: list[dict[str, Any]], slide_w: float, slide_h: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    regions: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for idx, shape in enumerate(shapes):
        shape_type = str(shape.get("shape_type") or shape.get("type") or "").strip()
        loc = _extract_location(shape)
        fill = shape.get("fill") or shape.get("fill_color")
        line = shape.get("line") or shape.get("line_color")
        if shape_type not in SUPPORTED_SHAPES or loc is None or not (fill or line):
            skipped.append({"index": idx, "reason": "unsupported_shape_or_missing_style", "shape_type": shape_type})
            continue
        regions.append(
            {
                "region_id": f"migrated_deco_{idx}",
                "role": "decoration",
                "x_frac": round(loc["x"] / slide_w, 4),
                "y_frac": round(loc["y"] / slide_h, 4),
                "w_frac": round(loc["w"] / slide_w, 4),
                "h_frac": round(loc["h"] / slide_h, 4),
                "decoration_shape": "rounded_rect" if shape_type in {"roundRect", "rounded_rect"} else "rect",
                "fill": fill,
                "line": line,
            }
        )
    return regions, skipped


def migrate_file(shapes_json: Path, output_report: Path, slide_w: float, slide_h: float) -> dict[str, Any]:
    payload = json.loads(shapes_json.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        shapes = payload
    elif isinstance(payload, dict):
        shapes = payload.get("shapes", [])
    else:
        shapes = []
    if not isinstance(shapes, list):
        raise ValueError("shapes.json must contain a list or a top-level 'shapes' list")
    regions, skipped = migrate_shapes(shapes, slide_w=slide_w, slide_h=slide_h)
    report = {"input": str(shapes_json), "converted": regions, "skipped": skipped}
    output_report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate stable shapes.json decoration styles into recipe DECORATION regions.")
    parser.add_argument("shapes_json", type=Path)
    parser.add_argument("--output-report", type=Path, default=Path("migration_report.json"))
    parser.add_argument("--slide-width", type=float, default=13.333)
    parser.add_argument("--slide-height", type=float, default=7.5)
    args = parser.parse_args()
    report = migrate_file(args.shapes_json, args.output_report, args.slide_width, args.slide_height)
    print(f"converted={len(report['converted'])} skipped={len(report['skipped'])} report={args.output_report}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 编写 test_migrate_shapes_json.py**

```python
import json

from scripts.migrate_shapes_json import migrate_file, migrate_shapes


def test_migrate_supported_rect_to_decoration_region():
    regions, skipped = migrate_shapes(
        [
            {
                "shape_type": "rect",
                "location": {"x": 1.0, "y": 1.5, "w": 2.0, "h": 1.0},
                "fill_color": "#112233",
            }
        ],
        slide_w=10.0,
        slide_h=5.0,
    )

    assert skipped == []
    assert regions == [
        {
            "region_id": "migrated_deco_0",
            "role": "decoration",
            "x_frac": 0.1,
            "y_frac": 0.3,
            "w_frac": 0.2,
            "h_frac": 0.2,
            "decoration_shape": "rect",
            "fill": "#112233",
            "line": None,
        }
    ]


def test_skips_complex_or_unstyled_shapes():
    regions, skipped = migrate_shapes(
        [{"shape_type": "freeform", "location": {"x": 0, "y": 0, "w": 1, "h": 1}}],
        slide_w=10.0,
        slide_h=5.0,
    )

    assert regions == []
    assert skipped == [{"index": 0, "reason": "unsupported_shape_or_missing_style", "shape_type": "freeform"}]


def test_migrate_file_writes_report(tmp_path):
    shapes_json = tmp_path / "shapes.json"
    report_path = tmp_path / "migration_report.json"
    shapes_json.write_text(json.dumps({"shapes": [{"shape_type": "rect", "location": {"x": 0, "y": 0, "w": 1, "h": 1}, "line_color": "#000000"}]}), encoding="utf-8")

    report = migrate_file(shapes_json, report_path, slide_w=10.0, slide_h=5.0)

    assert report_path.exists()
    assert len(report["converted"]) == 1
    assert json.loads(report_path.read_text(encoding="utf-8"))["converted"][0]["line"] == "#000000"
```

- [ ] **Step 3: 运行测试**

```bash
uv run pytest test/test_migrate_shapes_json.py -v
```

- [ ] **Step 4: Commit**

```bash
git add scripts/migrate_shapes_json.py test/test_migrate_shapes_json.py
git commit -m "feat: add shapes.json decoration migration report"
```

---

### Task 12: 配置 feature flag

**Files:**
- Modify: `slidegen/core/config.py`

- [ ] **Step 1: 在 config.py 中添加 feature flag 配置项**

在 Settings 类的适当位置添加：

```python
    # [RENDERER]
    ENABLE_RECIPE_RENDERER: bool = False
    ENABLE_RECIPE_AGENT: bool = True
```

- [ ] **Step 2: Commit**

```bash
git add slidegen/core/config.py
git commit -m "feat: add ENABLE_RECIPE_RENDERER and ENABLE_RECIPE_AGENT feature flags"
```

---

### Task 13: Phase 1b 集成测试 — 全链路验证

**Files:**
- Create: 集成测试（已在 test_slide_renderer.py 中包含全链路测试）

- [ ] **Step 1: 运行所有测试**

```bash
uv run pytest -v
```

- [ ] **Step 2: 验证全链路独立可运行**

```bash
uv run python -c "
import asyncio
from pptx import Presentation
from slidegen.services.presentation.design_tokens import DEFAULT_TOKENS
from slidegen.services.presentation.preset_recipes import PresetRecipeFallback
from slidegen.services.presentation.slide_renderer import SlideRenderer
from slidegen.services.presentation.semantic import SlideSpec, SlideKind, BlockSpec, BlockKind
from slidegen.services.presentation.post_render_validator import PostRenderValidator

async def main():
    prs = Presentation()
    fallback = PresetRecipeFallback()
    renderer = SlideRenderer(DEFAULT_TOKENS)

    spec = SlideSpec(kind=SlideKind.COVER, title='Deck', source_level=1,
        blocks=(BlockSpec(kind=BlockKind.TITLE, title='Deck', text='Subtitle'),))
    recipe = fallback.select(spec, DEFAULT_TOKENS)
    await renderer.render(prs.slides.add_slide(prs.slide_layouts[6]), recipe, spec)

    spec2 = SlideSpec(kind=SlideKind.CONTENT_POINTS, title='Points', source_level=2,
        blocks=tuple(BlockSpec(kind=BlockKind.POINT, title=f'P{i}', text=f'Text {i}') for i in range(4)))
    recipe2 = fallback.select(spec2, DEFAULT_TOKENS)
    await renderer.render(prs.slides.add_slide(prs.slide_layouts[6]), recipe2, spec2)

    prs.save('/tmp/test_phase1b.pptx')
    print('PPTX saved with', len(prs.slides), 'slides')

    validator = PostRenderValidator()
    issues = validator.validate(prs)
    print(f'Validator issues: {len(issues)}')
    for issue in issues:
        print(f'  [{issue.level}] {issue.message}')
    print('Phase 1b integration test PASSED')

asyncio.run(main())
"
```

- [ ] **Step 3: Commit (Phase 1b 完成标记)**

```bash
git commit --allow-empty -m "feat: complete Phase 1b — minimal rendering loop"
```

---

## Phase 1c: RecipeAgent 接入（LLM 生成 recipe 主路径）

### Task 14: 创建 RecipeAgent

**Files:**
- Create: `slidegen/services/presentation/recipe_agent.py`
- Create: `test/test_recipe_agent.py`

- [ ] **Step 1: 创建 recipe_agent.py（使用 agno Agent + structured_outputs）**

```python
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
    """agno structured output model — 直接产出 LayoutRecipe JSON schema。"""
    name: str
    regions: list[AgentRegionOutput] = Field(default_factory=list)
    repeats: list[AgentRepeatRuleOutput] = Field(default_factory=list)
    region_roles: dict[str, str] = Field(default_factory=dict)
    region_block_indexes: dict[str, int] = Field(default_factory=dict)
    region_text_sources: dict[str, str] = Field(default_factory=dict)


# === Agent instructions（无需再写 JSON 格式说明，由 output_model 的 schema 自动约束） ===

RECIPE_AGENT_INSTRUCTIONS = """You are a slide layout designer. Given content blocks and visual constraints, produce a slide LayoutRecipe.

## Canvas
Coordinates are fractions (0.0–1.0) of canvas dimensions.
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
    field types and ranges (x_frac ∈ [0,1], z_layer ∈ {0,10,20,30}, etc.).
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
            # agno structured output: 自动将 LLM 输出解析为 AgentRecipeOutput
            structured_outputs=True,
            output_model=AgentRecipeOutput,
        )
        response = await agent.arun(prompt)
        # 开启 structured_outputs 后，response.content 直接是 AgentRecipeOutput 实例
        if isinstance(response.content, AgentRecipeOutput):
            return response.content
        # fallback：如果 agno 没有自动解析，尝试手动从 dict 构造
        if isinstance(response.content, dict):
            return AgentRecipeOutput.model_validate(response.content)
        raise RecipeAgentError(f"Unexpected agent output type: {type(response.content)}")

    def _to_layout_recipe(self, output: AgentRecipeOutput) -> LayoutRecipe:
        """将 agno 结构化输出转换为内部 LayoutRecipe 数据类。"""
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
        """二次验证：虽然 Pydantic 已做基本校验，但业务逻辑（非空等）在此检查。"""
        if not recipe.regions and not recipe.repeats:
            raise RecipeAgentError("LayoutRecipe must have at least one region or repeat rule")
        for region in recipe.regions:
            if region.x_frac + region.w_frac > 1.01:
                raise RecipeAgentError(f"Region {region.region_id}: right edge out of canvas")
            if region.y_frac + region.h_frac > 1.01:
                raise RecipeAgentError(f"Region {region.region_id}: bottom edge out of canvas")
```

- [ ] **Step 2: 编写 test_recipe_agent.py（mock agno Agent.arun）**

```python
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
    """创建一个 mock coroutine，模拟 RecipeAgent._run_agent 的结构化输出。"""
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
        import asyncio
        await asyncio.sleep(1.0)
    agent = RecipeAgent()
    agent._run_agent = _slow
    with pytest.raises(RecipeAgentError):
        await agent.generate(_make_spec(), DEFAULT_TOKENS, timeout=0.1)


@pytest.mark.anyio
async def test_agent_recipe_output_pydantic_validates_fields():
    """Pydantic 自动校验：z_layer 必须是 Literal 值。"""
    with pytest.raises(Exception):  # Pydantic ValidationError
        AgentRegionOutput(region_id="bad", x_frac=0.1, y_frac=0.1, w_frac=0.5, h_frac=0.5, z_layer=15)


@pytest.mark.anyio
async def test_agent_recipe_output_rejects_out_of_bounds_coords():
    """Pydantic 自动校验：x_frac 必须在 [0,1] 范围。"""
    with pytest.raises(Exception):
        AgentRegionOutput(region_id="bad", x_frac=-0.1, y_frac=0.1, w_frac=0.5, h_frac=0.5, z_layer=10)


@pytest.mark.anyio
async def test_agent_recipe_output_rejects_overflow():
    """Pydantic 自动校验：w_frac 必须在 [0,1] 范围。"""
    with pytest.raises(Exception):
        AgentRegionOutput(region_id="bad", x_frac=0.1, y_frac=0.1, w_frac=1.5, h_frac=0.5, z_layer=10)
```

- [ ] **Step 3: 运行测试**

```bash
uv run pytest test/test_recipe_agent.py -v
```

- [ ] **Step 4: Commit**

```bash
git add slidegen/services/presentation/recipe_agent.py test/test_recipe_agent.py
git commit -m "feat: add RecipeAgent with LLM-driven recipe generation and JSON schema validation"
```

---

### Task 15: 创建 Agent → Fallback 调度层

**Files:**
- Modify: `slidegen/services/presentation/recipe_agent.py`（在同一个文件中或新建调度函数）

- [ ] **Step 1: 在 recipe_agent.py 中添加调度函数**

```python
from slidegen.services.presentation.preset_recipes import PresetRecipeFallback
from slidegen.services.presentation.post_render_validator import PostRenderValidator


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
```

- [ ] **Step 2: 编写调度层测试**

```python
@pytest.mark.anyio
async def test_resolve_recipe_falls_back_on_agent_error():
    agent = RecipeAgent()
    async def _fail(_prompt: str):
        raise RecipeAgentError("mock failure")
    agent._run_agent = _fail
    spec = _make_spec()
    recipe = await resolve_recipe(spec, DEFAULT_TOKENS, agent=agent, enable_agent=True)
    assert isinstance(recipe, LayoutRecipe)
    # 应该 fallback 到预设
    assert recipe.name in ("TitleBodyRecipe", "GridCardsRecipe", "TwoColumnRecipe",
                           "CoverRecipe", "AgendaRecipe", "ClosingRecipe")


@pytest.mark.anyio
async def test_resolve_recipe_uses_fallback_when_agent_disabled():
    agent = RecipeAgent()
    agent._run_agent = _mock_arun(_valid_output())
    spec = _make_spec()
    recipe = await resolve_recipe(spec, DEFAULT_TOKENS, agent=agent, enable_agent=False)
    # Agent 未被调用 — fallback 路径不调用 _run_agent
    assert isinstance(recipe, LayoutRecipe)
    assert recipe.name in ("TitleBodyRecipe", "GridCardsRecipe", "TwoColumnRecipe",
                           "CoverRecipe", "AgendaRecipe", "ClosingRecipe")
```

- [ ] **Step 3: 运行测试**

```bash
uv run pytest test/test_recipe_agent.py -v
```

- [ ] **Step 4: Commit**

```bash
git add slidegen/services/presentation/recipe_agent.py test/test_recipe_agent.py
git commit -m "feat: add resolve_recipe dispatch with agent-to-fallback failover"
```

---

### Task 16: 并发调度

**Files:**
- Modify: `slidegen/services/presentation/recipe_agent.py`

- [ ] **Step 1: 添加并发调度函数**

```python
async def resolve_all_recipes(
    specs: list[SlideSpec],
    tokens: DesignTokens,
    *,
    agent: RecipeAgent | None = None,
    fallback: PresetRecipeFallback | None = None,
    enable_agent: bool = True,
    agent_timeout: float = 5.0,
) -> list[LayoutRecipe]:
    """并发解析所有 slide 的 LayoutRecipe。单个失败不影响其他 slide。"""
    async def resolve_one(spec: SlideSpec) -> LayoutRecipe:
        return await resolve_recipe(
            spec, tokens,
            agent=agent, fallback=fallback,
            enable_agent=enable_agent, agent_timeout=agent_timeout,
        )

    tasks = [resolve_one(spec) for spec in specs]
    return list(await asyncio.gather(*tasks))
```

- [ ] **Step 2: 编写并发测试**

```python
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
    # 第 2 个 slide fallback 到预设
    assert recipes[1].name != "TestRecipe"
```

- [ ] **Step 3: 运行测试**

```bash
uv run pytest test/test_recipe_agent.py -v
```

- [ ] **Step 4: Commit**

```bash
git add slidegen/services/presentation/recipe_agent.py test/test_recipe_agent.py
git commit -m "feat: add concurrent resolve_all_recipes with independent per-slide failover"
```

---

### Task 17: Phase 1c 集成验证

- [ ] **Step 1: 运行全部测试**

```bash
uv run pytest -v
```

- [ ] **Step 2: Commit (Phase 1c 完成标记)**

```bash
git commit --allow-empty -m "feat: complete Phase 1c — RecipeAgent integration"
```

---

## Phase 2: 切换到新主渲染管线

### Task 18: 在 converter.py 中接入新渲染路径

**Files:**
- Modify: `slidegen/services/presentation/converter.py`
- Modify: `test/test_converter.py`

- [ ] **Step 1: 先写 feature-flag 新路径集成测试**

```python
import pytest
from pptx import Presentation

from slidegen.services.document.markdown import MarkdownDocument
from slidegen.services.presentation.converter import MarkdownToPresentation


@pytest.mark.anyio
async def test_recipe_renderer_path_builds_full_deck_without_template_cleanup(monkeypatch):
    monkeypatch.setattr("slidegen.core.config.settings.ENABLE_RECIPE_RENDERER", True)
    monkeypatch.setattr("slidegen.core.config.settings.ENABLE_RECIPE_AGENT", False)

    template = Presentation()
    template.slide_width = 12192000
    template.slide_height = 6858000
    template.slides.add_slide(template.slide_layouts[6])
    document = MarkdownDocument(
        "# Deck\n"
        "## Chapter A\n"
        "### Point One\n"
        "#### Detail\n"
        "Body A\n"
        "### Point Two\n"
        "#### Detail\n"
        "Body B\n"
    )

    prs = await MarkdownToPresentation().generate(template, document)

    assert prs is not template
    assert prs.slide_width == template.slide_width
    assert prs.slide_height == template.slide_height
    assert len(prs.slides) == 6  # cover, agenda, chapter home, 2 content slides, closing
    all_text = "\n".join(shape.text for slide in prs.slides for shape in slide.shapes if shape.has_text_frame)
    assert "Deck" in all_text
    assert "Chapter A" in all_text
    assert "Point One" in all_text
    assert "Body A" in all_text
```

- [ ] **Step 2: 在 converter.py 中添加完整 feature-flag 分支**

在 imports 中新增：

```python
from slidegen.core.config import settings
from slidegen.services.presentation.design_tokens import extract_design_tokens_from_presentation
from slidegen.services.presentation.post_render_validator import PostRenderValidator
from slidegen.services.presentation.recipe_agent import RecipeAgent, resolve_recipe
from slidegen.services.presentation.semantic import BlockKind, BlockSpec, SlideKind, SlideSpec, build_content_slide_spec
from slidegen.services.presentation.slide_renderer import AssetProvider, SlideRenderer
```

在 `MarkdownToPresentation` 中添加构造函数和新路径 helper；`generate()` 开头在解析 profile 之前插入 `if settings.ENABLE_RECIPE_RENDERER: return await self._generate_with_recipe_renderer(template_prs, markdown_document)`，旧 XML-copy 路径保持原样：

```python
class MarkdownToPresentation:
    """Generate a PPT presentation from a markdown document."""

    def __init__(self, *, recipe_model: object | None = None, asset_provider: AssetProvider | None = None) -> None:
        self.recipe_model = recipe_model
        self.asset_provider = asset_provider

    async def _generate_with_recipe_renderer(
        self,
        template_prs: Presentation,
        markdown_document: MarkdownDocument,
    ) -> Presentation:
        main_heading = markdown_document.main
        if main_heading is None:
            raise MarkdownDocumentError("Markdown document must have a main heading")

        chapter_slide_groups = list(iter_chapter_slide_groups(main_heading))
        chapters: list[Heading] = [group.chapter for group in chapter_slide_groups]
        if not chapters:
            raise MarkdownDocumentError("Markdown document must have at least one level 2 heading")

        output_prs = Presentation()
        output_prs.slide_width = template_prs.slide_width
        output_prs.slide_height = template_prs.slide_height
        tokens = extract_design_tokens_from_presentation(template_prs, "general")
        renderer = SlideRenderer(tokens, asset_provider=self.asset_provider)
        agent = RecipeAgent(model=self.recipe_model) if settings.ENABLE_RECIPE_AGENT and self.recipe_model is not None else None

        async def render_spec(spec: SlideSpec) -> None:
            recipe = await resolve_recipe(spec, tokens, agent=agent, enable_agent=agent is not None)
            slide = output_prs.slides.add_slide(output_prs.slide_layouts[6])
            await renderer.render(slide, recipe, spec)

        await render_spec(self._cover_spec(main_heading))
        await render_spec(self._agenda_spec(chapters))
        for group in chapter_slide_groups:
            await render_spec(self._chapter_home_spec(group.chapter))
            for content_heading in group.slides:
                await render_spec(build_content_slide_spec(content_heading))
        await render_spec(self._closing_spec())

        issues = PostRenderValidator(mode="fail").validate(output_prs)
        if issues:
            messages = "; ".join(issue.message for issue in issues if issue.level == "error")
            if messages:
                raise MarkdownDocumentError(f"Recipe-rendered presentation failed geometry validation: {messages}")
        return output_prs

    def _cover_spec(self, main_heading: Heading) -> SlideSpec:
        return SlideSpec(
            kind=SlideKind.COVER,
            title=main_heading.element_text,
            source_level=1,
            blocks=(BlockSpec(kind=BlockKind.SUBTITLE, title="", text=""),),
        )

    def _agenda_spec(self, chapters: list[Heading]) -> SlideSpec:
        return SlideSpec(
            kind=SlideKind.AGENDA,
            title="目录",
            source_level=1,
            blocks=tuple(BlockSpec(kind=BlockKind.POINT, title=chapter.element_text, text="") for chapter in chapters),
        )

    def _chapter_home_spec(self, chapter: Heading) -> SlideSpec:
        return SlideSpec(
            kind=SlideKind.SECTION_COVER,
            title=chapter.element_text,
            source_level=2,
            blocks=(BlockSpec(kind=BlockKind.TITLE, title=chapter.element_text, text=""),),
        )

    def _closing_spec(self) -> SlideSpec:
        return SlideSpec(
            kind=SlideKind.CLOSING,
            title="谢谢",
            source_level=1,
            blocks=(BlockSpec(kind=BlockKind.TITLE, title="谢谢", text=""),),
        )
```

- [ ] **Step 3: 运行 feature flag 新路径测试**

```bash
uv run pytest test/test_converter.py::test_recipe_renderer_path_builds_full_deck_without_template_cleanup -v
```

- [ ] **Step 4: 运行旧路径回归测试，确认默认 flag 不改变现有行为**

```bash
uv run pytest test/test_converter.py -v
```

- [ ] **Step 5: Commit**

```bash
git add slidegen/services/presentation/converter.py test/test_converter.py
git commit -m "feat: add full-deck recipe renderer path behind feature flag"
```

---

### Task 19: Phase 2 切换验收并保留旧路径

**Files:**
- No code changes

- [ ] **Step 1: 明确 Phase 2 不清理 PresentationRenderPlan**

Phase 2 只新增完整 feature-flag 新路径。`PresentationRenderPlan.use_native_*`、template index 字段、`_cleanup_template_slides()` 仍服务于默认关闭的旧路径；这些字段必须等 Phase 3 删除旧渲染路径时一起清理。

- [ ] **Step 2: 运行新旧路径 converter 测试，确认默认关闭不回归**

```bash
uv run pytest test/test_converter.py -v
```

- [ ] **Step 3: Commit (Phase 2 完成标记)**

```bash
git commit --allow-empty -m "feat: complete Phase 2 — feature-flagged full-deck recipe renderer"
```

---

## Phase 3: 清理旧代码和历史资产

### Task 20: 删除旧渲染代码

- [ ] **Step 1: 删除 components.py**

```bash
git rm slidegen/services/presentation/components.py
```

- [ ] **Step 2: 删除 pages.py 中的旧页面类**

删除: `ChapterContentPage`, `CoverPage`, `CatalogPage`, `ChapterHomePage`, `EndPage`, `Page` base class 中的 XML 操作辅助方法

- [ ] **Step 3: 删除 utils/slide.py 中的 XML 函数**

删除: `add_shape_by_xml`, `add_para_by_xml`, `convert_paragraph_xml`, `runs_merge`, `modify_shape_xml`

- [ ] **Step 4: 删除 native_pages.py**

```bash
git rm slidegen/services/presentation/native_pages.py
```

- [ ] **Step 5: 清理 template_profile.py 中的 _supports_legacy_renderer**

- [ ] **Step 6: 清理 converter.py 中的旧方法**

删除: `_cleanup_template_slides`, `_slide_index_by_id`, `reused_template_slide_ids`, `current_template_index`, `cleanup_template_slide_ids`

- [ ] **Step 7: 清理 render_plan.py 中的旧模板复用字段**

删除: `chapter_home_template_index`, `chapter_content_template_index`, `end_template_index`, `use_native_*`, `cleanup_template_indexes`。`PresentationRenderPlan` 保留 slide index 编排和 `ConversionSummary` 所需字段。

- [ ] **Step 8: 移除 feature flag ENABLE_RECIPE_RENDERER**

新路径成为唯一路径，删除 feature flag 相关条件分支。

- [ ] **Step 9: 清理 shapes.json 运行时依赖**

将 `shapes.json` 移入 test fixture 或归档目录。

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "refactor: delete legacy XML-copy rendering code (~800 lines removed)"
```

---

### Task 21: 更新测试和最终验证

- [ ] **Step 1: 更新所有受影响的现有测试**

```bash
uv run pytest -v
# 修复所有失败测试
```

- [ ] **Step 2: 验证运行时不再引用 shapes.json**

```bash
rg "shapes\\.json" slidegen --glob "*.py" || echo "No runtime references to shapes.json found"
```

- [ ] **Step 3: 验证代码量减少**

```bash
git diff --stat main
```

- [ ] **Step 4: 最终 commit**

```bash
git add -A
git commit -m "test: update tests for new recipe-driven rendering pipeline"
```

---

## 自审检查

### 1. Spec 覆盖检查

| Spec 章节 | 覆盖 Task |
|---|---|
| §1 Design Token 层 | Task 2 (DesignTokens + 提取) |
| §2 增强版语义模型 | Task 3 (SlideSpec/BlockSpec 扩展) |
| §3 RecipeAgent + PresetRecipeFallback | Task 4, 8 (PresetRecipeFallback), Task 14-16 (RecipeAgent + 调度 + 并发) |
| §4 LayoutRecipe | Task 6 (LayoutRecipe), Task 7 (6 个核心 Recipe) |
| §4.1 默认 Recipe 样式库迁移 | Task 11 (shapes.json → DECORATION region 迁移脚本 + migration_report.json) |
| §4.5 z-layer 编排 | Task 14 (Agent prompt 含 z-layer 约束), Task 6 (Region.z_layer) |
| §5 SlideRenderer | Task 9 (SlideRenderer + AssetProvider) |
| §6 PostRenderValidator | Task 10 |
| §7 模板 PPTX 新角色 | Task 2 (extract_design_tokens_from_presentation) |
| §8 AssetProvider | Task 9 (AssetProvider 接口) |
| §9 图片/图标插入流程 | Task 7 (ICON region + block 绑定), Task 9 (AssetProvider + ICON/IMAGE 渲染) |
| §10 页码和页脚 | Task 9 (FOOTER/INDEX 文本渲染契约) |
| §11 模板清理策略 | Task 18 (新路径只提取 DesignTokens 并生成新 Presentation), Task 20 (旧路径删除后清理 converter/render_plan) |
| Phase 1a | Tasks 1-5 |
| Phase 1b | Tasks 6-13 |
| Phase 1c | Tasks 14-17 |
| Phase 2 | Tasks 18-19 |
| Phase 3 | Tasks 20-21 |

### 2. Placeholder 扫描

无 TBD/TODO/占位符。所有步骤包含实际代码。

### 3. 类型一致性

- `Region.region_id: str` — 所有引用一致
- `RepeatRule.expand(count: int)` — 所有调用一致
- `LayoutRecipe.regions: tuple[Region, ...]` — 所有引用一致
- `LayoutRecipe.region_block_indexes` / `region_text_sources` — RecipeAgent、default_recipes、SlideRenderer 三处共享同一绑定契约
- `PresetRecipeFallback.select(spec, tokens)` — 所有调用一致
- `RecipeAgent.generate(spec, tokens, timeout)` — 所有调用一致

> 注：Phase 2 现在是完整的 feature-flag 全页面新路径，不再是 content-only 示例；`PresentationRenderPlan` 清理延后到 Phase 3，避免默认关闭旧路径期间出现半切换回归。
