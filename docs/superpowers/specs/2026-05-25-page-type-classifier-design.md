# PageTypeClassifier 第一阶段设计

## 背景

当前 `components/shapes/shapes.json` 中的内容主要依赖人工收集。目标是后续支持上传一整份 PPT 后，自动识别可复用的内容页布局，并把这些布局转换为 `one_point`、`two_points`、`three_points`、`four_points` 形式。

上传的 PPT 通常包含多种页面：封面、目录、章节页、内容页、结束页等。如果直接从所有页面提取组件，容易把 Cover、Agenda、Chapter Home 或 End 页面误写入内容页布局库。因此第一阶段先实现一个独立的页面类型分类器，对齐 `slidegen/services/presentation/pages.py` 中已有的五类页面。

## 目标

实现 `PageTypeClassifier`，用于把 PPT 中的每一页分类为：

- `cover`，对应 `CoverPage`
- `catalog`，对应 `CatalogPage`
- `chapter_home`，对应 `ChapterHomePage`
- `chapter_content`，对应 `ChapterContentPage`
- `end`，对应 `EndPage`
- `unknown`，表示无法可靠判断

第一阶段只产出分类结果和报告，不写入 `shapes.json`，也不做 `one_point` 等布局抽取。

## 非目标

- 不在第一阶段修改 `components/shapes/shapes.json`
- 不实现 `one_point/two_points/three_points/four_points` 的提取
- 不导入 Cover、Catalog、Chapter Home、End 页面到 `page_placeholders`
- 不新增前端上传流程
- 不要求纯规则完成复杂 PPT 分类

## 设计原则

真实 PPT 的结构和版式复杂，纯规则分类不可靠。因此分类器采用 LLM-first 设计：

- 本地规则只处理非常明显、低风险的情况
- 大多数页面交给 agno Agent 判断，使用 `structured_outputs=True` + `output_model` 约束输出格式
- agno Agent + Pydantic 自动校验 LLM 输出的合法性（枚举、数值范围、非空）
- 低置信度、调用异常或无法判断的页面降级为 `unknown`

## LLM 实例管理

LLM 配置是用户级的（不同用户可能使用不同 provider/model/api_key），因此**不做全局单例**。

分类器在每次 `classify_pages` 调用开头，通过 `user_id` + `llm_config_id` 调用 `get_llm_instance` 创建一个 LLM 实例（`Model` 类型），该实例在同一次分类任务内复用于所有页面的 Agent 调用。调用结束后实例随方法生命周期结束，不持久化。

好处：

- 同一次分类 20 页只创建 1 个 LLM 实例，避免逐页重复构造
- 不同用户的调用各自使用自己的配置，互不干扰
- 用户更新 LLM 配置后，下次调用自然生效
- 测试可直接注入 mock LLM，无需改签名

## 模块位置

新增模块：

`slidegen/services/presentation/page_classifier.py`

该模块属于 service 层，可调用项目已有 LLM 配置。Router 层后续只传入 primitive 参数，例如 `user_id`、`llm_config_id`、`pptx_path`，不直接创建 LLM。

## 核心类型

```python
class PageType(str, Enum):
    COVER = "cover"
    CATALOG = "catalog"
    CHAPTER_HOME = "chapter_home"
    CHAPTER_CONTENT = "chapter_content"
    END = "end"
    UNKNOWN = "unknown"
```

```python
@dataclass
class PageClassification:
    page_index: int
    page_type: PageType
    confidence: float
    reason: str
    method: Literal["rule", "llm", "fallback"]
```

```python
@dataclass
class ShapeSummary:
    shape_id: int
    name: str
    shape_type: str
    text: str
    x: int
    y: int
    width: int
    height: int
    has_text_frame: bool
    is_placeholder: bool
    is_picture: bool
    font_size: float | None
    is_bold: bool | None
```

### agno Agent 结构化输出模型

分类器使用 `agno.Agent`（与项目中 `OutlineAgent`、`ContentAgent` 同模式）进行 LLM 分类，通过 `output_model` + `structured_outputs=True` 约束输出格式，LLM 自动输出符合 schema 的 JSON，无需手动解析和校验。

```python
class AgentPageClassificationOutput(BaseModel):
    """agno Agent 的 output_model，约束 LLM 输出格式。"""
    page_type: PageType = Field(description="分类结果，必须为六种枚举之一")
    confidence: float = Field(ge=0.0, le=1.0, description="置信度，0 到 1")
    reason: str = Field(min_length=1, description="分类理由，非空字符串")
```

`PageClassification`（dataclass）是分类器的最终返回类型，包含 `page_index` 和 `method` 等本地字段；`AgentPageClassificationOutput`（Pydantic BaseModel）仅作为 agno Agent 的输出约束，只包含 LLM 能决定的三个字段。两者职责不同，不合并。

