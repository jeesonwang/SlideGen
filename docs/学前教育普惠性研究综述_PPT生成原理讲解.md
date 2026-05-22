# 《学前教育普惠性研究综述_课堂汇报》PPT 生成原理讲解

## 1. 先说结论

这份 PPT 的“复杂但不乱、丰富但不冲突”，并不是因为底层有一个很强的“自动排版 AI 引擎”在实时帮它避让碰撞，而是因为它采用了下面这套更稳定的工程化路径：

1. 先用 JS 把整套视觉系统写成明确规则。
2. 再把常见版式抽象成可复用组件函数。
3. 每一页都用精确坐标把对象摆到固定位置。
4. 在导出前，做一次“有没有重叠、有没有越界”的机械检查。
5. 最后由 `pptxgenjs` 把这些对象翻译成 PPT 里的原生文本框、形状、线条和页面。

所以，这份代码本质上不是“让模型现场想怎么摆”，而是“先把设计语言和版式语法写死，再让程序按规则执行”。

## 2. 一个关键事实：这份实际代码与当前 `Presentations` skill 并不完全一致

你贴出来的当前 `Presentations` skill 文档强调的是：

- 现在推荐走 `artifact-tool presentation JSX`
- 通过 artifact-tool 导入、渲染、导出 PPTX

但你这份实际生成代码走的是另一条更直接的链路：

- 使用 `pptxgenjs`
- 用 `slide.addText(...)`、`slide.addShape(...)` 直接往 PPT 里写对象
- 再用本地辅助脚本做布局检查

从源码就能看出来：

- 引入 `pptxgenjs`：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:4)
- 引入布局校验辅助函数：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:5)
- 最终导出 `pptx.writeFile(...)`：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:1036)

这意味着你现在看到的这份 deck，原理上更像：

`内容规划 -> JS 版式脚本 -> pptxgenjs 对象树 -> PPTX 文件`

而不是：

`内容规划 -> presentation JSX -> artifact-tool 渲染/导出 -> PPTX 文件`

这一点很重要，因为它决定了“合理布局”主要来自人工设计好的 JS 规则，而不是 artifact-tool 自带的自动布局系统。

## 3. 整个生成链路到底怎么跑

### 3.1 初始化 PPT 容器

代码先创建一个 `pptx` 实例，并定义整份文档的全局属性：

- 宽屏比例：`pptx.layout = "LAYOUT_WIDE"`
- 语言：`zh-CN`
- 主题字体：`Microsoft YaHei`

对应源码：

- 版面与主题：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:11)
- 幻灯片尺寸常量：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:43)

这里的 `13.333 x 7.5` 可以理解为一个统一的二维画布。后面所有对象都是在这个坐标系里摆放的。

### 3.2 所有元素都是“对象”

在这条链路里，PPT 不是一张位图，而是一组结构化对象：

- 文本框
- 矩形
- 圆角矩形
- 线条
- 页脚
- 装饰条

例如：

- `slide.addShape(...)` 负责添加背景块、卡片、圆角标签、线条
- `slide.addText(...)` 负责添加标题、正文、编号、注释

因此，JS 代码其实是在“声明一个页面对象树”。

### 3.3 导出时发生了什么

最后的 `await pptx.writeFile({ fileName: OUT_PATH })` 会把每一页上积累的这些对象，转换成 PPTX 内部的 XML 结构，然后打包成 `.pptx` 文件。

对应源码：

- 导出：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:1036)

从本质上说，PPTX 只是一个压缩包，里面装着很多描述“某页有个文本框、坐标是多少、字体多大、填充什么颜色”的 XML 文件。`pptxgenjs` 的作用，就是替你生成这些 XML。

## 4. 为什么它能做出“复杂但合理”的布局

这里面最核心的不是“会画”，而是“先约束，再组合”。

### 4.1 第一层：先锁定设计令牌，而不是每页随便配色

代码一开始就定义了统一色板 `C`：

- `navy` 深蓝：主标题、主背景、重点结构
- `teal` 青绿：强调、编号、流程箭头、轻强调边框
- `cyan` / `sky` / `cream`：低饱和浅背景
- `text` / `sub`：主文字与次文字
- `gold` / `red` / `green`：局部分类强调

对应源码：

- 色板常量：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:28)

这一步非常关键，因为“颜色不冲突”往往不是靠后期修出来的，而是靠一开始就把可选颜色限制在一小组彼此兼容的颜色里。

这份代码的做法是：

