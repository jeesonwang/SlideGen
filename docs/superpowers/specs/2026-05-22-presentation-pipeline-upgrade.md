# Presentation Pipeline Upgrade: From XML-Copy Rendering to Recipe-Driven Native Generation

Date: 2026-05-22
Status: proposed for review
Depends on: [2026-05-18-semantic-layout-renderer-design.md](./2026-05-18-semantic-layout-renderer-design.md)

## Context

当前 SlideGen 的内容页生成路径是：

```
Markdown → MarkdownToPresentation → ChapterContentPage
  → 数字节点数量 → one_point/two_points/three_points/four_points
  → get_random_style() → 复制 shapes.json 中的 PowerPoint XML
  → 替换占位符文本
```

这套路径有几个根本性问题：

1. **布局由"抽取的 shape 样本"决定，而非内容语义**。一个 3-point slide 和另一个 3-point slide 可能被随机分配到视觉完全不相关的 style，因为它们来自不同人在不同模板里手画的 shape。
2. **完全依赖模板 PPTX**。如果模板缺少某个 role，fallback 路径（`NativePage`）产出的只是白底黑字，视觉质量断崖式下降。
3. **不支持长文本、表格、图表、对比页、流程页**。`ChapterContentPage` 的唯一逻辑是数字节点数量，只支持 1-4 个 point。
4. **没有导出前 QA**。没有重叠检测、越界检测、可读性检测。当前验证模块（`validation/`）只做 PPTX 的 XML Schema 级别校验，不做视觉层面的几何检查。
5. **`shapes.json` 和 `ComponentsManager` 成为瓶颈**。每个新版式都需要先手画一个 PPTX 模板页 → 提取 XML → 写入 shapes.json，开发体验差，且产出的 XML 难以调试。

与此同时，我们分析了[一份高质量 PPT 的 JS 生成代码](../../学前教育普惠性研究综述_PPT生成原理讲解.md)，它的工程链路提供了重要的参考：

```
设计令牌 → 组件化版式函数 → 约束坐标布局 → 机械 QA → 导出
```

这套链路的核心思想是"先把视觉规则写死，再让程序按规则执行"，而不是"从模板里随机抽一个 style 碰运气"。

本 spec 基于 [semantic-layout-renderer-design](./2026-05-18-semantic-layout-renderer-design.md) 的设计方向，结合上述分析，提出一个更具体的、包含删除旧运行时管线和迁移现有样式资产的升级方案。

## Relationship To Existing Specs

这份 spec 是 [semantic-layout-renderer-design](./2026-05-18-semantic-layout-renderer-design.md) 的收敛升级版。前一版提出 `SlideSpec / BlockSpec → LayoutSelector → LayoutRecipe → Renderer` 的方向，并允许 `shapes.json` 在迁移期作为兼容或装饰资产继续存在；本 spec 将目标态进一步明确为：

- `shapes.json` 不再作为运行时依赖，也不再由 `ComponentsManager.get_random_style()` 随机选择。
- `shapes.json` 中已有的布局经验可以先保留，但要迁移成代码内置的 `LayoutRecipe` 样式库（装饰元素以 `DECORATION` region 形式存储）。
- 旧 XML-copy renderer 删除后，所有 PPT 页面都通过 `DesignTokens + LayoutRecipe + SlideRenderer` 渲染。
- `BlockSpec` 只表达内容语义，不承载从 XML 抽取出的视觉形状。

## Goals

- 用 **Design Token + LayoutRecipe + Native Renderer** 替代当前的 `shapes.json` 随机 style 路径作为唯一主渲染管线
- 将现有 `shapes.json` 的可复用样式经验迁移为代码内置的默认 `LayoutRecipe` 库（装饰元素以 `DECORATION` region 形式存储）
- 增加 **导出前几何 QA** 层（重叠检测、越界检测、可读性检测）
- 增强 `SlideSpec`/`BlockSpec` 语义模型，支持更多 slide kind
- 实现 `LayoutSelector`，基于内容语义而非子节点数量选择版式
- 让 `NativePage` 从"占位符 fallback"升级为"有设计令牌支持的完整视觉方案"
- 保留模板 PPTX 的配色/字体提取能力（作为 Design Token 的来源之一），但不再依赖模板 shape 的结构
- 删除旧的 XML-copy 渲染链路，避免新旧两套路由长期并存

## Non-Goals

- 不在此阶段实现 table/chart 的 native rendering（保留在当前 `semantic.py` 的 slide kind 定义中，但 rendering 留给后续 PR）
- 不改造前端编辑器
- 不改变 API 路由签名
- 不删除模板 PPTX 的上传/管理功能（模板仍可作为 Design Token 来源和品牌风格参考）
- 不追求与现有 `shapes.json` 产出的像素级等价
- 不把 `shapes.json` 的 XML 抽象成 `BlockSpec`。`BlockSpec` 是语义层，旧样式资产应迁移到 `LayoutRecipe` 层（`DECORATION` region）
- 不在新主渲染管线中继续复制 PowerPoint XML 片段。解析不了的复杂装饰先跳过或降级为简单 native primitive

## What Gets Deleted Or Retired

以下模块/代码将在迁移完成后删除或退出运行时路径：

| 删除/退出项 | 原因 |
|---|---|
| `components.py` — `ComponentsManager`, `CShape`, `Style`, `LayoutType`, `ChapterLayout`, `ContentType`, `Location` | 随机 style loader 和 XML shape 数据模型被代码定义的 Recipe/Primitive 体系取代 |
| `components/shapes/shapes.json` 的运行时依赖 | 不再由运行时读取 JSON 或复制其中 XML；该文件可暂时保留为迁移输入、fixture 或历史样式来源 |
| `pages.py` — `ChapterContentPage`（及其中 `_get_slide_type`, `get_random_style`, `add_shape_by_xml` 调用链） | 内容页渲染改为 Recipe + Native Renderer |
| `pages.py` — `CoverPage`, `CatalogPage`, `ChapterHomePage`, `EndPage` 的全部 XML-copy 实现 | 这些页面类型改为使用 Recipe + SlideRenderer |
| `pages.py` — `Page` base class 中的 XML 操作辅助方法 | 不再需要解析/操作 shape XML |
| `utils/slide.py` — `add_shape_by_xml`, `add_para_by_xml`, `convert_paragraph_xml`, `runs_merge` | 不再需要手动拼装 PowerPoint XML |
| `template_profile.py` 中 `_supports_legacy_renderer` | Role 检测和 legacy 兼容性拆开；新主渲染管线不依赖旧占位符结构 |
| `converter.py` — `_cleanup_template_slides`, `_slide_index_by_id`, `reused_template_slide_ids`, `current_template_index`, `cleanup_template_slide_ids` | 新架构不再 clone 和清理模板 slide |
| `render_plan.py` — `use_native_*` flag、`chapter_home_template_index`、`chapter_content_template_index`、`end_template_index`、`cleanup_template_indexes` 属性 | 新架构统一走 native 路径，不再有 template vs native 二元选择。注：`PresentationRenderPlan` 本身保留（见 What Stays），只删除这些字段 |