`ShapeSummary.text` 需要截断到固定长度，避免 prompt 过大。XML 不进入第一阶段分类 prompt。

## 分类流程

```python
class PageTypeClassifier:
    async def classify_pages(
        self,
        pptx_path: str,
        user_id: uuid.UUID,
        llm_config_id: uuid.UUID | None = None,
    ) -> list[PageClassification]:
        # 1. 创建 LLM 实例（单次调用内复用）
        model = await get_llm_instance(...)
        # 2-7. 遍历页面，规则判断或 Agent 判断，复用 model
        ...
```

1. 调用 `get_llm_instance` 创建 LLM 实例（`Model` 类型），整个分类任务复用此实例。
2. 打开 PPT，遍历每一页。
3. 为每页提取轻量摘要：
   - slide index
   - shape 数量
   - 文本 shape 数量
   - 图片数量
   - 每个 shape 的类型、文本、位置、尺寸、字号、是否占位符
4. 执行本地低风险规则：
   - 最后一页含明显结束语，例如 `thank you`、`thanks`、`谢谢`、`Q&A`，可判为 `end`
   - 第一页只有少量大标题或副标题，可判为 `cover`
   - 空白页或几乎无有效内容，判为 `unknown`
5. 如果规则无法高置信度判断，则创建 agno Agent 并调用（使用步骤 1 的 model）：

```python
agent = Agent(
    name="Page type classifier",
    instructions=[PAGE_CLASSIFIER_INSTRUCTIONS],
    model=model,
    output_schema=AgentPageClassificationOutput,
)
response = await agent.arun(page_summary_prompt)
```
- `page_type` 必须属于 `PageType` 枚举（非法值会被 Pydantic 拒绝）
- `confidence` 必须在 0 到 1 之间（`Field(ge=0.0, le=1.0)`）
- `reason` 必须是非空字符串（`Field(min_length=1)`）

6. 从 Agent 输出构造 `PageClassification`，补充 `page_index` 和 `method="llm"`。
7. Agent 调用异常、agno 内部校验失败或置信度过低时，返回 `unknown`，`method` 为 `fallback`。

## LLM Prompt 要点

Prompt 应明确要求模型在五类页面和 `unknown` 中选择，并解释：

- `cover`：演示文稿封面，通常包含主标题、副标题、作者、日期
- `catalog`：目录、议程、agenda、章节列表
- `chapter_home`：章节过渡页或章节首页，突出章节标题或编号
- `chapter_content`：实际内容页，通常包含观点、标题正文组、图文说明、分析信息
- `end`：结束页、感谢页、Q&A、联系方式页
- `unknown`：无法可靠归类

LLM 不负责在第一阶段判断 `one_point` 等布局，也不负责返回每个 shape 的 `content_type`。

## 与后续组件导入的关系

后续自动写入 `shapes.json` 时，只处理分类为 `chapter_content` 且置信度达标的页面。

非内容页的处理策略：

- `cover`：跳过并报告
- `catalog`：跳过并报告
- `chapter_home`：跳过并报告
- `end`：跳过并报告
- `unknown`：跳过并报告原因

## 错误处理

- LLM 实例创建失败（用户无活跃配置、配置无效）：抛出清晰异常，由上层服务转换为接口错误，不降级为逐页 unknown
- PPT 文件无法打开：抛出清晰异常，由上层服务转换为接口错误
- 单页 shape 摘要提取失败：该页返回 `unknown`，报告原因
- agno Agent 调用异常（网络超时、provider 错误）：该页返回 `unknown`，报告原因
- agno Agent 输出校验失败（Pydantic 验证异常）：该页返回 `unknown`，报告原因

## 测试计划

新增 `test/test_page_classifier.py`。

测试范围：

- `ShapeSummary` 能从普通文本框、图片、placeholder 提取基础信息
- 明显结束页可由规则判为 `end`
- 明显封面页可由规则判为 `cover`
- mock Agent 返回合法 `AgentPageClassificationOutput` 时能构造目标 `PageClassification`
- mock Agent 返回 Pydantic 校验失败时降级为 `unknown`
- Agent 调用异常（超时、网络错误）时降级为 `unknown`
- 批量分类多页时能返回每页报告

测试运行方式遵循项目约定：

```bash
uv run pytest test/test_page_classifier.py
```

## 验收标准

- 可以对一份 PPT 的所有页面输出 `PageClassification` 列表
- 分类类型严格对齐 `pages.py` 的五个页面类和 `unknown`
- 默认使用 LLM-first 设计，规则只处理高置信度明显页面
- LLM 输出由 agno Agent `structured_outputs` + `output_model` 保证格式合法，失败时不会污染后续导入流程
- 第一阶段不修改 `shapes.json`
- 单测覆盖规则分类、LLM 分类、LLM 失败降级和批量报告