- 大面积背景只用低饱和浅色
- 深色只承担结构锚点和高对比标题
- 强调色数量很少，避免每页出现很多互相打架的颜色
- 语义颜色有分工，不会任意漂移

所以它看起来统一，不是因为随机碰巧好看，而是因为根本没有给自己太多“出错自由度”。

### 4.2 第二层：把版式抽成组件，而不是每页手搓

这份代码最重要的稳定器，是几个可复用函数：

- `addFrame`：上下色条和背景框架
- `addFooter`：统一页脚和页码
- `addTitle`：统一章节标签、标题、副标题
- `addCard`：统一卡片容器
- `addBullets`：统一项目符号正文
- `addTag`：统一右上角小标签
- `finalizeSlide`：统一做导出前检查

对应源码：

- 框架：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:46)
- 页脚：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:66)
- 标题区：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:89)
- 卡片：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:134)
- 项目符号：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:166)
- 标签：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:194)
- 收尾校验：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:217)

这意味着：

- 同一种信息，总是用同一种视觉语法呈现
- 间距、圆角、标题高度、分割线位置都是复用的
- 单页复杂度提高了，但系统复杂度降低了

这和网页里做 design system 是一样的。复杂感来自组合，不来自失控。

补充一点，卡片阴影也没有随手乱配，而是统一走 `safeOuterShadow(...)`，用固定的外阴影参数保证质感一致，同时避免导出 XML 时出现奇怪的阴影兼容问题。

- 阴影辅助函数：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/pptxgenjs_helpers/util.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/pptxgenjs_helpers/util.js:5)

### 4.3 第三层：不是自动排版，而是“受约束的手工坐标布局”

这份 JS 的核心布局方式是：

- 每个对象都明确写 `x / y / w / h`
- 坐标用统一画布
- 不同卡片之间靠固定 gap 组织
- 内容长度反过来影响字体和盒子尺寸

例如目录页：

- 从 `startX = 0.72` 开始
- 卡片宽 `cardW = 1.82`
- 间隔 `gap = 0.24`
- 通过循环把 6 个目录卡片均匀排开

对应源码：

- 目录页横向排布：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:357)

再比如“八大研究主题”这一页：

- 先定义统一盒子尺寸 `boxW = 3.7`, `boxH = 0.9`
- 用 `idx % 2` 算列
- 用 `Math.floor(idx / 2)` 算行
- 再按 `colGap`、`rowGap` 自动铺成两列四行

对应源码：

- 两列网格布局：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:558)

所以它“看起来像自动排得很好”，但本质上更接近：

- 先人工定一个可信的网格法则
- 再让程序重复执行这个法则

### 4.4 第四层：复杂感来自“信息分组”，不是来自对象变多

这份 deck 的复杂感主要来自四种结构，而不是靠堆装饰：

1. 大框架
2. 内容卡片
3. 局部标签
4. 结论条或总结条

以封面为例：

- 左侧深色纵向主视觉区
- 右侧正文信息区
- 中部双卡片
- 底部一句高亮结论

对应源码：

- 封面结构：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:223)

你会发现，这并不是“往页面上加了很多小东西”，而是先划大区，再在区内加少量有职责的对象。

这就是为什么它不会乱：

- 大结构先定边界
- 小结构只在边界内活动
- 每个对象都有明确角色

### 4.5 第五层：文本不是无限流入的，而是被提前裁成适合版面的长度

很多 PPT 重叠，根源不是布局函数差，而是内容太长。

这份代码能稳定，一个重要前提是：文本内容在进入布局前就已经被“版式化”了。

表现为：

- 每个 bullet 基本都是一到两句
- 每个卡片只容纳有限条目
- 结论条只放一句高密度总结
- 目录卡、副标题、标签都很短

比如 `addBullets` 并没有做复杂的自动折行求解，它只是：

- 设定统一字体大小
- 设定统一行高
- 每个 bullet 占固定高度
- 逐条把 `y` 往下推进

对应源码：

- 项目符号的顺序堆叠逻辑：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:166)

也就是说，这个系统默认的哲学不是“超长文字也能智能适配”，而是“先把文字浓缩成适合 PPT 的单位，再交给版式函数”。

### 4.6 第六层：层级靠字号、颜色、底色，而不是靠花哨造型

这份 deck 的视觉层级主要靠以下几个维度建立：

- 标题更大、更深色
- 副标题更小、更灰
- 卡片标题加粗
- 标签使用独立底色
- 总结句使用整条强调底
- 深色背景上只放少量高对比信息