## What Stays

| 保留项 | 角色变化 |
|---|---|
| `MarkdownToPresentation` (converter.py) | 保留为 orchestrator，但内部调用链从 `ChapterContentPage` 切换到 `LayoutSelector → SlideRenderer`；移除 `_cleanup_template_slides` 等旧方法 |
| `render_plan.py` — `PresentationRenderPlan`, `build_presentation_render_plan` | 保留 slide 编排职责，剔除 `use_native_*` flag 和 template index 相关字段，只做 slide index 计算 |
| `semantic.py` — `SlideSpec`, `BlockSpec`, `build_content_slide_spec` | **增强**：增加更多 slide/block kind，增加内容密度估算 |
| `template_profile.py` — `TemplateProfile`, `profile_presentation_template`, role 检测 | 保留 role 检测逻辑；移除 `_supports_legacy_renderer`；role assignment 不再等同于 legacy renderer 可用性 |
| `design_tokens.py`（新增） | DesignTokens 数据类 + 默认 token set + PPTX theme 提取 + shape 采样提取 |
| `recipes.py`（新增） | `LayoutRecipe` 数据类定义 + Recipe factory 函数 |
| `default_recipes.py`（新增） | 承接从 `shapes.json` 迁移来的默认布局和装饰 region；6 个核心 Recipe 的具体实现 |
| `slide_renderer.py`（新增） | 基于 python-pptx 原生 API 的 SlideRenderer + AssetProvider 接口 |
| `native_pages.py` | **保留至 Phase 2 结束**：Phase 1 期间继续作为 fallback 渲染路径；Phase 2 被 `SlideRenderer` 完全取代后，在 Phase 3 删除 |
| `post_render_validator.py`（新增） | 越界检测 + 字体检测（Phase 1），重叠检测（experimental/warn-only） |
| `validation/` | 保留 XML schema 校验，与 PostRenderValidator 职责互补（XML 结构 vs 几何视觉） |
| `generator.py` — `PresentationGenerator` | 保留对外 API，内部 converter 调用不变 |

## Proposed Architecture

### 整体新链路

```
MarkdownDocument
  → SlideSpec / BlockSpec (增强版语义模型)
  → LayoutSelector (确定性版式选择)
  → DesignTokens (配色/字体/间距)
  → LayoutRecipe (参数化公式计算的完整版式描述，含确定性默认 z_layer)
  → SlideRenderer (python-pptx 原生 API)
  → PostRenderValidator (重叠/越界/可读性 QA)
  → PPTX
```

### 1. Design Token 层（新增）

这是本次升级最重要的新增层。参考那份 JS 代码的做法——先定义统一色板 `C`，把所有可选颜色限制在一小组互相兼容的颜色里。

```python
@dataclass(frozen=True)
class DesignTokens:
    """Unified design tokens for native slide rendering.

    All color values are hex strings (e.g. "#1A2B3C") for consistency
    with python-pptx's RGBColor.
    """

    # Color palette — each color has a single semantic role
    primary: str         # 结构主色（标题、重点边框、深色背景）
    accent: str          # 强调色（编号、流程箭头、标签）
    light_bg: str        # 大面积浅背景
    light_bg_alt: str    # 卡片内交替背景
    text_primary: str    # 主文字色
    text_secondary: str  # 次文字色
    text_on_dark: str    # 深色背景上的文字

    # Semantic accent colors — used for data categories, status badges, etc.
    semantic_positive: str   # e.g. green — growth, positive trends
    semantic_negative: str   # e.g. red — decline, warnings
    semantic_neutral: str    # e.g. gray/blue — neutral, informational

    # Typography
    title_font: str
    title_size: int      # pt
    subtitle_font: str
    subtitle_size: int
    body_font: str
    body_size: int
    caption_font: str
    caption_size: int

    # Spacing (in inches, for a 13.333×7.5 widescreen canvas)
    slide_width: float = 13.333      # inches — used by Recipe factory to convert spacing → fraction
    slide_height: float = 7.5        # inches — used by Recipe factory to convert spacing → fraction
    page_margin_x: float
    page_margin_y: float
    card_gap: float
    section_gap: float
    line_spacing_multiple: float = 1.2  # multiplier (1.0 = single, not inches)
```

**Spacing 与 Region fraction 的关系：**

`DesignTokens` 中的 spacing 字段（`page_margin_x`、`card_gap` 等）以 inches 表示，这是设计师的自然思维单位。`Region` 中的坐标以 fraction（0.0–1.0）表示，这是适配任意 canvas 尺寸的归一化坐标。

两者的桥梁在 **Recipe factory 函数**中完成一次性转换：

```python
def grid_cards_recipe(n_blocks: int, tokens: DesignTokens) -> LayoutRecipe:
    margin_frac = tokens.page_margin_x / tokens.slide_width
    gap_frac = tokens.card_gap / tokens.slide_width
    card_w = (1.0 - 2 * margin_frac - (n_blocks - 1) * gap_frac) / n_blocks
    # ... 生成 n 个 region，坐标全部为 fraction
```

Recipe factory 接收 `DesignTokens`，输出的 `LayoutRecipe` 中所有 `Region` 坐标已经是 fraction。`SlideRenderer` 只需调用 `region.to_absolute(tokens.slide_width, tokens.slide_height)` 转换为 inches 即可。

**Token 来源优先级：**

1. 用户上传的模板 PPTX → 提取主题色/字体 → `TemplateTokens`
2. 内置预设主题 → `PresetTokens`（如 "general", "minimal", "academic"）
3. 硬编码默认值 → `DefaultTokens`（保证永远不出现白底黑字 fallback）

新增 `design_tokens.py`，提供 `extract_design_tokens_from_presentation(prs) → DesignTokens`。`TemplateProfile` 继续负责 role/profile 结果，不持有 `Presentation` 对象，也不承载 token 提取副作用。

**Token 提取策略（两层）：**

