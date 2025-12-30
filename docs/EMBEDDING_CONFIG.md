# Embedding配置系统

## 概述

SlideGen现在支持用户自定义配置embedding模型，类似于LLM配置系统。用户可以通过API创建、管理和使用自己的embedding配置，而不再需要依赖环境变量。

## 主要特性

### 1. 支持的Embedding Provider

- **OpenAI**: OpenAI官方embedding API
  - text-embedding-3-large (3072维)
  - text-embedding-3-small (1536维)
  - text-embedding-ada-002 (1536维)

- **Azure OpenAI**: Azure平台上的OpenAI embedding服务
  - 支持所有Azure OpenAI embedding模型

- **Ollama**: 本地开源embedding模型
  - nomic-embed-text (768维)
  - mxbai-embed-large (1024维)
  - all-minilm (384维)

- **Custom**: 自定义兼容OpenAI接口的embedding服务

### 2. 配置管理

每个用户可以：
- 创建多个embedding配置
- 设置一个默认配置
- 测试配置是否有效
- 更新和删除配置

### 3. 向后兼容

为了保持向后兼容性，KnowledgeBaseManager仍然支持从环境变量读取配置：
- 如果传入了`embedding_config`参数，将使用该配置
- 如果未传入配置，将回退到环境变量（会显示警告）

## API端点

所有embedding配置相关的API端点都在 `/api/v1/embedding-config/` 路径下：

### 获取所有Provider信息
```http
GET /api/v1/embedding-config/providers
```

返回所有支持的embedding provider的详细信息。

### 获取特定Provider的预设模型
```http
GET /api/v1/embedding-config/providers/{provider}/models
```

参数:
- `provider`: openai, azure_openai, ollama, custom

### 测试Embedding配置
```http
POST /api/v1/embedding-config/test
```

请求体:
```json
{
  "provider": "openai",
  "model_id": "text-embedding-3-small",
  "api_key": "your-api-key",
  "base_url": "https://api.openai.com/v1",
  "dimensions": 1536,
  "test_text": "测试文本"
}
```

响应:
```json
{
  "success": true,
  "embedding_dimension": 1536,
  "latency": 0.234
}
```

### 获取当前用户的所有配置
```http
GET /api/v1/embedding-config/
```

查询参数:
- `skip`: 跳过的记录数（默认0）
- `limit`: 返回的最大记录数（默认100）

### 创建新配置
```http
POST /api/v1/embedding-config/
```

请求体:
```json
{
  "name": "我的OpenAI Embedding",
  "provider": "openai",
  "model_id": "text-embedding-3-small",
  "api_key": "sk-...",
  "base_url": "https://api.openai.com/v1",
  "dimensions": 1536,
  "description": "用于知识库的embedding配置",
  "is_active": true,
  "is_default": true
}
```

### 获取特定配置
```http
GET /api/v1/embedding-config/{config_id}
```

### 更新配置
```http
PATCH /api/v1/embedding-config/{config_id}
```

请求体（所有字段可选）:
```json
{
  "name": "更新的配置名称",
  "is_default": true
}
```

### 删除配置
```http
DELETE /api/v1/embedding-config/{config_id}
```

### 设置默认配置
```http
POST /api/v1/embedding-config/{config_id}/set-default
```

### 获取当前用户的默认配置
```http
GET /api/v1/embedding-config/default/current
```

## 使用示例

### 1. 在API中创建配置

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/embedding-config/",
        headers={"Authorization": "Bearer your-token"},
        json={
            "name": "OpenAI Embedding Small",
            "provider": "openai",
            "model_id": "text-embedding-3-small",
            "api_key": "sk-...",
            "base_url": "https://api.openai.com/v1",
            "dimensions": 1536,
            "is_default": True
        }
    )
    config = response.json()
    print(f"Created config: {config['id']}")
```

### 2. 在代码中使用配置

```python
from slidegen.models.embedding_config import EmbeddingConfigBase, EmbeddingProvider
from slidegen.workflows.knowledge.kb_manager import KnowledgeBaseManager

# 创建embedding配置
embedding_config = EmbeddingConfigBase(
    name="My Embedding Config",
    provider=EmbeddingProvider.OPENAI,
    model_id="text-embedding-3-small",
    api_key="sk-...",
    base_url="https://api.openai.com/v1",
    dimensions=1536,
)

# 使用配置创建知识库管理器
kb_manager = KnowledgeBaseManager(
    user_id="user123",
    session_id="session456",
    embedding_config=embedding_config
)

# 添加和搜索文档
await kb_manager.add_document("文档内容", {"source": "doc1.txt"})
results = await kb_manager.search("搜索查询")
```

### 3. 使用默认配置

```python
from sqlmodel import select
from slidegen.models.embedding_config import EmbeddingConfigModel