所以它的“复杂”其实是信息层级复杂，不是视觉噪声复杂。

## 5. 为什么它通常不会重叠

### 5.1 因为大多数元素的位置都是提前算好的

只要：

- 卡片尺寸固定
- 行高固定
- 间距固定
- 文本长度受控

那么重叠风险本来就会很低。

例如目录页 6 张卡片的排布，不是让运行时自己挤，而是按公式直接算出 6 个 `x` 值。只要 `cardW * 6 + gap * 5` 没超过页面宽度，它就天然不会互撞。

### 5.2 因为导出前做了“碰撞体检”

`finalizeSlide(...)` 在每页结尾都会调用两个检查器：

- `warnIfSlideHasOverlaps(...)`
- `warnIfSlideElementsOutOfBounds(...)`

对应源码：

- 调用检查：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:217)

#### 重叠检查怎么做

`warnIfSlideHasOverlaps(...)` 会扫描当前页的所有对象，抽取每个对象的：

- 类型
- `x`
- `y`
- `w`
- `h`

然后两两比较它们的边界关系，看是：

- 重叠
- 包含
- 分离

对应源码：

- 类型推断：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/pptxgenjs_helpers/layout.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/pptxgenjs_helpers/layout.js:4)
- 重叠扫描入口：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/pptxgenjs_helpers/layout.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/pptxgenjs_helpers/layout.js:23)

它还做了两个很实用的工程处理：

- 可以忽略线条，因为很多分割线的包围盒天生会“压到”别的元素
- 对“斜线的包围盒误判”为重叠做了特殊排除

对应源码：

- 忽略线条选项：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/pptxgenjs_helpers/layout.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/pptxgenjs_helpers/layout.js:33)
- 斜线误判修正：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/pptxgenjs_helpers/layout.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/pptxgenjs_helpers/layout.js:82)

如果是文本之间的严重重叠，它会直接报 `THIS MUST BE FIXED` 级别的错误，而不是轻描淡写地提醒。

对应源码：

- 严重文本重叠阈值：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/pptxgenjs_helpers/layout.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/pptxgenjs_helpers/layout.js:20)
- 严重错误输出：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/pptxgenjs_helpers/layout.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/pptxgenjs_helpers/layout.js:168)

#### 越界检查怎么做

`warnIfSlideElementsOutOfBounds(...)` 会读取每个对象的边界，再和整页宽高比较：

- 左边是否小于 0
- 上边是否小于 0
- 右边是否超出版心
- 下边是否超出版心

对应源码：

- 越界检查入口：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/pptxgenjs_helpers/layout.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/pptxgenjs_helpers/layout.js:575)

这一步能防止：

- 页码被挤出页面
- 卡片右边超出去
- 底栏文字压到底边之外

### 5.3 我实际复跑过这份脚本，当前版本没有触发这些警告

我在本地重新执行了这份 JS：

```bash
node /Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js \
  /Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/_regen_check.pptx
```

控制台只输出了成功生成信息，没有出现重叠或越界警告。说明当前这一版参数组合在现有内容下是能通过自检的。

## 6. 为什么它通常不会出现颜色冲突

颜色不冲突，核心不是“颜色选得少”，而是“颜色职责单一”。

这份代码里大致是这种语法：

- `navy`：结构主色
- `teal`：交互式强调色 / 编号色 / 分割导向色
- `cyan` / `sky` / `cream`：承载信息的浅底色
- `text` / `sub`：主次文字
- `gold` / `green` / `red`：分类性强调，不做大面积主背景

这就避免了几个常见问题：

- 每页换主色导致整体失焦
- 标题和背景都很重，彼此争抢注意力
- 为了“丰富”而堆很多高饱和色
- 一种颜色同时承担太多语义

更重要的是，这份代码大量使用：

- 深字配浅底
- 白字配深底
- 浅色块只做辅助，不抢标题

所以它天然更容易保持可读性。

## 7. 为什么它看起来“复杂”，却没有“自动生成感”

因为它没有用一种版式打完整份 deck，而是在同一设计系统内做了多种宏观结构。

你可以看到至少有这些页面语法：

- 封面：左右分栏 + 双信息卡 + 结论条
- 目录：六等分横向卡片带流程箭头
- 引言：左大卡 + 右上时间节点 + 右下说明卡
- 研究分析：左概述 + 右侧 2x4 主题网格
- 研究结果：上方四卡 + 下方三块横向重点
- 综合讨论：左右对照双栏
- 结论：三块并列总结
- 阅读心得：三张反思卡 + 底部总结条
- 结束页：中心大卡