1. **Theme XML 提取**：从 `theme.xml` 读取 `<a:clrScheme>` 和 `<a:fontScheme>`，映射到 DesignTokens。这是主要的结构化提取路径。
2. **Shape 采样提取**（补充）：实际 PPTX 模板大量使用 shape 级别的直接颜色而非 theme color 引用。遍历模板所有 slide（上限 10 个），过滤面积 < 1 平方英寸的 shape（图标、装饰点），统计剩余 shape 实际使用的填充色和字体色频率（按 shape 面积加权）。字体同理——采样 shape 中实际使用的字体名和字号。

**颜色频率 → Token 角色映射 heuristic：**

| 排名 | 映射目标 | 理由 |
|---|---|---|
| 频率最高的深色（HSL lightness < 40%） | `primary` | 大面积深色通常是品牌主色 |
| 频率最高的浅色（HSL lightness > 80%） | `light_bg` | 大面积浅色通常是背景 |
| 频率第二高的深色 | `accent` | 次要深色用作强调 |
| 频率第二高的浅色 | `light_bg_alt` | 次要浅色用作卡片交替背景 |
| 字体中频率最高的深色 | `text_primary` | 最常用字体颜色 |
| 字体中频率第二高的深色 | `text_secondary` | 次要字体颜色 |

如果模板 slide 数量 < 3，采样数据不足以可靠统计，跳过 shape 采样层，完全依赖 theme.xml 提取 + 硬编码默认值。

两层结果合并时，theme.xml 的显式定义优先，采样数据用于填补空缺。

### 2. 增强版语义模型

在现有 `semantic.py` 基础上扩展：

```python
class SlideKind(str, Enum):
    COVER = "cover"
    AGENDA = "agenda"
    SECTION_COVER = "section_cover"
    CONTENT_POINTS = "content_points"
    COMPARISON = "comparison"       # 新增：左右对照
    PROCESS = "process"             # 新增：步骤流程
    TIMELINE = "timeline"           # 新增：时间线
    DATA_TABLE = "data_table"
    DATA_CHART = "data_chart"
    CLOSING = "closing"

class BlockKind(str, Enum):
    TITLE = "title"
    SUBTITLE = "subtitle"
    POINT = "point"           # 涵盖 bullet list 和 numbered list；通过 SlideKind.PROCESS 区分步骤
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
    estimated_text_length: int      # 字符数（len(text)），在 build_content_slide_spec 时确定性计算

    # 图片/图标资源提示（可选）—— 只表达"需要什么"，不表达"放在哪"
    image_prompt: str | None = None   # 非空表示该 block 需要配图，值为生成 prompt
    icon_query: str | None = None     # 非空表示该 block 需要图标，值为搜索 query

    # NOTE: 行数估算（estimated_line_count）不放在 BlockSpec 中。
    # 行数依赖 region 宽度和字号，这些参数在 LayoutSelector 阶段尚未确定（鸡生蛋问题）。
    # LayoutSelector 的 variant 选择只基于 estimated_text_length 阈值：
    #   短内容（< 200 字符/block）→ grid cards，长内容（>= 200 字符/block）→ stacked
    # 行数估算推迟到 SlideRenderer 阶段，在已知 region 宽度和字号后按需计算。

@dataclass(frozen=True)
class SlideSpec:
    kind: SlideKind
    title: str
    source_level: int
    blocks: tuple[BlockSpec, ...]

    # 新增：供 LayoutSelector 使用的聚合指标
    @property
    def total_text_length(self) -> int: ...
    @property
    def block_kinds(self) -> frozenset[BlockKind]: ...
    @property
    def has_data(self) -> bool: ...
```

`BlockSpec` 的边界必须保持干净：它只描述内容语义和密度，不保存颜色、坐标、XML、shape 类型、z-layer 或具体视觉样式。所有从旧 `shapes.json` 迁移来的视觉信息都进入 `LayoutRecipe`（装饰元素存为 `DECORATION` region）。

**Slide kind 推断规则（Markdown → SlideSpec 阶段）：**

- 在 `ChapterSlideGroup.slides` 的单个内容 `Heading` 中检测到恰好两个同级子标题 → `COMPARISON`。自动推断仅覆盖最明显的情况；对于"优缺点对比"等非对称结构，推荐用户使用显式 hint `<!-- slide: comparison -->` 触发
- 显式 Markdown hint `<!-- slide: comparison -->` 可覆盖自动推断，是 COMPARISON 的首选触发方式
- 检测到编号列表（`1.`, `2.`, `3.` 或 `第一步`、`第二步`）→ `PROCESS`
- 检测到年份/日期模式（`2020年`、`第一阶段`、`Q1`）→ `TIMELINE`
- 检测到 Markdown table → `DATA_TABLE`
- `IMAGE_TEXT` 不通过 Markdown 自动推断，仅由显式 Markdown hint（如 `<!-- slide: image_text -->`）触发
- 默认 → `CONTENT_POINTS`

### 3. LayoutSelector（新增）

```python
class LayoutSelector:
    """Deterministic layout selection based on content semantics.

    Selection is purely semantic — no DesignTokens dependency.
    Tokens belong in the Renderer, not the Selector.
    """

    def select(self, spec: SlideSpec) -> LayoutRecipe:
        """Choose a recipe based on slide kind, block kinds, and content density."""
        # 按优先级匹配：
        # 1. slide kind → recipe family
        # 2. block count + estimated text length → recipe variant
        # 3. has_data → special data recipe
        ...
```

**选择逻辑的关键规则：**

- **同 slide kind + 同 recipe family**：保证视觉一致性
- **内容密度决定 variant**：4 个短 point → 2x2 卡片网格；2 个长 point → 上下堆叠
- **确定性优先**：默认不随机。随机变体仅在 `style_variant: "random"` 时用于装饰层（颜色变体、图标风格）
- **不支持的组合** → fallback 到 `TitleBodyRecipe` + warning 日志

### 4. LayoutRecipe（新增）

