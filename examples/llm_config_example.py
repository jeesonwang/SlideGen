"""
大模型配置系统使用示例
"""

import asyncio

from slidegen.factories.llm_factory import LLMFactory
from slidegen.models.llm_config import LLMProvider
from slidegen.schemas.llm_config import LLMConfigTest


async def test_openai_config() -> None:
    """测试 OpenAI 配置"""
    print("测试 OpenAI 配置...")

    config = LLMConfigTest(
        provider=LLMProvider.OPENAI,
        model_id="gpt-4o-mini",
        api_key="your-openai-api-key",  # 请替换为真实的 API 密钥
        base_url="https://api.openai.com/v1",
        temperature=0.7,
        test_prompt="介绍一下人工智能",
    )

    # 验证配置
    is_valid, error = LLMFactory.validate_config(config)
    if not is_valid:
        print(f"配置验证失败: {error}")
        return

    # 测试连接
    result = await LLMFactory.test_llm_config(config)
    print(f"测试结果: {result}")


async def test_openrouter_config() -> None:
    """测试 OpenRouter 配置"""
    print("\n测试 OpenRouter 配置...")

    config = LLMConfigTest(
        provider=LLMProvider.OPENROUTER,
        model_id="openai/gpt-4o-mini",
        api_key="your-openrouter-api-key",  # 请替换为真实的 API 密钥
        temperature=0.7,
        test_prompt="什么是机器学习？",
    )

    # 验证配置
    is_valid, error = LLMFactory.validate_config(config)
    if not is_valid:
        print(f"配置验证失败: {error}")
        return

    # 测试连接
    result = await LLMFactory.test_llm_config(config)
    print(f"测试结果: {result}")


async def test_anthropic_config() -> None:
    """测试 Anthropic 配置"""
    print("\n测试 Anthropic 配置...")

    config = LLMConfigTest(
        provider=LLMProvider.ANTHROPIC,
        model_id="claude-3-5-sonnet-20241022",
        api_key="your-anthropic-api-key",  # 请替换为真实的 API 密钥
        base_url="https://api.anthropic.com",
        temperature=0.7,
        test_prompt="解释一下深度学习的基本原理",
    )

    # 验证配置
    is_valid, error = LLMFactory.validate_config(config)
    if not is_valid:
        print(f"配置验证失败: {error}")
        return

    # 测试连接
    result = await LLMFactory.test_llm_config(config)
    print(f"测试结果: {result}")


async def test_ollama_config() -> None:
    """测试 Ollama 配置"""
    print("\n测试 Ollama 配置...")

    config = LLMConfigTest(
        provider=LLMProvider.OLLAMA,
        model_id="llama3.1:8b",
        base_url="http://localhost:11434",
        temperature=0.7,
        test_prompt="你好，请介绍一下自己",
    )

    # 验证配置
    is_valid, error = LLMFactory.validate_config(config)
    if not is_valid:
        print(f"配置验证失败: {error}")
        return

    # 测试连接
    result = await LLMFactory.test_llm_config(config)
    print(f"测试结果: {result}")


async def main() -> None:
    """主函数"""
    print("=== 大模型配置系统测试 ===\n")

    # 注意: 请在测试前替换为真实的API密钥
    # 或者注释掉不需要测试的配置

    try:
        # 测试各种配置
        # await test_openai_config()
        # await test_openrouter_config()
        # await test_anthropic_config()
        # await test_ollama_config()

        print("\n所有测试完成！")

    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
