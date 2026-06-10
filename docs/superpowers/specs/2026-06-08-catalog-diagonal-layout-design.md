# 目录页斜向布局与 catalog_items 补位设计

**日期**: 2026-06-08
**状态**: 待实现
**作者**: Claude + wjs

## 问题描述

当前目录页生成逻辑对模板目录项数量和排列方向的处理还不够稳：

1. 当模板中存在 2 个及以上目录项时，代码能从编号形状判断大致的 `VERTICAL` / `HORIZONTAL`，但后续克隆时会根据枚举归零 `dx` 或 `dy` 的一个分量，导致斜向排列无法保持。
2. 当模板只有 1 个目录项时，代码只能从 number-text 相对位置启发式推断排列方向；如果这个单项位于页面中央，继续向下或向右克隆可能很快超出页面。
3. 当模板项太少时，当前逻辑会优先从已有模板项推断和克隆，但项目已经支持从 `shapes.json` 读取 `catalog_items`；这种更完整的模板库数据应该优先参与补位。
4. 当前 `_get_or_create_catalog_items()` 只在页面上完全没有目录项时使用 `shapes.json catalog_items` 或默认 fallback。新的需求是：目录页只有单项或已有项数量不足时，都应优先使用 `shapes.json` 中的 `catalog_items`；如果库数据不可用，再按当前项向量计算容量并分页克隆，避免单页溢出。

## 当前代码基线

相关实现集中在 `slidegen/services/presentation/pages.py` 的 `CatalogPage`：

- `_get_or_create_catalog_items()`：先从当前 slide 提取目录项；没有目录项时才使用 `shapes.json catalog_items`，再退回默认 fallback。
- `_create_catalog_items_from_library()`：从 `components_manager.get_catalog_items(template_name)` 加载 `shapes.json` 中的目录项模板。
- `_calculate_max_per_page()`：依赖 `layout_direction` 和 `_calculate_catalog_step()` 计算容量。
- `_calculate_catalog_step()`：只返回单轴步长。
- `_resolve_layout_direction()` / `_infer_single_item_layout_direction()`：用于判断垂直或水平布局。
- `generate_slide()`：当模板目录项少于内容数量时，克隆最后一个目录项，并根据 `CatalogLayout` 选择 `(0, step)` 或 `(step, 0)`。

当前已有测试覆盖：

- 单项模板可以扩展到同一页。
- 空白目录页使用默认 fallback。
- 空白目录页可使用 `shapes.json catalog_items`。
- 默认 fallback 是居中的目录组。
- 克隆 shape 保持唯一 id，且 background 位于 number/text 下方。

## 设计目标

1. **支持斜向布局**：当真实模板中有 2 个及以上目录项时，保留相邻目录项的完整 `(dx, dy)` 向量。
2. **优先使用模板库补位**：当当前目录页只有单项，或当前目录项数量不足以承载内容时，优先直接使用 `shapes.json` 中的 `catalog_items`；容量评估用于决定当前项 fallback 的分页边界，不作为独立触发条件重复建模。
3. **避免过度推断单项布局**：单项只作为最后 fallback 的克隆种子，不再作为优先路径。
4. **容量计算使用完整边界**：斜向布局容量必须同时检查水平和垂直边界，不能只按主导方向估算。
5. **保持现有 API 兼容**：`CatalogPage.generate_slide()` 签名不变，异常类型不扩大。

## 核心策略

目录项来源优先级调整为：

1. 先尝试从当前 slide 提取目录项。
2. 如果提取结果为空、只有单项，或数量少于 `catalog_num`，尝试从 `shapes.json catalog_items` 加载目录项。
3. 如果 `shapes.json catalog_items` 可用，先清理当前 slide 中已提取到的目录 shape，再使用库中的目录项替代当前提取结果，并把库项数量视为该页最大容量。
4. 如果库数据不可用，再使用当前提取结果。
5. 如果当前提取结果也为空，使用默认 fallback。

