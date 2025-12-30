"""测试SlideGen工作流"""

import os
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from agno.models.openrouter import OpenRouter
from loguru import logger

from slidegen.schemas.gen_request import GeneratePresentationRequest, Tone, Verbosity
from slidegen.services.slidegen.workflow import SlideGenWorkflow, run_slidegen_workflow

# 测试用的固定 UUID
TEST_USER_ID = uuid.UUID("12345678-1234-5678-1234-567812345678")


class TestSlideGenWorkflow:
    """SlideGen工作流测试类"""

    @pytest.fixture
    def llm(self):
        llm = OpenRouter(id="z-ai/glm-4.5-air:free", api_key=os.getenv("OPENROUTER_API_KEY"), max_tokens=7896)
        return llm

    @pytest.fixture
    def mock_get_llm_instance(self, llm):
        """Mock get_llm_instance 函数"""
        with patch(
            "slidegen.services.slidegen.workflow.get_llm_instance",
            new_callable=AsyncMock,
            return_value=llm,
        ) as mock:
            yield mock

    @pytest.fixture
    def basic_request(self) -> GeneratePresentationRequest:
        """创建基础的演示文稿生成请求"""
        return GeneratePresentationRequest(
            content="Python编程语言介绍，包括详细的示例",
            instructions="专注于实际应用和最佳实践",
            tone=Tone.EDUCATIONAL,
            verbosity=Verbosity.STANDARD,
            web_search=False,  # 测试时关闭网络搜索以加快速度
            n_slides=5,
            language="Chinese",
            user_id=TEST_USER_ID,
        )

    @pytest.fixture
    def web_search_request(self) -> GeneratePresentationRequest:
        """创建启用网络搜索的请求"""
        return GeneratePresentationRequest(
            content="人工智能的最新发展趋势",
            instructions="包含最新的技术动态和实际应用案例",
            tone=Tone.PROFESSIONAL,
            verbosity=Verbosity.STANDARD,
            web_search=True,
            n_slides=6,
            language="Chinese",
            user_id=TEST_USER_ID,
        )

    @pytest.fixture
    def concise_request(self) -> GeneratePresentationRequest:
        """创建简洁风格的请求"""
        return GeneratePresentationRequest(
            content="敏捷开发方法论",
            tone=Tone.PROFESSIONAL,
            verbosity=Verbosity.CONCISE,
            web_search=False,
            n_slides=4,
            language="Chinese",
            user_id=TEST_USER_ID,
        )

    async def test_workflow_creation(self, basic_request, mock_get_llm_instance):
        """测试工作流实例创建"""
        try:
            workflow_instance = await SlideGenWorkflow.from_request(basic_request)
            assert workflow_instance is not None
            assert workflow_instance.outline_agent is not None
            assert workflow_instance.content_agent is not None
            # 没有知识库时，summary_agent应该为None
            assert workflow_instance.summary_agent is None
            assert workflow_instance.kb_manager is None
            logger.info("工作流实例创建成功")
            # 验证 mock 被调用
            mock_get_llm_instance.assert_called_once_with(basic_request)
        except Exception as e:
            logger.exception("工作流实例创建失败")
            pytest.fail(f"工作流创建失败: {e!s}")

    async def test_workflow_with_knowledge_base(self, mock_get_llm_instance):
        """测试包含知识库的工作流创建"""
        request = GeneratePresentationRequest(
            content="Python编程语言介绍",
            tone=Tone.EDUCATIONAL,
            verbosity=Verbosity.STANDARD,
            web_search=False,
            n_slides=5,
            language="Chinese",
            user_id=TEST_USER_ID,
            files=["dummy_file_id_1", "dummy_file_id_2"],  # 模拟有文件
        )

        # Mock file processor to avoid actual file processing
        with patch("slidegen.services.slidegen.workflow.FileProcessor") as mock_file_processor:
            mock_instance = AsyncMock()
            mock_file_processor.return_value = mock_instance
            mock_instance.extract_and_index_content = AsyncMock()

            try:
                workflow_instance = await SlideGenWorkflow.from_request(request)
                assert workflow_instance is not None
                assert workflow_instance.outline_agent is not None
                assert workflow_instance.content_agent is not None
                # 有知识库时，summary_agent应该被创建
                assert workflow_instance.summary_agent is not None
                assert workflow_instance.kb_manager is not None
                logger.info("包含知识库的工作流实例创建成功")
                logger.info("Summary agent已创建用于处理知识库内容")
            except Exception as e:
                logger.exception("包含知识库的工作流实例创建失败")
                pytest.fail(f"工作流创建失败: {e!s}")

    async def test_parse_outline(self):
        """测试大纲解析功能"""
        # 测试字符串格式的大纲
        outline_str = """
        # Python编程语言介绍
        ## 第一部分：Python基础
        ### 1.1 Python简介
        ### 1.2 环境搭建
        ## 第二部分：核心概念
        ### 2.1 变量和数据类型
        ### 2.2 控制流
        """
        doc = SlideGenWorkflow.parse_outline(outline_str)
        sections = [section.text for section in doc.children]
        assert len(sections) > 0
        logger.info(f"解析到 {len(sections)} 个章节")

        # 测试字典格式的大纲
        outline_dict = {
            "section1": "第一部分：Python基础",
            "section2": "第二部分：核心概念",
        }
        sections_dict = SlideGenWorkflow.parse_outline(outline_dict)
        assert len(sections_dict) > 0

        # 测试空大纲 - parse_outline返回的是MarkdownDocument对象，不是空列表
        from slidegen.services.document.markdown import MarkdownDocument

        empty_doc = SlideGenWorkflow.parse_outline(None)
        assert isinstance(empty_doc, MarkdownDocument)
        assert len(empty_doc.contents) == 0

    async def test_basic_workflow_execution(self, basic_request, mock_get_llm_instance):
        """测试基础工作流执行"""
        try:
            result = await run_slidegen_workflow(basic_request)

            assert result is not None
            assert "success" in result
            assert result["success"] is True
            assert "result" in result

            logger.info(f"工作流执行成功: {result['message']}")

            # 验证结果包含预期的步骤输出
            if result["result"]:
                logger.info(f"工作流结果: {result['result']}")

        except Exception as e:
            logger.exception("基础工作流执行失败")
            pytest.fail(f"工作流执行失败: {e!s}")

    @pytest.mark.slow
    async def test_web_search_workflow_execution(self, web_search_request, mock_get_llm_instance):
        """测试启用网络搜索的工作流执行（标记为慢速测试）"""
        try:
            result = await run_slidegen_workflow(web_search_request)

            assert result is not None
            assert "success" in result
            assert result["success"] is True

            logger.info("启用网络搜索的工作流执行成功")

        except Exception as e:
            logger.exception("网络搜索工作流执行失败")
            pytest.fail(f"工作流执行失败: {e!s}")

    async def test_concise_workflow_execution(self, concise_request, mock_get_llm_instance):
        """测试简洁风格的工作流执行"""
        try:
            result = await run_slidegen_workflow(concise_request)

            assert result is not None
            assert "success" in result
            assert result["success"] is True

            logger.info("简洁风格工作流执行成功")

        except Exception as e:
            logger.exception("简洁风格工作流执行失败")
            pytest.fail(f"工作流执行失败: {e!s}")

    async def test_different_tones(self, mock_get_llm_instance):
        """测试不同的语气风格"""
        tones_to_test = [Tone.CASUAL, Tone.PROFESSIONAL, Tone.EDUCATIONAL]

        for tone in tones_to_test:
            request = GeneratePresentationRequest(
                content="项目管理基础",
                tone=tone,
                verbosity=Verbosity.CONCISE,
                web_search=False,
                n_slides=3,
                language="Chinese",
                user_id=TEST_USER_ID,
            )

            try:
                result = await run_slidegen_workflow(request)
                assert result["success"] is True
                logger.info(f"语气风格 {tone.value} 测试通过")
            except Exception as e:
                logger.exception(f"语气风格 {tone.value} 测试失败")
                pytest.fail(f"语气风格 {tone.value} 测试失败: {e!s}")

    async def test_different_verbosity_levels(self, mock_get_llm_instance):
        """测试不同的详细程度"""
        verbosity_levels = [Verbosity.CONCISE, Verbosity.STANDARD, Verbosity.TEXT_HEAVY]

        for verbosity in verbosity_levels:
            request = GeneratePresentationRequest(
                content="数据库设计原则",
                tone=Tone.PROFESSIONAL,
                verbosity=verbosity,
                web_search=False,
                n_slides=3,
                language="Chinese",
                user_id=TEST_USER_ID,
            )

            try:
                result = await run_slidegen_workflow(request)
                assert result["success"] is True
                logger.info(f"详细程度 {verbosity.value} 测试通过")
            except Exception as e:
                logger.exception(f"详细程度 {verbosity.value} 测试失败")
                pytest.fail(f"详细程度 {verbosity.value} 测试失败: {e!s}")

    async def test_workflow_error_handling(self, mock_get_llm_instance):
        """测试工作流的错误处理"""
        # 测试无效的请求（比如slides数量为0）
        invalid_request = GeneratePresentationRequest(
            content="测试内容",
            n_slides=0,  # 可能会导致问题
            language="Chinese",
            user_id=TEST_USER_ID,
        )

        try:
            result = await run_slidegen_workflow(invalid_request)
            # 即使参数不理想，工作流也应该返回结果
            assert result is not None
            assert "success" in result
            logger.info("错误处理测试完成")
        except Exception as e:
            logger.warning(f"工作流处理异常输入: {e!s}")

    async def test_workflow_with_instructions(self, mock_get_llm_instance):
        """测试包含自定义指令的工作流"""
        request = GeneratePresentationRequest(
            content="云计算技术",
            instructions="强调安全性和成本优化，包含实际案例",
            tone=Tone.PROFESSIONAL,
            verbosity=Verbosity.STANDARD,
            web_search=False,
            n_slides=4,
            language="Chinese",
            user_id=TEST_USER_ID,
        )

        try:
            result = await run_slidegen_workflow(request)
            assert result["success"] is True
            logger.info("自定义指令工作流测试通过")
        except Exception as e:
            logger.exception("自定义指令工作流测试失败")
            pytest.fail(f"测试失败: {e!s}")