```python
@dataclass(frozen=True)
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
    """A rectangular area on the slide canvas.

    Coordinates are expressed as fractions of slide dimensions (0.0–1.0)
    so recipes adapt to any canvas size (16:9, 4:3, custom).

    Call to_absolute(slide_w, slide_h) to convert to inches at render time.

    When role is DECORATION, the optional decoration_* fields tell SlideRenderer
    what shape to draw and which token colors to use for fill/line. For content
    roles (TITLE, BODY, CARD, etc.), these fields are ignored.
    """

    region_id: str              # unique within the recipe, referenced by region_roles
    x_frac: float               # fraction of slide width from left
    y_frac: float               # fraction of slide height from top
    w_frac: float               # fraction of slide width
    h_frac: float               # fraction of slide height
    z_layer: int = 10           # 固定分层: 0=bg, 10=content, 20=decoration, 30=fg
                                # 同层内顺序由 region 在 LayoutRecipe.regions 元组中的索引决定

    # Decoration rendering hints — only meaningful when region role is DECORATION
    decoration_shape: str | None = None   # "rounded_rect", "rect", "ellipse", "line"
    fill_role: str | None = None          # token color role for fill (e.g. "primary", "accent")
    line_role: str | None = None          # token color role for border/line
    opacity: float = 1.0

    def to_absolute(self, slide_w: float, slide_h: float) -> tuple[float, float, float, float]:
        return (self.x_frac * slide_w, self.y_frac * slide_h,
                self.w_frac * slide_w, self.h_frac * slide_h)

@dataclass(frozen=True)
class LayoutRecipe:
    """Describes regions, typography, spacing, and rendering rules for one slide."""
    name: str
    regions: tuple[Region, ...]
    region_roles: dict[str, RegionRole]    # region_id → RegionRole
    supported_block_kinds: frozenset[BlockKind]

    # 供测试和文档使用
    @property
    def max_blocks(self) -> int: ...

    @property
    def region_ids(self) -> frozenset[str]:
        return frozenset(r.region_id for r in self.regions)
```

**装饰和内容用统一的 Region 表达。**

旧 `VisualPrimitive` 概念（装饰形状的位置、颜色、线型）已合并到 `Region` 中。当 `RegionRole = DECORATION` 时，`Region` 上的 `decoration_shape` / `fill_role` / `line_role` / `opacity` 字段告诉 `SlideRenderer` 如何渲染装饰形状；当角色为内容类型（`TITLE`、`BODY`、`CARD` 等）时这些字段被忽略。

这样避免了 Region 和 VisualPrimitive 两套位置系统的协调问题——所有区域（不管是放内容还是画装饰）都在同一个 `LayoutRecipe.regions` 列表里，由 `region_roles` 字典区分用途。

旧 `shapes.json` 的 `content_type` 映射规则：

| 旧字段 | 新位置 |
|---|---|
| `title` | `RegionRole.TITLE` |
| `content` | `RegionRole.BODY` / `RegionRole.CARD_BODY` |
| `number` | `RegionRole.INDEX` |
| `icon` / `picture` | `RegionRole.ICON` / `RegionRole.IMAGE` |
| `None` | `RegionRole.DECORATION` region |

**首批 Recipe（按优先级，只包含 6 个核心 Recipe）：**

| Recipe | 适用场景 | 区域 |
|---|---|---|
| `TitleBodyRecipe` | 标题 + 正文段落 | title + body |
| `GridCardsRecipe` | 多 point 短内容 | title + N 个等大卡片（2x2, 2x3, 3x2 自适应） |
| `TwoColumnRecipe` | 对比、左右栏、COMPARISON | title + left column + right column |
| `CoverRecipe` | 封面 | title + subtitle + 装饰卡 |
| `AgendaRecipe` | 目录 | N 等分横向卡片 + 编号 |
| `ClosingRecipe` | 结束页 | 居中感谢文字 + 装饰元素 |

`ProcessRecipe`、`TimelineRecipe`、`DataFullBleedRecipe` 留在后续 PR 实现。
`ComparisonRecipe` 是 `TwoColumnRecipe` 的特化变体（左右 panel 各自包含 title+body），合并到 TwoColumnRecipe 中。

每个 Recipe 的实现是一段使用 `python-pptx` 原生 API 的代码，**不再拼接 XML 字符串**。

### 4.1 默认 Recipe 样式库（从 shapes.json 迁移）

现有 `components/shapes/shapes.json` 不直接删除。它先作为迁移输入，抽取成代码内置的默认样式库，例如：

```text
slidegen/services/presentation/default_recipes.py
  - classic_one_point()
  - classic_two_points_numbered()
  - classic_two_points_icon_cards()
  - classic_three_points_numbered()
```

迁移规则：

1. 读取旧 layout/style 的 `location`、`zorder`（对应新架构 `z_layer`）、`content_type`。
2. 将 `content_type` 转成 recipe region role。
3. 对 XML 中可稳定解析的颜色、线条、形状类型、圆角等信息，转成 `RegionRole.DECORATION` 的 region（设置 `decoration_shape`、`fill_role`、`line_role`）。
4. 对复杂自由多边形、不可稳定解析的 XML 片段，先降级为简单 decoration region（如纯色矩形），或者记录在迁移报告中暂不迁入。
5. 新运行时不再读取 `shapes.json`，也不再复制 XML。`shapes.json` 后续只作为 fixture、迁移源或历史归档保留。

**迁移脚本的 Pass/Skip 判定规则：**

| 判定 | XML 特征 | 迁移产出 |
|---|---|---|
| **Pass** | `<a:solidFill>` 纯色填充 + `<a:prstGeom>` 标准几何形状（rect, roundRect, ellipse, line） | `DECORATION` region，保留 fill_role/line_role/decoration_shape |
| **Pass** | 纯色线条（`<a:ln>` 含 `<a:solidFill>`，无 `<a:custDash>`） | `DECORATION` region，decoration_shape="line" |
| **Skip** | `<a:custGeom>`（自由曲线/多边形） | 记入迁移报告，标记 "custom geometry — skip" |
| **Skip** | `<a:gradFill>`（渐变填充） | 记入迁移报告，标记 "gradient fill — skip" |
| **Skip** | `<a:blipFill>`（图片填充） | 记入迁移报告，标记 "image fill — skip" |
| **Skip** | `<a:effectLst>` 含阴影/发光等复杂效果 | 记入迁移报告，标记 "complex effect — skip" |

迁移报告格式为 JSON 文件（`migration_report.json`），每条记录包含 `layout_name`、`style_name`、`shape_name`、`status`（pass/skip）、`reason`。

这样既保留当前模板中已有的一部分视觉经验，又避免新管线继续绑定难调试的 PowerPoint XML。

Recipe 的关键设计原则（来自 JS 代码分析的启发）：

- **大结构先定边界，小结构只在边界内活动**（先划大区，再在区内加对象）
- **坐标用固定 gap 计算，不是自动流式排版**（`cardW * n + gap * (n-1)` 不超过页宽就天然不碰撞）
- **每个 Recipe 暴露 expected_regions 和 supported_block_kinds**，方便测试

### 4.5 z-layer 编排策略

z-layer 决定 shape 的前后遮挡关系，采用**固定分层 + Recipe 内置默认值**的确定性方案：

**宏观分层（固定规则）：**

