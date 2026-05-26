# Content Style Importer 第二阶段设计

## 背景

第一阶段已经实现 `PageTypeClassifier`，可以把上传 PPT 中的页面分类为 `cover`、`catalog`、`chapter_home`、`chapter_content`、`end` 或 `unknown`。第二阶段要在此基础上，只处理可靠的 `chapter_content` 页面，把这些内容页转换为当前 `ChapterContentPage` 可消费的 `one_point`、`two_points`、`three_points`、`four_points` 样式。

当前运行时链路仍然是：

```text
ChapterContentPage.generate_slide()
  -> ChapterLayout(len(content.children))
  -> components_manager.get_random_style(chapter_layout)
  -> 按 ContentType 替换 title/content/picture/number/icon
```

因此第二阶段的产物必须严格符合 `components/shapes/shapes.json` 的现有结构，而不是引入新的渲染模型。更长期的语义布局渲染器仍可把 `shapes.json` 作为迁移和样式资产，但本阶段的目标是先把“人工收集样式”变成“可控的自动导入流程”。

## 目标

- 新增一个内容页样式导入服务，接收 PPTX 路径、`user_id`、可选 `llm_config_id` 和写入选项。
- 复用第一阶段 `PageTypeClassifier`，只筛选 `chapter_content` 且置信度达标的页面。
- 对内容页中的 shape 做内容组识别和 `ContentType` 标注。
- 将合格内容页转换为 `Style`，写入 `one_point`、`two_points`、`three_points`、`four_points`。
- 默认支持 dry-run，先返回导入报告，不修改 `shapes.json`。
- 真正写入时保护已有 JSON：保留现有 layout、style 和 `page_placeholders`，并使用原子写入。

## 非目标

- 不修改 `PageTypeClassifier` 的 agno 参数；第一阶段以当前已验证实现为准。
- 不导入 `cover`、`catalog`、`chapter_home`、`end` 的 page placeholders。
- 不新增前端上传 UI 或 HTTP API。
- 不替换 `ChapterContentPage.generate_slide()` 的运行时渲染逻辑。
- 不尝试支持超过四个内容组的页面。
- 不把表格、图表、复杂 SmartArt 语义化为新内容模型；这些页面本阶段跳过或作为装饰保守处理。

## 模块位置

新增模块：

```text
slidegen/services/presentation/component_importer.py
```

该模块属于 service 层，可以：

- 打开 PPTX 文件
- 调用 `PageTypeClassifier`
- 在服务层解析项目已有 LLM 配置
- 创建 `ComponentsManager`
- 写入组件 JSON

Router 层后续如果接入该能力，只传 `pptx_path`、`user_id`、`llm_config_id`、`dry_run` 等 primitive 参数，不创建 LLM 实例，也不直接操作 JSON。

## 核心类型

```python
class ImportSlideStatus(str, Enum):
    IMPORTED = "imported"
    SKIPPED = "skipped"
    DRY_RUN = "dry_run"
    FAILED = "failed"
```

```python
@dataclass
class ContentStyleImportOptions:
    pptx_path: Path
    user_id: uuid.UUID
    llm_config_id: uuid.UUID | None = None
    target_json_path: Path = Path(settings.COMPONENTS_PATH)
    min_page_confidence: float = 0.7
    min_role_confidence: float = 0.7
    dry_run: bool = True
    overwrite_existing: bool = False
    backup: bool = True
```

```python
@dataclass
class ShapeAssignment:
    shape_id: int
    content_type: ContentType
    group_index: int | None
    include: bool
    reason: str
    confidence: float
```

```python
@dataclass
class ImportedSlideReport:
    page_index: int
    page_type: PageType
    page_confidence: float
    status: ImportSlideStatus
    layout: ChapterLayout | None
    style_name: str | None
    reason: str
    warnings: list[str]
```

```python
@dataclass
class ImportReport:
    pptx_path: Path
    target_json_path: Path
    dry_run: bool
    imported_count: int
    skipped_count: int
    failed_count: int
    slides: list[ImportedSlideReport]
```

## 服务入口

```python
class ContentStyleImporter:
    async def import_from_pptx(
        self,
        *,
        pptx_path: str | Path,
        user_id: uuid.UUID,
        llm_config_id: uuid.UUID | None = None,
        target_json_path: str | Path | None = None,
        min_page_confidence: float = 0.7,
        min_role_confidence: float = 0.7,
        dry_run: bool = True,
        overwrite_existing: bool = False,
    ) -> ImportReport:
        return report
```

实现时建议在 `import_from_pptx()` 开头解析一次 LLM 实例，并在同一次导入任务内复用：

```text
get_llm_instance(request)
  -> PageTypeClassifier.classify_pages(pptx_path=pptx_path, user_id=user_id, model=model)
  -> ShapeRoleAgent.assign_roles(slide=slide, summaries=summaries, model=model)
```

这样同一份 PPT 不会为页面分类和 shape role 判断重复创建模型实例。测试可以直接注入 fake classifier、fake role assigner 或 fake model，避免真实网络调用。

## 流程