这样做的含义是：单项或项太少的模板不再优先依赖启发式克隆，而是优先相信已结构化保存的 `catalog_items`。一旦采用库项，库项仍不足以承载全部内容时直接分页，不再继续克隆库项。按当前项向量克隆后的 `projected_capacity` 仍然需要计算，但只用于库数据不可用时的 fallback 克隆和分页，不再作为单独的 library 触发分支。

## 详细设计

### 1. 目录项获取与补位

将 `_get_or_create_catalog_items()` 调整为数量感知逻辑，并让内部结果携带来源信息。`CatalogPage.generate_slide()` 的公共签名不变，但内部需要知道当前目录项是否来自 `shapes.json`，以决定是否允许继续克隆。

```python
@dataclass
class CatalogItemsResolution:
    items: CatalogList
    source: Literal["slide", "library", "default"]
    allow_clone: bool


@staticmethod
def _get_or_create_catalog_items(
    slide: Slide,
    target_count: int = 1,
    template_name: str | None = None,
) -> CatalogItemsResolution:
    extracted_items = CatalogList()
    try:
        extracted_items = CatalogPage._get_catalog_items(slide)
    except CatalogTemplateNotFoundError:
        pass

    should_use_library = len(extracted_items) <= 1 or len(extracted_items) < target_count
    if should_use_library:
        has_library_items = CatalogPage._has_catalog_items_in_library(template_name)
        if has_library_items:
            CatalogPage._remove_catalog_items(slide, extracted_items)
            library_items = CatalogPage._create_catalog_items_from_library(slide, template_name, target_count)
        else:
            library_items = CatalogList()
        if library_items:
            logger.info(
                "Catalog slide has {} extracted items; using shapes.json catalog items for {}",
                len(extracted_items),
                template_name,
            )
            return CatalogItemsResolution(
                items=library_items,
                source="library",
                allow_clone=False,
            )

    if extracted_items:
        return CatalogItemsResolution(
            items=extracted_items,
            source="slide",
            allow_clone=True,
        )

    logger.info("Catalog slide has no template items; creating default catalog item fallback")
    return CatalogItemsResolution(
        items=CatalogPage._create_default_catalog_items(slide, target_count),
        source="default",
        allow_clone=True,
    )
```

关键约束：

- 只要 `shapes.json catalog_items` 可用，单项和项太少的情况直接使用库数据。
- `template_name is None` 或 `components_manager.get_catalog_items(template_name)` 为空时，视为库数据不可用，继续走当前 slide 提取项或默认 fallback。
- 使用库数据替代当前 slide 提取项前，必须删除已提取目录项对应的 number/text/background shape，避免旧单项、旧少量项或递归分页复制出来的上一页内容残留。
- 不把当前 slide 提取项与库项混合，以免 z-order、样式和相对位置来自两套来源。
- `_create_catalog_items_from_library()` 继续按 `target_count` 和库中可用数量取最小值；如果库项仍少于内容数量，本页只填充库项数量，剩余内容递归分页。
- `source == "library"` 时 `allow_clone=False`，因为 `shapes.json` 中保存的 `catalog_items` 表示该模板在单页内可安全放置的最大目录项集合。
- 如果库数据不可用，才基于当前 slide 提取项计算 `projected_capacity` 并按容量分页克隆；此时 `projected_capacity` 是 fallback 容量上限，不是额外的 library 选择条件。
- 默认 fallback 仍保持当前“居中目录组”的语义，不受单项位置调整影响。

### 2. 向量化偏移计算

用 `_calculate_catalog_offset()` 替代 `_calculate_catalog_step()`，返回完整 `(dx, dy)`：