对应源码入口：

- `buildCover`：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:223)
- `buildAgenda`：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:357)
- `buildIntro`：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:442)
- `buildAnalysis`：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:512)
- `buildResults`：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:615)
- `buildDiscussion`：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:746)
- `buildConclusion`：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:804)
- `buildReflection`：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:871)
- `buildEnding`：[/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js](/Users/wjs/work/wjy/.codex_tmp_preschool_review_ppt/学前教育普惠性研究综述_课堂汇报.js:954)

这就是它“复杂而合理”的真正来源：

- 页面之间有变化，所以不单调
- 变化发生在少数受控模板之间，所以不失控

## 8. 这份代码并没有做什么

理解它没有做什么，反而更能看懂它为什么稳定。

### 8.1 它没有真正的智能自动布局器

它不会像 Figma Auto Layout 那样：

- 根据内容自动重排整页
- 自动缩放卡片组
- 自动求最优列数
- 动态回流复杂图文关系

它更像“高质量脚本化排版”，不是“通用自适应排版引擎”。

### 8.2 它没有自动解决内容爆炸问题

如果你突然把某张卡片里的每个 bullet 都加长两倍：

- 很可能就会开始挤压
- 甚至触发重叠检查

所以这套系统的前提一直是：

- 内容摘要质量足够高
- 每页信息密度被人工控制过

### 8.3 它没有自动修复碰撞

`warnIfSlideHasOverlaps(...)` 只是报错或警告，不会帮你挪位置。

也就是说：

- 检查器负责发现问题
- 版式函数负责避免问题
- 生成者负责修改问题

这是一套“规则 + QA”的体系，不是“自愈式布局”的体系。

## 9. 这份代码里最值得借鉴的工程思想

如果你以后也想稳定地产出这种 PPT，最值得复用的不是某个颜色值，而是下面这些方法。

### 9.1 先做设计系统，再做单页

先定义：

- 色板
- 字体
- 容器类型
- 页脚规则
- 标题规则
- 标签规则

再去写每页。这样复杂度会明显下降。

### 9.2 让“页面组件”复用，而不是复制粘贴坐标

`addCard`、`addBullets`、`addTitle` 这种函数，本质上就是“PPT 组件化”。这比每页直接手写所有对象，更不容易漂移。

### 9.3 内容写作要服从版面单位

真正稳定的 PPT 生成，不是先得到一大坨文本再硬塞进页面，而是先把内容压缩成适合：

- 一张卡
- 一条结论
- 一行副标题
- 三到四条 bullet

这种可排版单位。

### 9.4 导出前一定要做机械 QA

人工看图很重要，但机械检查同样关键。特别是：

- 重叠
- 越界
- 行高过密
- 标签与正文互压

这类问题非常适合程序提前扫出来。

## 10. 如果把它和更现代的 `artifact-tool presentation JSX` 对比，区别在哪

你贴的 `Presentations` skill 代表的是一种更“系统化”的未来方向，它通常更强调：

- story spine
- design system lock
- contact-sheet planning
- preview render
- QA rubric

而你这份实际 JS 更像是：

- 已经得到一个比较成熟的版式结果
- 然后用 `pptxgenjs` 把它精确实现出来

二者最本质的区别是：

- `artifact-tool JSX` 更强调“结构化构建流程”
- 这份 `pptxgenjs` 代码更强调“直接对象编排”

但在“为什么好看”这件事上，两者的共同点其实一样：

- 先有清楚的信息层级
- 再有统一视觉规则
- 最后才是导出工具

工具决定上限的一部分，但不会替代版式方法本身。

## 11. 用一句话概括这份 PPT 的生成原理

这份 PPT 之所以能从 JS 变成“布局复杂又合理、没有重叠、颜色也不打架”的成品，本质上是因为：

它把视觉设计规则、内容层级规则和页面几何规则都先编码成了受约束的组件与坐标系统，再用 `pptxgenjs` 忠实地把这些规则翻译成 PPT 对象，并在导出前用几何检查器做了一次机械 QA。

如果你愿意，我下一步可以继续帮你做两件事里的任意一件：

1. 把这份 JS 逐页加注释，做成“源码精读版”。
2. 把这套原理进一步抽象成“如何自己写一套 PPT 生成框架”的教程。