```text
PPTX
  -> PageTypeClassifier
  -> filter chapter_content pages
  -> summarize shapes
  -> local role/group rules
  -> LLM role fallback when ambiguous
  -> validate ChapterContentPage compatibility
  -> build Style
  -> dry-run report or atomic JSON write
```

每页处理顺序：

1. 打开 PPT，获取所有 slide。
2. 调用 `PageTypeClassifier.classify_pages()` 得到页面分类。
3. 跳过非 `chapter_content` 页面，并在报告中记录原因。
4. 跳过置信度低于 `min_page_confidence` 的内容页。
5. 对候选内容页提取 shape 摘要，包含文本、位置、尺寸、字号、shape 类型、是否 placeholder、是否图片。
6. 用本地规则识别明显的 slide title、number、picture、icon、decoration 和内容组。
7. 如果规则无法形成可靠的 1 到 4 个内容组，调用 LLM role agent 判断。
8. 校验导入结果是否符合 `ChapterContentPage` 当前运行时约束。
9. dry-run 时只返回报告；非 dry-run 时写入 `shapes.json`。

## 内容组识别规则

内容组是 `one_point/two_points/three_points/four_points` 的来源。第二阶段以“能被当前 `ChapterContentPage` 正确复用”为准，而不是以视觉复杂度为准。

### 需要跳过的页面元素

- placeholder shape 默认不进入 style；内容页标题由 `Page._find_or_inject_placeholder(page_type="chapter_content", role="title")` 负责。
- 位于页面顶部、横跨宽度较大、字体明显更大的文本框，视为 slide-level title，跳过。
- 页码、页眉、页脚、logo、水印、版权信息等不属于内容组，作为 `DECORATION` 或跳过。
- 无法提取 XML 的非图片 shape 跳过并记录 warning。

### 本地规则优先识别

- 纯数字、`01`、`02`、`1.`、罗马数字等短文本，优先标注为 `NUMBER`。
- 有文本且与正文框相邻、字号更大或位置更靠上，标注为 `TITLE`。
- 承载较长文本、项目说明或段落的文本框，标注为 `CONTENT`。
- 图片按 slide-relative 面积区分：
  - 面积较小、近似正方形、靠近标题或编号，优先 `ICON`。
  - 面积较大或作为主视觉区域，优先 `PICTURE`。
- 无文本的线条、色块、背景框、分隔线，标注为 `DECORATION`。

### group_index 规则

- `group_index` 从 0 开始，按视觉阅读顺序排列。
- 横向布局优先按 `x` 排序，纵向布局优先按 `y` 排序。
- 同一个内容组内通常包含一个 `TITLE`、一个 `CONTENT`，可选 `NUMBER`、`ICON`、`PICTURE` 和若干 `DECORATION`。
- 当候选内容组数量不在 1 到 4 之间时，该页跳过。

## LLM Role Agent

本地规则不确定时，使用 LLM 只判断 shape role 和 group，不让它返回 XML 或修改 JSON。

输入：

- slide index、slide width、slide height
- shape 摘要列表
- 页面分类结果和分类理由
- 本地规则已确定的 role 候选和不确定项

输出模型：

```python
class AgentShapeAssignment(BaseModel):
    shape_id: int
    content_type: Literal["title", "content", "number", "picture", "icon", "decoration", "skip"]
    group_index: int | None = Field(ge=0, le=3)
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)


class AgentShapeRoleOutput(BaseModel):
    point_count: int = Field(ge=1, le=4)
    assignments: list[AgentShapeAssignment]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)
```

LLM 输出低于 `min_role_confidence`、缺少必要 shape、`point_count` 与 group 数不一致、shape id 不存在、或者 Pydantic 校验失败时，该页跳过，不写入。

## `ChapterContentPage` 兼容性校验

当前 `ChapterContentPage.generate_slide()` 对 `TITLE` 和 `CONTENT` 有强约束：

- 当 style 中存在 `ContentType.TITLE` 时，`len(title_shape.location)` 必须等于 point 数。
- 当 style 中存在 `ContentType.CONTENT` 时，`len(content_shape.location)` 必须等于 point 数。

因此第二阶段导入时必须满足：

- `point_count` 在 1 到 4 之间。
- `ChapterLayout(point_count)` 可映射到 `one_point/two_points/three_points/four_points`。
- 必须能形成一个 `TITLE` 逻辑 shape，且 location 数量等于 `point_count`。
- 必须能形成一个 `CONTENT` 逻辑 shape，且 location 数量等于 `point_count`。
- 可选重复角色 `NUMBER`、`ICON`、`PICTURE` 的 location 数量若存在，优先要求等于 `point_count`；否则降级为 `DECORATION` 或跳过该角色。
- 多个同类重复 shape 必须能被合并为一个 `CShape`，也就是 XML 在去除位置、shape id、shape name 和文本内容后足够相似。
- 如果同类 shape 视觉上属于同一角色但 XML 风格差异过大，本阶段跳过该页，避免生成时重复渲染或数量不匹配。

这一段是第二阶段最重要的验收门槛。宁可少导入，也不要写入无法被当前生成器安全消费的 style。

## Style 构建