```python
@staticmethod
def _calculate_catalog_offset(catalog_items: CatalogList) -> tuple[int, int]:
    if len(catalog_items) >= 2:
        positions = [(item.number_shape["left"], item.number_shape["top"]) for item in catalog_items]
        avg_dx = sum(positions[i + 1][0] - positions[i][0] for i in range(len(positions) - 1)) / (
            len(positions) - 1
        )
        avg_dy = sum(positions[i + 1][1] - positions[i][1] for i in range(len(positions) - 1)) / (
            len(positions) - 1
        )
        return int(avg_dx), int(avg_dy)

    if len(catalog_items) == 1:
        item = catalog_items[0]
        direction = CatalogPage._infer_single_item_layout_direction(item)
        item_width, item_height = CatalogPage._catalog_item_size(item)
        if direction == CatalogLayout.VERTICAL:
            return 0, max(item_height + CATALOG_DEFAULT_ITEM_GAP_EMU, CATALOG_DEFAULT_ITEM_HEIGHT_EMU)
        return max(item_width + CATALOG_DEFAULT_ITEM_GAP_EMU, CATALOG_DEFAULT_NUMBER_WIDTH_EMU), 0

    return 0, 0
```

注意：

- 多项场景必须保留 `dx` 和 `dy` 的正负号，支持向右下、左下、右上、左上等方向。
- 单项场景仍只生成水平或垂直默认向量，因为单个 item 无法可靠推断斜向排列。
- 单项场景已经被 `shapes.json catalog_items` 优先路径覆盖；这里主要是库数据不可用时的 fallback。

### 3. 容量计算

`_calculate_max_per_page()` 移除 `layout_direction` 参数，改为使用完整向量和 item bounding box。该容量计算只用于 `resolution.allow_clone == True` 的路径；当目录项来自 `shapes.json catalog_items` 时，`len(catalog_items)` 就是当前页容量上限。

不能使用“主导方向”估算容量。斜向布局需要同时检查两个轴：

```python
@staticmethod
def _calculate_max_per_page(
    catalog_items: CatalogList,
    slide_height: int,
    slide_width: int,
) -> int:
    if not catalog_items:
        return 0

    dx_per_item, dy_per_item = CatalogPage._calculate_catalog_offset(catalog_items)
    if dx_per_item == 0 and dy_per_item == 0:
        return len(catalog_items)

    source_item = catalog_items[-1]
    item_bounds = CatalogPage._catalog_item_bounds(source_item)
    max_extra_by_x = CatalogPage._calculate_axis_capacity(
        start_min=item_bounds.left,
        start_max=item_bounds.right,
        step=dx_per_item,
        axis_size=slide_width,
    )
    max_extra_by_y = CatalogPage._calculate_axis_capacity(
        start_min=item_bounds.top,
        start_max=item_bounds.bottom,
        step=dy_per_item,
        axis_size=slide_height,
    )
    max_extra = min(max_extra_by_x, max_extra_by_y)
    return max(len(catalog_items), len(catalog_items) + max_extra)
```

`_calculate_axis_capacity()` 的规则：

- `step == 0` 时，该轴不限制容量，返回一个足够大的哨兵值。
- `step > 0` 时，使用 `axis_size - start_max` 计算还能向正方向移动多少次。
- `step < 0` 时，使用 `start_min` 计算还能向负方向移动多少次。
- 返回值表示在已有最后一个目录项之后还能额外克隆多少项。

### 4. 克隆逻辑

`generate_slide()` 中的克隆循环改为向量乘法：

```python
resolution = CatalogPage._get_or_create_catalog_items(catalog_slide, catalog_num, template_name)
catalog_items = resolution.items

dx_per_item, dy_per_item = CatalogPage._calculate_catalog_offset(catalog_items)
n_existing = len(catalog_items)

if resolution.allow_clone:
    for clone_idx in range(1, target_count - n_existing + 1):
        dx = dx_per_item * clone_idx
        dy = dy_per_item * clone_idx
        # clone background, number, text
```

保留的行为：