| z_layer 范围 | 用途 | 示例 |
|---|---|---|
| 0 | 背景色块 | 全页底色、section 背景 |
| 10 | 内容 | 标题、正文、卡片 |
| 20 | 装饰 | 色条、分割线、边框 |
| 30 | 前景/页脚 | 页码、来源注释 |

**同层内排序规则（确定性）：**

同一 z_layer 内多个 region 的渲染顺序由其在 `LayoutRecipe.regions` 元组中的索引决定（先定义的先渲染，后定义的覆盖在上方）。这意味着：

- Recipe 作者通过 region 定义顺序显式控制同层遮挡关系
- 不需要运行时动态决策
- 对于 6 个核心 Recipe 的简单布局（title + body / grid cards / two columns），同层内的 region 不存在有意义的遮挡，顺序影响可忽略

**每个 Recipe 的 DECORATION region 带有内置的默认 z_layer 值**（在 Recipe factory 函数中硬编码）。例如 `CoverRecipe` 的装饰色条固定在 z_layer=20，确保覆盖在背景之上、文本之下。

### 4.6 Future Phase: AI Visual Composer（z-layer 编排与视觉微调）

> **此节描述的是 Phase 3 之后的增强方向，不在当前迁移范围内。**

当基础管线稳定后（Phase 1-3 完成），可引入 AI Agent 对复杂 slide 做 z-layer 编排和装饰层微调：

- **触发条件：** 复杂 slide（多 card 叠加、带 hero image 的封面）中，确定性默认 z_layer 无法满足视觉需求
- **Agent 输入：** SlideSpec + DesignTokens + LayoutRecipe skeleton
- **Agent 输出：** 调整后的 LayoutRecipe（z_layer 微调 + 可选的额外 DECORATION region）
- **Fallback：** Agent 超时或失败时，使用 Recipe 的确定性默认值

**前置条件（进入此 Phase 前必须满足）：**
1. 6 个核心 Recipe 用确定性默认值产出的 PPTX 通过 PostRenderValidator 检查
2. 在 >= 10 个真实 Markdown 输入上验证基础管线的视觉质量可接受
3. 定义 Agent 的 prompt schema、输出 JSON schema、延迟/成本预算

当前 `NativePage` 是白底黑字。升级后它变成一个完整的 Renderer：

### 5. SlideRenderer（新增）

```python
class SlideRenderer:
    """Render a LayoutRecipe onto a slide using python-pptx native APIs."""

    def __init__(self, tokens: DesignTokens):
        self.tokens = tokens

    def render(
        self,
        slide: Slide,
        recipe: LayoutRecipe,
        spec: SlideSpec,
    ) -> None:
        """Render all blocks into the recipe's regions."""
        ...
```

**渲染规则：**

1. **背景层（z_layer=0）**：根据 region role 填充 `tokens.light_bg` / `tokens.primary` 底色
2. **装饰层（z_layer=20）**：按 `DECORATION` region 渲染色条、分割线、圆角矩形边框
3. **文本层（z_layer=10）**：标题、正文、标签，字号/颜色从 tokens 取
4. **内容层（z_layer=10）**：卡片、bullet list、图片占位等（同层内按 region 定义顺序写入）
5. **页脚层（z_layer=30）**：统一页码 + 来源/注释

**线条/装饰处理：**
- 装饰性线条和色条用 `slide.shapes.add_shape()` 原生 API 渲染 `DECORATION` region
- 不使用 `shapes.json` 中的 XML 片段；旧 XML 只能作为迁移时解析输入
- 线条 region 的包围盒不与内容区重叠（或重叠可忽略），避免误导 QA 检查

### 6. Post-Render Validator（新增）

参考那份 JS 代码的 `warnIfSlideHasOverlaps` 和 `warnIfSlideElementsOutOfBounds`，在导出前增加几何 QA。

```python
@dataclass
class SlideGeometryIssue:
    level: Literal["error", "warning"]
    slide_index: int
    message: str
    shapes_involved: tuple[str, ...]

class PostRenderValidator:
    """Validate slide geometry after rendering, before export."""

    def validate(self, prs: Presentation) -> list[SlideGeometryIssue]:
        issues: list[SlideGeometryIssue] = []

        for i, slide in enumerate(prs.slides):
            issues.extend(self._check_overlaps(slide, i))
            issues.extend(self._check_out_of_bounds(slide, i))
            issues.extend(self._check_readability(slide, i))

        return issues

    def _check_overlaps(self, slide: Slide, index: int) -> list[SlideGeometryIssue]:
        """两两比较所有 shape 的边界盒，检测严重重叠。
        忽略：线条之间、装饰条与文本的轻微重叠、斜线的包围盒误判。"""
        ...

    def _check_out_of_bounds(self, slide: Slide, index: int) -> list[SlideGeometryIssue]:
        """检测任何 shape 的边界超出页面的情况。"""
        ...

    def _check_readability(self, slide: Slide, index: int) -> list[SlideGeometryIssue]:
        """检测字体是否小于 8pt（不可读）。"""
        ...
```

**关键设计点：**

- 重叠检测的工程难度高：python-pptx shape 的包围盒包含不可见的 padding 和文本边距，两个视觉上不重叠的 textbox 其 bounding box 可能大量重叠。**Phase 1 只做越界检测和字体大小检测**（几乎没有 false positive）。重叠检测标记为 **experimental/warn-only**，需要在一组真实 PPTX 上验证 false positive 率后再决定是否提升到 error。
- 线条（line shape）默认忽略，因为分割线的包围盒天然会"压到"别的元素
- group shape 中的子 shape 坐标为相对坐标，需要特殊处理转换为页面绝对坐标
- 越界 → `error` 级别
- 字体过小（< 8pt）→ `warning` 级别
- validator 支持 `off` / `warn` / `fail` 模式。Phase 1 默认 `warn`；Phase 2 对新主路径的越界检测提升到 `fail`，重叠检测保持 `warn`
- **重叠检测毕业标准：** 在 >= 20 个真实生产 PPTX 上运行，false positive rate < 5% 时，可从 `warn` 提升到 `error` 级别。Phase 2 结束前完成评估，评估结果记入 PR 描述

### 7. 模板 PPTX 的新角色

模板 PPTX 不再是"提供 shape 结构"的角色，而是"提供视觉 DNA"的角色：

- **配色提取**：从 `theme.xml` 读取 `<a:clrScheme>` 映射到 DesignTokens
- **字体提取**：从 `theme.xml` 读取 `<a:fontScheme>` 映射到 DesignTokens
- **Role 检测**：保留现有 `TemplateProfile` 的 slide role 检测逻辑，但 role assignment 不再等同于 legacy XML renderer 可用性
- **装饰参考**：模板中的装饰性 shape（色条、圆角矩形边框）的颜色/尺寸参数可被提取为 token，但不复制 XML