不再直接使用现有 `ComponentsManager.add_style_from_slide()` 的面积启发式作为导入入口，因为它会自行猜测 `content_type`。第二阶段新增显式 assignment 驱动的构建路径：

```python
def add_style_from_slide_assignments(
    self,
    slide: Slide,
    layout_type: ChapterLayout,
    style_name: str,
    assignments: list[ShapeAssignment],
) -> Style:
    return style
```

也可以先把该逻辑放在 `component_importer.py` 的 `StyleBuilder` 内部，等稳定后再沉入 `ComponentsManager`。

构建规则：

- `include=False` 的 shape 不进入 style。
- 图片类型保持 `xml=None`，写入 `location` 和 `content_type`。
- 文本、线条、色块等 XML shape 使用 `remove_custDataLst()` 清理。
- shape name 使用稳定格式，例如 `title_0`、`content_0`、`number_0`、`decoration_0`。
- `zorder` 保留原 slide 顺序，导入后按 `zorder` 输出。
- 相同角色的重复 shape 按 group 顺序合并 location。
- `TITLE` 和 `CONTENT` location 必须按 `group_index` 排序。

## JSON 写入策略

写入必须通过独立 `ComponentsManager` 实例完成，不直接复用全局 `components_manager`，避免测试或并发任务污染全局状态。

写入步骤：

1. 从 `target_json_path` 加载现有 JSON。
2. 确保目标 layout key 存在；如果 `four_points` 不存在但导入了四点页面，创建空 layout。
3. 生成 style name：`upload_<ppt_stem>_p<page_number>`。
4. 如果 style name 已存在：
   - `overwrite_existing=False` 时自动追加短 hash 后缀。
   - `overwrite_existing=True` 时替换同名 style。
5. 计算 style fingerprint，避免同一页或相同结构重复导入。
6. dry-run 时不写文件，只在报告中列出拟写入内容。
7. 非 dry-run 时先写临时文件，再 `replace()` 到目标路径。
8. `backup=True` 时写入前保存一份 `.bak` 文件。

## 错误处理

- PPTX 文件不存在：抛出 `FileNotFoundError`。
- PPTX 无法打开：抛出清晰异常，由上层转换为接口错误。
- LLM 实例创建失败：抛出清晰异常，不降级为全量 skipped。
- 单页 role 判断失败：该页 `status=failed` 或 `skipped`，继续处理后续页面。
- 页面无法满足兼容性校验：跳过该页并记录原因。
- JSON 写入失败：抛出异常，报告不声称导入成功。

## 报告示例

```json
{
  "dry_run": true,
  "imported_count": 2,
  "skipped_count": 5,
  "failed_count": 0,
  "slides": [
    {
      "page_index": 0,
      "page_type": "cover",
      "status": "skipped",
      "reason": "Only chapter_content pages are imported."
    },
    {
      "page_index": 4,
      "page_type": "chapter_content",
      "status": "dry_run",
      "layout": "two_points",
      "style_name": "upload_sales_review_p5",
      "reason": "Detected 2 reusable content groups."
    }
  ]
}
```

## 测试计划

新增测试文件：

```text
test/test_component_importer.py
```

测试范围：

- 只导入 `chapter_content` 页面，跳过 cover/catalog/chapter_home/end/unknown。
- `min_page_confidence` 低于阈值时跳过。
- 规则能从生成的两点内容页识别 `TWO_POINTS`。
- 规则能识别 slide-level title 并排除在 style 外。
- 生成 style 后，`TITLE` 和 `CONTENT` location 数量等于 point 数。
- dry-run 不修改目标 JSON。
- 非 dry-run 保留已有 layout、style 和 `page_placeholders`。
- `four_points` layout 不存在时可以创建。
- style name 冲突时追加后缀，除非 `overwrite_existing=True`。
- LLM role agent 返回非法 shape id、低置信度或非法 group 时跳过页面。
- 相同 PPT 重复导入时不会产生重复 fingerprint。

测试中的 LLM 相关逻辑全部使用 fake model / fake role agent，不调用真实 provider。

运行方式：

```bash
uv run pytest test/test_component_importer.py
uv run pytest test/test_page_classifier.py test/test_components.py test/test_pages.py
```

## 验收标准

- 可以对一份包含多种页面类型的 PPT 执行 dry-run，并得到逐页导入报告。
- 非内容页不会进入 `one_point/two_points/three_points/four_points`。
- 合格内容页能生成当前 `ChapterContentPage` 可消费的 `Style`。
- `TITLE` 和 `CONTENT` 的 location 数量与 point 数严格一致。
- 写入 JSON 时保留已有数据，并使用原子写入。
- 模糊页面、复杂页面和低置信度页面被跳过并说明原因。
- 不修改 `PageTypeClassifier` 的已验证 agno 配置。

## 后续阶段

第三阶段可以在第二阶段稳定后再做：

- 导入 Cover、ChapterHome、End 的 `page_placeholders`。
- 为 Catalog 页面单独设计目录模板导入逻辑。
- 接入上传 API 和前端 dry-run 预览。
- 将导入得到的 style 迁移为未来 `LayoutRecipe` 或 `VisualPrimitive` 资产。