- background 仍先克隆，保证在 number/text 下方。
- 克隆 shape 仍必须重新分配 non-visual id。
- `fill_count`、递归分页、`begin_number` 递增逻辑不变。
- 当 `resolution.source == "library"` 时，`target_count` 不再通过克隆扩展；本页最多填充 `len(catalog_items)` 项，剩余内容走现有递归分页。

### 5. 目录项提取边界

本次改造不扩大 `_get_catalog_items()` 的 number-text 配对能力。

因此斜向布局支持范围明确为：

- 支持目录项之间的 anchor 斜向排列。
- 单个目录项内部的 number/text 仍需要能被当前提取逻辑识别。
- 如果模板的 number/text 配对本身也需要斜向或更复杂识别，应作为后续独立改造处理。

## 错误处理与 fallback

| 场景 | 处理方式 |
|------|---------|
| 当前 slide 无目录项 | 尝试 `shapes.json catalog_items`；不可用再创建默认 fallback |
| 当前 slide 只有 1 项 | 优先直接使用 `shapes.json catalog_items`；不可用再用单项 fallback 克隆 |
| 当前 slide 项数少于内容项 | 优先直接使用 `shapes.json catalog_items`；库项仍不足时直接分页，不再克隆库项 |
| `shapes.json catalog_items` 不存在 | 使用当前提取结果；若为空则默认 fallback |
| 偏移向量为零 | 容量回退到 `len(catalog_items)`，通过分页继续处理剩余内容 |
| 当前项 fallback 克隆后仍空间不足 | 按 `_calculate_max_per_page()` 的容量上限正常分页 |

`CatalogTemplateNotFoundError` 仍作为内部探测信号使用，由 `_get_or_create_catalog_items()` 消化。对外异常仍保持 `PPTGenError` / `PPTTemplateError` 现有边界。

## 测试策略

测试文件：`test/test_pages.py`

新增或更新用例：

| 测试名称 | 场景 | 验证点 |
|---------|------|--------|
| `test_catalog_page_single_template_item_prefers_shape_json_catalog_items` | 当前 slide 只有 1 个目录项，`shapes.json` 有多个 catalog_items | 使用库项替代当前单项，保留库项位置，旧单项 shape 被清理 |
| `test_catalog_page_insufficient_template_items_prefers_shape_json_catalog_items` | 当前 slide 有 2 项但内容更多，库中有更多 catalog_items | 优先使用库项，而不是先克隆当前 slide 项，旧少量项 shape 被清理 |
| `test_catalog_page_shape_json_items_paginate_without_cloning` | 内容数量超过库中 catalog_items 数量 | 本页只填充库项数量，剩余内容分页，不克隆库项 |
| `test_catalog_page_shape_json_pagination_does_not_leave_previous_page_content` | 使用库项分页生成多页目录 | 新页替换 duplicated slide 中的上一页目录内容，不残留上一页标题 |
| `test_catalog_diagonal_layout_cloning` | 当前 slide/default 路径至少 2 项，编号 anchor 斜向排列 | 克隆项保留 `dx` 和 `dy` |
| `test_catalog_diagonal_layout_capacity_uses_both_axes` | 斜向布局接近右/下边界 | 每页容量取两个轴约束的最小值，不越界 |
| `test_catalog_negative_offset_capacity` | 目录项向左或向上排列 | 容量计算使用负向边界 |
| `test_catalog_single_item_fallback_when_shape_json_missing` | 当前 slide 只有 1 项且库数据不可用 | 仍可按单项推断生成内容 |
| `test_catalog_page_default_fallback_items_are_centered_and_larger` | 空白页且库数据不可用 | 默认 fallback 仍居中 |
| `test_catalog_page_cloned_shapes_keep_unique_ids_and_background_order` | 克隆带背景目录项 | shape id 唯一，背景位于文字下方 |

项目 pytest 配置使用 anyio，新增 async 测试需要标注 `@pytest.mark.anyio`。