# 在API路由中获取用户的默认配置
async def get_user_default_embedding(session, user_id):
    statement = select(EmbeddingConfigModel).where(
        EmbeddingConfigModel.user_id == user_id,
        EmbeddingConfigModel.is_default == True,
        EmbeddingConfigModel.is_active == True
    )
    return (await session.execute(statement)).scalars().first()

# 使用默认配置
default_config = await get_user_default_embedding(session, current_user.id)
if default_config:
    kb_manager = KnowledgeBaseManager(
        user_id=str(current_user.id),
        embedding_config=default_config
    )
```

## 数据库迁移

新增了 `embedding_configs` 表，包含以下字段：

- `id` (UUID): 主键
- `user_id` (UUID): 外键，关联到users表
- `name` (String): 配置名称
- `provider` (Enum): Provider类型
- `model_id` (String): 模型ID
- `api_key` (String): API密钥（返回时会掩码）
- `base_url` (String): API基础URL
- `dimensions` (Integer): Embedding维度（可选）
- `description` (String): 描述
- `extra_params` (JSON): 额外参数
- `is_active` (Boolean): 是否启用
- `is_default` (Boolean): 是否为默认配置
- `create_time` (DateTime): 创建时间
- `update_time` (DateTime): 更新时间

运行数据库迁移（使用Alembic）：

```bash
alembic revision --autogenerate -m "Add embedding_configs table"
alembic upgrade head
```

## 安全性

1. **API密钥保护**:
   - API返回配置时，API密钥会被掩码（只显示最后4位）
   - 数据库中建议加密存储API密钥

2. **用户隔离**:
   - 每个用户只能访问自己的配置
   - API会验证配置所有权

3. **配置验证**:
   - 创建和更新配置前会进行参数验证
   - 可选的测试功能验证配置是否可用

## 配置参数说明

### dimensions (embedding维度)

- 对于OpenAI的text-embedding-3系列，可以通过设置dimensions参数来获取更小的embedding
- 如果不设置，使用模型的默认维度
- 示例：
  - text-embedding-3-large: 默认3072，可设置256-3072之间的值
  - text-embedding-3-small: 默认1536，可设置256-1536之间的值

### extra_params (额外参数)

用于传递特定provider需要的额外参数：

**Azure OpenAI**:
```json
{
  "azure_deployment": "your-deployment-name",
  "api_version": "2023-05-15"
}
```

## 最佳实践

1. **使用测试端点**: 在保存配置前，使用测试端点验证配置是否正确
2. **设置描述**: 为每个配置添加描述，便于区分不同用途的配置
3. **默认配置**: 为常用场景设置默认配置，简化代码
4. **维度选择**: 根据实际需求选择合适的embedding维度，更小的维度可以节省存储和计算成本
5. **Base URL**: 如果使用代理或自定义服务，确保正确配置base_url

## 迁移指南

如果你之前使用环境变量配置embedding，现在可以迁移到新系统：

### 旧方式（环境变量）:
```bash
export OPENAI_EMBEDDING_MODEL=text-embedding-3-small
export OPENAI_API_KEY=sk-...
export OPENAI_BASE_URL=https://api.openai.com/v1
```

```python
kb_manager = KnowledgeBaseManager(
    user_id="user123",
    session_id="session456"
    # 不传embedding_config，使用环境变量
)
```

### 新方式（用户配置）:
```python
from slidegen.models.embedding_config import EmbeddingConfigBase, EmbeddingProvider

embedding_config = EmbeddingConfigBase(
    name="My OpenAI Embedding",
    provider=EmbeddingProvider.OPENAI,
    model_id="text-embedding-3-small",
    api_key="sk-...",
    base_url="https://api.openai.com/v1",
)

kb_manager = KnowledgeBaseManager(
    user_id="user123",
    session_id="session456",
    embedding_config=embedding_config
)
```

## 故障排除

### 1. 配置测试失败

检查：
- API密钥是否正确
- base_url是否可访问
- model_id是否存在
- 网络连接是否正常

### 2. Ollama连接失败

确保：
- Ollama服务正在运行
- base_url指向正确的Ollama地址（默认http://localhost:11434）
- 已经下载了指定的模型（使用`ollama pull model-name`）

### 3. Azure OpenAI配置失败

需要提供：
- 正确的azure_endpoint（base_url）
- azure_deployment名称（在extra_params中）
- api_version（在extra_params中）

## 更多信息

- 查看 `examples/embedding_config_example.py` 获取完整的使用示例
- 参考 `slidegen/models/embedding_config.py` 了解数据模型
- 查看 `slidegen/api/routers/embedding_config.py` 了解API实现