@pytest.mark.integration
class TestWorkflowIntegration:
    """工作流集成测试"""

    @pytest.fixture
    def llm(self):
        llm = OpenRouter(
            id="z-ai/glm-4.5-air:free",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        return llm

    @pytest.fixture
    def mock_get_llm_instance(self, llm):
        """Mock get_llm_instance 函数"""
        with patch(
            "slidegen.services.slidegen.workflow.get_llm_instance",
            new_callable=AsyncMock,
            return_value=llm,
        ) as mock:
            yield mock

    async def test_end_to_end_workflow(self, mock_get_llm_instance):
        """端到端工作流测试"""
        request = GeneratePresentationRequest(
            content="机器学习入门：从理论到实践",
            instructions="包含代码示例和可视化说明",
            tone=Tone.EDUCATIONAL,
            verbosity=Verbosity.STANDARD,
            web_search=False,
            n_slides=8,
            language="Chinese",
            user_id=TEST_USER_ID,
        )

        try:
            result = await run_slidegen_workflow(request)

            # 验证结果结构
            assert result is not None
            assert result["success"] is True
            assert "result" in result
            assert "message" in result

            logger.info("端到端工作流测试成功")
            logger.info(f"生成结果: {result['message']}")

        except Exception as e:
            logger.exception("端到端工作流测试失败")
            pytest.fail(f"集成测试失败: {e!s}")


if __name__ == "__main__":
    # 可以直接运行此文件进行快速测试
    import asyncio

    async def quick_test():
        """快速测试"""
        request = GeneratePresentationRequest(
            content="Python编程语言介绍",
            tone=Tone.EDUCATIONAL,
            verbosity=Verbosity.STANDARD,
            web_search=False,
            n_slides=5,
            language="Chinese",
            user_id=TEST_USER_ID,
        )

        result = await run_slidegen_workflow(request)
        logger.info(f"测试结果: {result}")

    asyncio.run(quick_test())