这样用户上传一个品牌模板后，生成的 PPT 会自动继承品牌配色和字体，而不会因为模板的 shape 结构限制内容的呈现方式。

### 8. Asset Provider（图片/图标依赖注入）

当前 `ChapterContentPage` 持有 `ImageGenerator` 和 `IconSearcher` 类属性。新架构中，图片和图标的生产逻辑通过依赖注入解耦：

```python
class AssetProvider:
    """Interface for image generation and icon search, injected into SlideRenderer."""

    async def get_image(self, prompt: str, width: int, height: int) -> str | None: ...
    async def get_icon(self, query: str) -> str | None: ...

class DefaultAssetProvider(AssetProvider):
    def __init__(self, image_generator: ImageGenerator, icon_searcher: IconSearcher): ...
```

`SlideRenderer` 只依赖 `AssetProvider` 接口，不直接依赖 `ImageGenerator`。对于不需要图片的 recipe，`AssetProvider` 可以是 `None`。

### 9. 图片和图标的插入流程

与旧架构的关键区别：旧架构中图片/图标的位置由 `shapes.json` 中提取的 shape `location` 字段预先决定；新架构中**位置由 Recipe 的 region 定义，插入决策由 BlockSpec 的 asset 字段驱动**。

**决策链：**

```
BlockSpec.image_prompt / .icon_query  (WHAT — 是否需要图片/图标)
    ↓
LayoutRecipe.regions[role=IMAGE/ICON]  (WHERE — 图片/图标放在哪个区域)
    ↓
SlideRenderer._render_block()           (HOW — 调用 AssetProvider 获取资源，插入到对应 region)
```

**具体流程（以 `GridCardsRecipe` 为例）：**

1. `GridCardsRecipe` 定义每个 card 包含两个子 region：
   - `region_id="card_0_icon"`, `role=ICON`（左上角小图标区）
   - `region_id="card_0_body"`, `role=CARD_BODY`（文本区）

2. `build_content_slide_spec()` 从 Markdown 构建 `BlockSpec` 时，根据内容的子元素判断是否需要图片/图标：
   ```python
   # Markdown 中的图片语法 → image_prompt
   # ![alt](image-url)  → BlockSpec(..., image_prompt="...")
   # 或者对每个 POINT block 自动设置 icon_query=block.title
   ```

3. `SlideRenderer._render_card()` 遍历 card 的子 region 时：
   - 遇到 `role=ICON` 的 region → 调用 `AssetProvider.get_icon(block.icon_query)` → `slide.shapes.add_picture()`
   - 遇到 `role=CARD_BODY` 的 region → 写入 `block.text`
   - 遇到 `role=IMAGE` 的 region → 调用 `AssetProvider.get_image(block.image_prompt)` → `slide.shapes.add_picture()`

4. 如果 block 没有 `icon_query` / `image_prompt`，对应 region 留空（或使用该 region 的默认背景色填充），不影响其他 region。

**`BlockSpec` 的 asset 字段来源（Markdown → BlockSpec 推断）：**

hint 是 **block 级别**的，不是 slide 级别。每个 `###` 子标题下的 `<!-- icon: xxx -->` 只作用于当前 block：

```markdown
## 市场分析                           → SlideSpec(CONTENT_POINTS, blocks=3)

### 用户增长                          → BlockSpec(icon_query="chart-up")
<!-- icon: chart-up -->
过去三年用户量增长了 300%...

### 收入趋势                          → BlockSpec(icon_query="dollar")
<!-- icon: dollar -->
营收同比增长 45%...

### 竞品对比                          → BlockSpec(icon_query="vs")
<!-- icon: vs -->
我们的市场份额领先第二名 15%...
```

**N 个 block → N 个 icon region 的对应关系：** Recipe（如 `GridCardsRecipe`）为每个 block 分配一个 `role=ICON` 的 region，Renderer 按 `block[0] → card_0_icon region, block[1] → card_1_icon region, ...` 顺序一一渲染。

| Markdown 特征 | 作用范围 | 映射 |
|---|---|---|
| `### 标题` | 一个 POINT block | `BlockSpec.title = "标题"` |
| `<!-- icon: query -->`（紧跟在 `###` 行之后） | 当前 block | `BlockSpec.icon_query = "query"` |
| `![alt](image-url)`（block 内的子元素） | 当前 block | `BlockSpec.image_prompt = alt` |
| 无 hint 的 POINT block | 当前 block | `BlockSpec.icon_query = block.title`（默认用标题搜图标） |
| 无 hint 的纯文本 block | 当前 block | `icon_query` 和 `image_prompt` 均为 `None` |

**与旧架构的对比：**

| 旧架构 | 新架构 |
|---|---|
| shapes.json 中 picture shape 的 location → 图片位置 | Recipe 中 `role=IMAGE/ICON` 的 region → 图片位置 |
| shapes.json 中 shape 的 content_type → 是否插入图片 | `BlockSpec.image_prompt / icon_query` → 是否插入图片 |
| 随机 style 决定图片/图标的视觉风格 | `DECORATION` region 决定图片/图标的边框、圆角等装饰 |
| 图片 prompt 来自 title 的前 20 个字符 | 图片 prompt 来自 Markdown alt text 或完整的 block title |

### 10. 页码和页脚

`SlideRenderer` 在渲染流程的最后一步（footer 层，z_layer=30）统一添加页码和来源/注释：

- 每个 `LayoutRecipe` 的 `regions` 中预留一个 `RegionRole.FOOTER` region（如果该 slide kind 需要页脚）
- `SlideRenderer.render()` 在所有内容渲染完成后，检查 recipe 是否有 footer region，有则写入页码
- 页码格式由 `DesignTokens` 的 `caption_font` / `caption_size` 控制

### 11. 模板 PPTX slide 清理策略

旧架构中，`converter.py._cleanup_template_slides()` 删除未被复用的模板页。新架构下：
- 模板 PPTX 只用于提取 DesignTokens，提取完成后可丢弃
- 所有 slide 基于 blank layout（`prs.slide_layouts[6]`）全新生成
- 不再需要 `_cleanup_template_slides`、`reused_template_slide_ids`、`current_template_index` 等逻辑
- `PresentationRenderPlan` 中的 `chapter_home_template_index`、`chapter_content_template_index`、`end_template_index`、`cleanup_template_indexes` 全部移除

## Migration Strategy

### Phase 1a: 建立数据模型层（不改变渲染路径）