## 代码改动汇总

| 文件 | 改动 |
|------|------|
| `slidegen/services/presentation/pages.py` | 调整 `_get_or_create_catalog_items()`，返回目录项来源和是否允许克隆 |
| `slidegen/services/presentation/pages.py` | 新增 library 可用性探测和目录项 shape 清理 helper，确保库项替换时不混合旧 shape |
| `slidegen/services/presentation/pages.py` | 新增 `_calculate_catalog_offset()`，替代 `_calculate_catalog_step()` |
| `slidegen/services/presentation/pages.py` | 新增 item bounds / axis capacity helper，用完整向量计算容量 |
| `slidegen/services/presentation/pages.py` | 修改 `_calculate_max_per_page()` 签名，移除 `layout_direction` 参数 |
| `slidegen/services/presentation/pages.py` | 修改 `generate_slide()` 克隆循环，使用向量偏移 |
| `test/test_pages.py` | 增加 shapes.json 优先、旧 shape 清理、库项分页不残留、斜向克隆、双轴容量、负向偏移等回归测试 |

## 向后兼容性

保持不变：

- `CatalogPage.generate_slide()` 公共签名不变。
- 默认 fallback 仍生成居中的目录组。
- background 克隆顺序和 shape id 去重逻辑不变。
- 递归分页和编号递增逻辑不变。

行为变化：

- 当前 slide 只有单项时，如果 `shapes.json catalog_items` 可用，将直接使用库项，而不是优先克隆当前单项。
- 当前 slide 项数不足时，如果 `shapes.json catalog_items` 可用，将直接使用库项；如果库项仍不足，直接分页，而不是继续克隆库项。
- 如果库数据不可用，才按当前 slide 项计算 `projected_capacity`，并用该容量决定本页克隆数量和后续分页。
- 多项斜向排列会保留完整 `(dx, dy)`。

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| `shapes.json catalog_items` 与当前 slide 视觉来源不同，替换当前提取项可能改变布局 | 这是本次需求的预期行为；测试明确验证单项/项少时优先使用库项 |
| 替换库项时旧 shape 残留，或递归分页复制上一页内容后又叠加库项 | 替换前统一删除 extracted items 对应 shape，并增加分页不残留测试 |
| 库项数量仍不足 | 不克隆库项，直接按库项数量分页 |
| 斜向容量误判导致越界 | 使用 x/y 双轴容量最小值，不再用主导方向估算 |
| number-text 配对仍无法识别复杂斜向 item | 本次范围明确不改 `_get_catalog_items()` 配对算法，复杂配对后续单独设计 |

## 实现顺序

1. 调整 `_get_or_create_catalog_items()` 的目录项来源优先级。
2. 增加 shapes.json 优先、旧 shape 清理和递归分页不残留测试。
3. 实现 `_calculate_catalog_offset()` 并替换 `_calculate_catalog_step()` 调用。
4. 实现 bounds / axis capacity helper，修改 `_calculate_max_per_page()`。
5. 修改 `generate_slide()` 克隆循环为向量偏移。
6. 在 `generate_slide()` 中禁止对 `source == "library"` 的目录项继续克隆，库项不足时直接分页。
7. 增加斜向布局、双轴容量、负向偏移、库项分页不克隆测试。
8. 运行 focused 测试：`uv run pytest test/test_pages.py`。

## 不在本次范围内

- 改造 `_get_catalog_items()` 的复杂 number-text 配对算法。
- 支持非线性目录排列，如弧形、圆形、网格自动换行。
- 手动指定目录克隆方向。
- 目录项旋转、缩放或重排。

## 参考

- 当前代码：`slidegen/services/presentation/pages.py`
- 测试文件：`test/test_pages.py`
- 模板库结构：`slidegen/services/presentation/components.py` 中的 `CatalogItemTemplate` / `CatalogShapeTemplate`
