# SlideGen 项目重构方案

## 当前问题

1. **controller/** - 名称误导，实际包含的是 Factory 类，不是 MVC Controller
2. **common/ vs utils/** - 功能重叠，职责不清晰
3. **engine/** - 命名不够直观
4. **workflows/utils/** - 工具函数分散
5. **exception/** - 目录命名不规范，应该为复数形式
6. 根目录下散落多个配置文件和入口文件

## 建议的新文件结构

```
slidegen/
├── api/                    # API 层 (已存在)
│   ├── routers/           # 路由端点 (已存在7个文件)
│   ├── deps.py            # 依赖注入
│   └── main.py            # API 主入口
│
├── core/                   # 核心配置和基础设施 (新建)
│   ├── config.py          # 应用配置 (来自 config/conf.py)
│   ├── celery_config.py   # Celery配置 (来自 config/celery_config.py)
│   ├── security.py        # 安全相关 (来自 common/security.py)
│   ├── database.py        # 数据库连接 (来自 engine/database.py)
│   ├── redis.py           # Redis 连接 (来自 engine/redis.py)
│   ├── logging.py         # 日志配置 (来自 common/log.py)
│   └── constants.py       # 常量定义 (来自 config/const.py)
│
├── services/              # 业务逻辑服务层 (新建，原 workflows 的重组)
│   ├── slidegen/          # 幻灯片生成服务
│   │   ├── workflow.py    # 主工作流 (来自 workflows/slidegen.py)
│   │   └── agents.py      # Agent 配置 (新建或从workflow中分离)
│   ├── knowledge/         # 知识库服务
│   │   └── kb_manager.py  # 知识库管理 (来自 workflows/knowledge/kb_manager.py)
│   ├── document/          # 文档处理服务 (原 docparse 重命名)
│   │   ├── parsers/       # 文档解析器 (来自 workflows/docparse/reader/)
│   │   │   ├── base.py
│   │   │   ├── docx_reader.py
│   │   │   ├── pdf_reader.py
│   │   │   ├── markdown_reader.py
│   │   │   └── ...
│   │   ├── processor.py   # 文档处理器 (来自 workflows/docparse/file_processor.py)
│   │   └── markdown/      # Markdown 处理 (来自 workflows/docparse/markdown_document/)
│   │       ├── elements.py
│   │       └── _typing.py
│   ├── presentation/      # 演示文稿生成服务
│   │   ├── components.py  # 组件 (来自 workflows/presentation/components.py)
│   │   ├── pages.py       # 页面生成 (来自 workflows/presentation/pages.py)
│   │   ├── converter.py   # 转换器 (来自 workflows/presentation/md_converter.py)
│   │   ├── generator.py   # 生成器 (新建或从现有文件中分离)
│   │   ├── icon_searcher.py # 图标搜索 (来自 workflows/presentation/icon_searcher.py)
│   │   └── image_generator.py # 图片生成 (来自 workflows/presentation/image_generator.py)
│   └── user/              # 用户相关服务 (新建)
│       └── auth.py        # 认证服务 (来自 common/user_center.py)
│
├── factories/             # Factory 类 (原 controller 重命名)
│   ├── llm_factory.py     # LLM 工厂 (来自 controller/llm_factory.py)
│   ├── embedding_factory.py  # Embedding 工厂 (来自 controller/embedding_factory.py)
│   └── presentation_factory.py  # 演示文稿工厂 (来自 controller/presentation_controller.py)
│
├── models/                # 数据库模型 (已存在)
│   ├── base.py
│   ├── user.py
│   ├── llm_config.py
│   ├── embedding_config.py
│   ├── task.py
│   └── image_asset.py     # 图片资源模型 (已存在)
│
├── schemas/               # Pydantic schemas (已存在)
│   ├── auth.py            # 认证相关schema (新建)
│   ├── gen_request.py     # 生成请求schema (已存在)
│   ├── llm_config.py      # LLM配置schema (已存在)
│   ├── embedding_config.py # Embedding配置schema (已存在)
│   ├── file_upload.py     # 文件上传schema (已存在)
│   ├── image_prompt.py    # 图片提示schema (已存在)
│   ├── page.py            # 页面schema (已存在)
│   └── response_schema.py # 响应schema (已存在)
│
├── middleware/            # 中间件 (已存在)
│   └── exception.py
│
├── exceptions/            # 异常定义 (原 exception 重命名)
│   ├── base.py            # 基础异常 (来自 exception/base.py)
│   ├── custom.py          # 自定义异常 (来自 exception/custom_exception.py)
│   └── codes.py           # 错误码 (来自 exception/error_code.py)
│
├── utils/                 # 通用工具函数 (合并 common + utils + workflows/utils)
│   ├── file.py            # 文件操作 (来自 utils/file_manager.py)
│   ├── time.py            # 时间处理 (来自 utils/time.py)
│   ├── validators.py      # 验证器 (来自 utils/verify.py)
│   ├── helpers.py         # 其他辅助函数 (新建，整合workflows/utils/)
│   ├── download.py        # 下载助手 (来自 workflows/utils/download_helpers.py)
│   ├── env.py             # 环境变量 (来自 workflows/utils/get_env.py)
│   ├── image.py           # 图片提供 (来自 workflows/utils/image_provider.py)
│   └── slide.py           # 幻灯片工具 (来自 workflows/utils/slide_utils.py)
│
├── tasks/                 # 后台任务 (新建)
│   ├── celery_app.py      # Celery应用 (来自根目录 celery_app.py)
│   └── slidegen_tasks.py  # SlideGen任务 (来自根目录 tasks.py)
│
├── server.py          # 服务器启动脚本 (来自根目录 server.py)
├── base.py            # 基础配置 (来自根目录 base.py)
├── gen_env_sample.py  # 环境变量示例生成 (来自根目录 gen_env_sample.py)

```