1. 实现 `DesignTokens` + 默认 token set（`DefaultTokens`、`PresetTokens`）
2. 新增 `extract_design_tokens_from_presentation(prs)`（两层提取：theme.xml + shape 采样）
3. 增强 `SlideSpec` / `BlockSpec`（新 SlideKind/BlockKind 值 + `estimated_text_length`）
4. 扩展 `build_content_slide_spec()` 的 slide kind 推断逻辑（COMPARISON / PROCESS / TIMELINE / DATA_TABLE / CONTENT_POINTS）
5. 实现 `LayoutSelector` skeleton（纯语义选择，不依赖 DesignTokens）
6. 测试：semantic model 测试、slide kind 推断测试、LayoutSelector 确定性测试

**Phase 1a 完成标志：**
- 所有新 `SlideKind` / `BlockKind` 值已定义
- `BlockSpec` 中没有 XML、坐标、颜色等视觉字段
- Markdown → SlideSpec 推断有单元测试覆盖
- 现有渲染路径行为不变

### Phase 1b: 建立最小渲染闭环 + 样式迁移工具

1. 实现 `Region`、`RegionRole`、`LayoutRecipe` 数据类（`Region` 含 `decoration_shape` 等装饰字段）
2. 实现 `TitleBodyRecipe` + `GridCardsRecipe` + `TwoColumnRecipe`（首批核心 recipe）
3. 实现 `SlideRenderer`（基于 `python-pptx` 原生 API 渲染 title/body/card/primitive）
4. 新增一次性 `shapes.json → default_recipes.py` 迁移脚本（只处理可稳定解析的形状：纯色填充矩形、纯色线条→`DECORATION` region；复杂形状在迁移报告中标记为 skipped）
5. 实现 `PostRenderValidator`，越界检测 + 字体检测，重叠检测 experimental/warn-only，默认 `warn` 模式
6. 保留 feature flag `enable_recipe_renderer`（环境变量或 config），默认 `False`，用于切换新主路径验证
7. 测试：Recipe 快照测试、SlideRenderer 输出验证、PostRenderValidator 单元测试

**Phase 1b 完成标志：**
- 新 renderer 能独立生成包含 title + body + cards 的可读 PPTX
- **提供独立的集成测试**：直接走 `SlideSpec → LayoutSelector → SlideRenderer → PPTX 文件` 全链路（跳过 `MarkdownToPresentation`），验证产出的 PPTX 通过 `PostRenderValidator` 检查且可被 python-pptx 正常读取
- `PostRenderValidator` 可以对产出做越界和字体检查
- `shapes.json` 中可解析的样式已经转换成 `DECORATION` region
- 新路径通过 feature flag 隔离，默认不启用
- feature flag `enable_recipe_renderer` 的接入点已在 `converter.py` 中预埋（至少对 content page 可切换），但默认 `False`

### Phase 2: 切换到新主渲染管线并删除旧内容页 renderer

1. 实现 `CoverRecipe` / `AgendaRecipe` / `ClosingRecipe`（补齐所有页面类型的 recipe 覆盖）
2. 实现 `AssetProvider` 接口，将 `ImageGenerator` 和 `IconSearcher` 从 `ChapterContentPage` 迁移为注入依赖
3. 将 `NativeCoverPage`、`NativeChapterContentPage` 等全部替换为基于 `LayoutSelector → SlideRenderer` 的实现
4. `MarkdownToPresentation.generate()` 统一走新路径：`profile template → extract tokens → build SlideSpecs → LayoutSelector → SlideRenderer → PostRenderValidator`
5. `PresentationRenderPlan` 移除 `use_native_*` flag，只做 slide index 计算
6. 删除 `ChapterContentPage` 的 XML-copy 调用链
7. 模板 PPTX 不再被 clone slide，只用于提取 DesignTokens；所有 slide 基于 blank layout 全新生成
8. `PostRenderValidator` 越界检测对新主路径提升到 `fail` 模式

**Phase 2 完成标志：**
- 无模板 PPTX 时（纯 native 路径），产出视觉统一、配色合理的 PPT
- 有模板 PPTX 时，Design Token 从模板提取，产出继承品牌风格的 PPT
- 所有 6 个核心 Recipe 通过 `PostRenderValidator` 检查
- `PresentationRenderPlan` 不再有 `use_native_*` flag
- 运行时不再读取 `components/shapes/shapes.json`

### Phase 3: 清理旧代码和历史资产

1. 删除 `components.py`
2. 将 `components/shapes/shapes.json` 移入测试 fixture 或归档目录，或在确认不再需要后删除
3. 删除 `pages.py` 中的 `ChapterContentPage` 及 Page base class 中的 XML 操作辅助方法
4. 删除 `CoverPage`、`CatalogPage`、`ChapterHomePage`、`EndPage` 的全部 XML-copy 实现
5. 删除 `utils/slide.py` 中的 `add_shape_by_xml`、`add_para_by_xml`、`convert_paragraph_xml`、`runs_merge` 等
6. 清理 `template_profile.py` 中的 `_supports_legacy_renderer`
7. `PresentationRenderPlan` 移除 `cleanup_template_indexes` 等旧模板清理相关逻辑
8. 删除 `native_pages.py`（已被 `SlideRenderer` 完全取代）
9. 移除 feature flag `enable_recipe_renderer`（新路径成为唯一路径）

**Phase 3 完成标志：**
- 所有测试通过（更新后的测试）
- 运行时代码不再引用 `shapes.json`
- 默认样式由 `default_recipes.py` 提供（装饰元素以 `DECORATION` region 形式内嵌在 recipe 中）
- 代码库减少约 800-1000 行

## Compatibility Rules

- API 路由签名不变
- `PresentationGenerator.generate_markdown_to_pptx()` 返回值不变
- 现有 Markdown 输入（无特殊标记）仍产出合法 PPTX
- 用户上传的模板 PPTX 仍可被读取和利用（配色/字体提取）
- 运行时不再依赖 `shapes.json` 的存在
- 旧 `shapes.json` 只能作为迁移输入、fixture 或历史归档，不参与生产渲染
- **性能基线：** 端到端生成时间（无图片/图标生成）不超过当前基线的 2x。Phase 2 集成测试中加入耗时断言，基线值从 Phase 1a 开始前测量并记录

## Risks

- **新 Renderer 初期产出可能不如精心设计的模板好看。** 通过 Design Token 从模板提取配色和字体来缓解。装饰性细节（阴影、渐变）可能需要额外迭代。
- **`post_render_validator` 的重叠检测可能产生大量 false positive。** python-pptx shape 包围盒包含不可见的 padding/边距。Phase 1 只做越界和字体检测，重叠检测保持 experimental/warn-only，在真实 PPTX 上验证后再决定是否提升级别。
- **从 `shapes.json` 迁移出的装饰元素可能丢失复杂视觉细节。** 对复杂 XML 先降级为简单 `DECORATION` region 或跳过，用迁移报告列出差异，避免为了追求还原度把 XML-copy 带回主路径。
- **删除运行时 `shapes.json` 依赖可能影响内部测试或脚本。** Phase 3 前需要 codebase 搜索确认无运行时引用，并把必要样例转入 fixture。
- **LayoutSelector 的推断规则可能不完美。** 初期保持保守（大部分 Markdown → `CONTENT_POINTS`），逐步增加推断规则，并给用户提供 Markdown hint 语法（如 `<!-- slide: comparison -->`）来显式指定 slide kind。
- **相对坐标系统可能引入浮点精度问题。** `x_frac` 等 0.0~1.0 的小数在转换为 inches 时可能产生亚像素偏差。`SlideRenderer` 在渲染时对坐标做 `round(x, 2)` 英寸精度处理。
- **Shape 采样提取 token 可能被模板中的 outlier shape 误导。** 采样时按面积加权，过滤面积 < 1 平方英寸的 shape（图标、装饰点）。模板 slide 数量 < 3 时跳过 shape 采样，完全依赖 theme.xml + 默认值。颜色 → token 角色映射使用 HSL lightness 启发式规则（详见 §1 Token 提取策略）。

## Testing Plan

### 语义模型测试

- 验证单个内容 `Heading` 下两个同级子标题 → `COMPARISON` slide kind
- 验证 Markdown 编号列表 → `PROCESS` slide kind
- 验证 Markdown table → `DATA_TABLE` slide kind
- 验证 `BlockSpec.estimated_text_length` 正确估算
- 验证未知模式 → `CONTENT_POINTS` fallback

### LayoutSelector 测试

- 验证相同 SlideSpec 产生相同 Recipe（确定性）
- 验证 4 个短 point → grid variant，2 个长 point → stacked variant
- 验证不支持的组合 → fallback recipe
- 验证从旧 `one_point/two_points/three_points` 迁移来的 classic recipes 可被确定性选择

### Renderer 测试

- 验证 `TitleBodyRecipe` 渲染后在 slide 上产生正确数量的 shapes
- 验证文本内容正确写入 text frame
- 验证颜色/字体来自 DesignTokens
- 验证 `DECORATION` region 通过 native `python-pptx` API 渲染，而不是复制 XML

### 快照测试（结构化输出验证）

- 为每个 Recipe 的渲染输出建立 shape count + position 快照（结构化数据，非像素截图）
- 快照内容：`[(shape_type, left, top, width, height) for shape in slide.shapes]`
- 快照作为 test fixture 入库，后续 recipe 修改可检测到意外的 shape 变更
- 验证从旧 `one_point/two_points/three_points` 迁移来的 classic recipes 产出的 shape 数量合理

### 兼容性测试

- 取生产环境中真实使用的 Markdown 输入样本，在新旧两条路径上分别生成 PPTX
- 比较 slide 数量、基本结构是否一致（不要求像素级等价）

### Post-Render Validator 测试

- 构造两个重叠的 textbox → 检测到 error
- 构造越界 shape → 检测到 error
- 构造 6pt 字体 → 检测到 warning
- 构造线条与文本轻微重叠 → 正确忽略
- 在现有 PPTX 上运行 → 发现现存问题（如有）

### 集成测试

- 完整 Markdown → PPTX 生成（无模板）→ 产出合法 PPTX，通过 validator
- 完整 Markdown → PPTX 生成（有模板）→ 产出继承品牌风格的 PPTX
- 新主渲染路径开启时 → 运行时不读取 `components/shapes/shapes.json`
- 旧 renderer 删除后 → Markdown → PPTX 仍通过 `LayoutSelector → SlideRenderer` 成功生成

## Recommended First Implementation Scope

### 第一个 PR（Phase 1a）：数据模型层

建立新管线的数据基础，不改变任何渲染行为：

1. `slidegen/services/presentation/design_tokens.py` — `DesignTokens` dataclass + 默认 token set（`DefaultTokens`、`PresetTokens`）+ `extract_design_tokens_from_presentation(prs)`（两层提取：theme.xml + shape 采样）
2. `slidegen/services/presentation/region.py` — `Region`、`RegionRole` 数据类（含 `decoration_shape` 等装饰渲染字段）
3. 增强 `semantic.py` — 新增 `SlideKind`/`BlockKind` 值 + `estimated_text_length` + slide kind 推断函数
4. `slidegen/services/presentation/layout_selector.py` — `LayoutSelector`（纯语义选择，不含 DesignTokens），先返回 recipe name（string），不依赖 recipe 实现
5. 测试：semantic model 测试、slide kind 推断测试、LayoutSelector 确定性测试

### 第二个 PR（Phase 1b）：最小渲染闭环

6. `slidegen/services/presentation/recipes.py` / `default_recipes.py` — `LayoutRecipe` 数据类 + 首批核心 Recipe（`TitleBodyRecipe`、`GridCardsRecipe`、`TwoColumnRecipe`）+ 从 `shapes.json` 迁移来的 `DECORATION` region 样式库
7. `slidegen/services/presentation/slide_renderer.py` — `SlideRenderer`（基于 `python-pptx` 原生 API 渲染 title/body/card/primitive）+ `AssetProvider` 接口 + `DefaultAssetProvider`
8. `slidegen/services/presentation/post_render_validator.py` — `PostRenderValidator`（越界检测 + 字体检测，重叠检测 experimental/warn-only，默认 warn 模式）
9. 一次性迁移脚本：`shapes.json` 的 `content_type/location/zorder`（对应 `z_layer`）映射到 recipe region（含 `DECORATION` region，只处理可稳定解析的形状）
10. 测试：Recipe 快照测试、SlideRenderer 输出验证、PostRenderValidator 单元测试

**`default_recipes.py` 和 `recipes.py` 的职责边界：**
- `recipes.py` → `LayoutRecipe` 数据类定义 + Recipe factory 函数接口
- `default_recipes.py` → 6 个核心 Recipe 的具体实现（工厂函数，如 `grid_cards_recipe(n_blocks, tokens)`）
- `region.py` → `Region`、`RegionRole` 等基础数据类（含 `decoration_shape` 等装饰渲染字段）

这两个 PR 不要求切走生产路径，但 Phase 1b 完成后必须证明新 renderer 能独立生成可用 PPTX。
