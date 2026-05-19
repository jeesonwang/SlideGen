"""Test SlideGen workflow"""

import uuid

import pytest
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.models.google.gemini import Gemini
from agno.models.message import Message
from agno.models.response import ModelResponse
from agno.workflow.types import StepInput, StepOutput
from loguru import logger

from slidegen.schemas.gen_request import GeneratePresentationRequest, Tone, Verbosity
from slidegen.services.document.markdown import MarkdownDocument
from slidegen.services.slidegen.workflow import SlideGenWorkflow, run_slidegen_workflow

# Fixed UUID for testing
TEST_USER_ID = uuid.UUID("12345678-1234-5678-1234-567812345678")


def test_nested_outline_groups_chapters_and_slides():
    from slidegen.services.slidegen.outline_structure import iter_chapter_slide_groups

    doc = MarkdownDocument(
        "# Deck\n"
        "## Chapter A\n"
        "### Section 1\n"
        "#### Topic 1\n"
        "Body 1\n"
        "### Section 2\n"
        "#### Topic 2\n"
        "Body 2\n"
    )

    groups = list(iter_chapter_slide_groups(doc.main))

    assert [group.chapter.element_text for group in groups] == ["Chapter A"]
    assert [slide.element_text for slide in groups[0].slides] == ["Section 1", "Section 2"]


def test_legacy_outline_keeps_h2_as_content_slide():
    from slidegen.services.slidegen.outline_structure import iter_chapter_slide_groups

    doc = MarkdownDocument(
        "# Deck\n"
        "## Legacy Slide\n"
        "### Topic 1\n"
        "Body 1\n"
    )

    groups = list(iter_chapter_slide_groups(doc.main))

    assert groups[0].chapter.element_text == "Legacy Slide"
    assert [slide.element_text for slide in groups[0].slides] == ["Legacy Slide"]


def test_nested_outline_content_slides_count_sections():
    from slidegen.services.slidegen.outline_structure import content_slides

    doc = MarkdownDocument(
        "# Deck\n"
        "## Chapter A\n"
        "### Section 1\n"
        "#### Topic 1\n"
        "Body 1\n"
        "### Section 2\n"
        "#### Topic 2\n"
        "Body 2\n"
        "## Chapter B\n"
        "### Section 3\n"
        "#### Topic 3\n"
        "Body 3\n"
    )

    sections = content_slides(doc.main)

    assert [section.element_text for section in sections] == ["Section 1", "Section 2", "Section 3"]


def test_mixed_nested_outline_keeps_sections_without_topics():
    from slidegen.services.slidegen.outline_structure import iter_chapter_slide_groups

    doc = MarkdownDocument(
        "# Deck\n"
        "## Chapter A\n"
        "### Section 1\n"
        "#### Topic 1\n"
        "Body 1\n"
        "### Section 2\n"
        "Body without explicit topic\n"
    )

    groups = list(iter_chapter_slide_groups(doc.main))

    assert groups[0].is_nested
    assert [slide.element_text for slide in groups[0].slides] == ["Section 1", "Section 2"]


async def test_merge_sections_preserves_nested_chapters():
    outline = (
        "# Deck\n"
        "## Chapter A\n"
        "### Section 1\n"
        "#### Topic 1\n"
        "## Chapter B\n"
        "### Section 2\n"
        "#### Topic 2\n"
    )
    step_input = StepInput(
        previous_step_outputs={
            "Outline generation": StepOutput(content=outline),
            "Loop writing sections": StepOutput(
                steps=[
                    StepOutput(content="### Section 1\n#### Topic 1\nBody 1"),
                    StepOutput(content="### Section 2\n#### Topic 2\nBody 2"),
                    StepOutput(content="All sections processed", stop=True),
                ]
            ),
        }
    )
    workflow = SlideGenWorkflow(outline_agent=None, content_agent=None)

    output = await workflow.merge_sections_processor(step_input)

    assert output.success
    assert output.content == (
        "# Deck\n\n"
        "## Chapter A\n\n"
        "### Section 1\n#### Topic 1\nBody 1\n\n"
        "## Chapter B\n\n"
        "### Section 2\n#### Topic 2\nBody 2"
    )


class TestSlideGenWorkflow:
    """SlideGen workflow test class"""

    @pytest.fixture
    def llm(self):
        """Create a real LLM instance for testing"""
        llm = Gemini(id="gemini-3-flash-preview")
        return llm

    @pytest.fixture
    def embedder(self):
        """Create a real embedder instance for testing (optional)"""
        # You can configure this with your preferred embedder
        # For example, using OpenAI embedder:
        return OpenAIEmbedder(api_key="dummy", id="null", base_url="http://192.168.1.144:8000/v1")

    # test embedder
    async def test_embedder(self, embedder: OpenAIEmbedder):
        """Test embedder instance creation"""
        try:
            result = embedder.get_embedding("Hello, world!")
            assert result is not None
            assert isinstance(result, list)
            assert len(result) > 0
            logger.info("Embedder test passed")
        except Exception:
            logger.exception("Embedder test failed")
            pytest.fail("Embedder test failed")

    # test llm
    async def test_llm(self, llm: Gemini):
        """Test LLM instance creation"""
        try:
            message = Message(role="user", content="Hello, world!")
            result = llm.response([message])
            assert result is not None
            assert isinstance(result, ModelResponse)
            assert len(result.content) > 0
            logger.info("LLM test passed")
        except Exception:
            logger.exception("LLM test failed")
            pytest.fail("LLM test failed")

    @pytest.fixture
    def basic_request(self) -> GeneratePresentationRequest:
        """Create a basic presentation generation request"""
        return GeneratePresentationRequest(
            content="Python编程语言介绍，包括详细的示例",
            instructions="专注于实际应用和最佳实践",
            tone=Tone.EDUCATIONAL,
            verbosity=Verbosity.STANDARD,
            web_search=False,  # Disable web search for faster testing
            n_slides=5,
            language="Chinese",
            user_id=TEST_USER_ID,
        )

    @pytest.fixture
    def web_search_request(self) -> GeneratePresentationRequest:
        """Create a request with web search enabled"""
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
        """Create a concise style request"""
        return GeneratePresentationRequest(
            content="敏捷开发方法论",
            tone=Tone.PROFESSIONAL,
            verbosity=Verbosity.CONCISE,
            web_search=False,
            n_slides=4,
            language="Chinese",
            user_id=TEST_USER_ID,
        )

    async def test_workflow_creation(self, basic_request, llm):
        """Test workflow instance creation"""
        try:
            workflow_instance = await SlideGenWorkflow.from_request(basic_request, llm=llm)
            assert workflow_instance is not None
            assert workflow_instance.outline_agent is not None
            assert workflow_instance.content_agent is not None
            # When there is no knowledge base, summary_agent should be None
            assert workflow_instance.summary_agent is None
            assert workflow_instance.kb_manager is None
            logger.info("Workflow instance created successfully")
        except Exception as e:
            logger.exception("Workflow instance creation failed")
            pytest.fail(f"Workflow creation failed: {e!s}")

    async def test_workflow_with_knowledge_base(self, llm, embedder):
        """test workflow creation with a knowledge base"""
        from unittest.mock import AsyncMock, patch

        request = GeneratePresentationRequest(
            content="Python编程语言介绍",
            tone=Tone.EDUCATIONAL,
            verbosity=Verbosity.STANDARD,
            web_search=False,
            n_slides=5,
            language="Chinese",
            user_id=TEST_USER_ID,
            files=["dummy_file_id_1", "dummy_file_id_2"],  # simulate having files
        )

        # Mock file processor to avoid actual file processing
        with patch("slidegen.services.slidegen.workflow.FileProcessor") as mock_file_processor:
            mock_instance = AsyncMock()
            mock_file_processor.return_value = mock_instance
            mock_instance.extract_and_index_content = AsyncMock()

            try:
                workflow_instance = await SlideGenWorkflow.from_request(request, llm=llm, embedder=embedder)
                assert workflow_instance is not None
                assert workflow_instance.outline_agent is not None
                assert workflow_instance.content_agent is not None
                # when there is a knowledge base, summary_agent should be created
                assert workflow_instance.summary_agent is not None
                assert workflow_instance.kb_manager is not None
                logger.info("Workflow instance with knowledge base created successfully")
                logger.info("Summary agent created for handling knowledge base content")
            except Exception as e:
                logger.exception("Workflow instance with knowledge base creation failed")
                pytest.fail(f"Workflow creation failed: {e!s}")

    async def test_parse_outline(self):
        """test outline parsing functionality"""
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
        logger.info(f"Parsed {len(sections)} sections")

        # 测试字典格式的大纲
        outline_dict = {
            "section1": "第一部分：Python基础",
            "section2": "第二部分：核心概念",
        }
        sections_dict = SlideGenWorkflow.parse_outline(outline_dict)
        assert len(sections_dict) > 0

        from slidegen.services.document.markdown import MarkdownDocument

        empty_doc = SlideGenWorkflow.parse_outline(None)
        assert isinstance(empty_doc, MarkdownDocument)
        assert len(empty_doc.contents) == 0

    async def test_basic_workflow_execution(self, basic_request, llm: Gemini):
        """test basic workflow execution"""
        try:
            result = await run_slidegen_workflow(basic_request, llm=llm)

            # Verify result is a MarkdownDocument
            assert result is not None
            assert isinstance(result, MarkdownDocument)

            # Verify the document has content
            assert len(result.main.contents) > 0 or result.main.children

            logger.info("Basic workflow execution passed")
            logger.info(f"Generated document length: {len(result.text)} characters")
            logger.info(f"Contains {len(result.main.contents)} content blocks")

        except Exception as e:
            logger.exception("Basic workflow execution failed")
            pytest.fail(f"Workflow execution failed: {e!s}")

    @pytest.mark.slow
    async def test_web_search_workflow_execution(self, web_search_request, llm):
        """test web search workflow execution (marked as slow test)"""
        try:
            result = await run_slidegen_workflow(web_search_request, llm=llm)

            assert result is not None
            assert isinstance(result, MarkdownDocument)
            assert len(result.main.contents) > 0 or result.main.children

            logger.info("Web search workflow execution passed")
            logger.info(f"Generated document length: {len(result.text)} characters")
            logger.info(f"Contains {len(result.main.contents)} content blocks")

        except Exception as e:
            logger.exception("Web search workflow execution failed")
            pytest.fail(f"Workflow execution failed: {e!s}")

    async def test_concise_workflow_execution(self, concise_request, llm):
        """test concise style workflow execution"""
        try:
            result = await run_slidegen_workflow(concise_request, llm=llm)

            assert result is not None
            assert isinstance(result, MarkdownDocument)
            assert len(result.main.contents) > 0 or result.main.children

            logger.info("Concise style workflow execution passed")
            logger.info(f"Generated document length: {len(result.text)} characters")
            logger.info(f"Contains {len(result.main.contents)} content blocks")

        except Exception as e:
            logger.exception("Concise style workflow execution failed")
            pytest.fail(f"Workflow execution failed: {e!s}")

    async def test_different_tones(self, llm):
        """test different tones"""
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
                result = await run_slidegen_workflow(request, llm=llm)
                assert result is not None
                assert isinstance(result, MarkdownDocument)
                logger.info(f"Tone {tone.value} test passed")
            except Exception as e:
                logger.exception(f"Tone {tone.value} test failed")
                pytest.fail(f"Tone {tone.value} test failed: {e!s}")

    async def test_different_verbosity_levels(self, llm):
        """test different verbosity levels"""
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
                result = await run_slidegen_workflow(request, llm=llm)
                assert result is not None
                assert isinstance(result, MarkdownDocument)
                logger.info(f"Verbosity {verbosity.value} test passed")
            except Exception as e:
                logger.exception(f"Verbosity {verbosity.value} test failed")
                pytest.fail(f"Verbosity {verbosity.value} test failed: {e!s}")

    async def test_workflow_error_handling(self, llm):
        """test workflow error handling"""
        # test invalid request (like slides number is 0)
        invalid_request = GeneratePresentationRequest(
            content="Test content",
            n_slides=0,  # may cause problems
            language="Chinese",
            user_id=TEST_USER_ID,
        )

        try:
            result = await run_slidegen_workflow(invalid_request, llm=llm)
            # even if the parameters are not ideal, the workflow should return a result
            assert result is not None
            assert isinstance(result, MarkdownDocument)
            logger.info("Error handling test completed")
        except Exception as e:
            logger.warning(f"Workflow processing exception input: {e!s}")

    async def test_workflow_with_instructions(self, llm):
        """test workflow with custom instructions"""
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
            result = await run_slidegen_workflow(request, llm=llm)
            assert result is not None
            assert isinstance(result, MarkdownDocument)
            logger.info("Custom instructions workflow test passed")
        except Exception as e:
            logger.exception("Custom instructions workflow test failed")
            pytest.fail(f"Test failed: {e!s}")

    async def test_workflow_with_real_embedder_and_llm(self, llm, embedder):
        """test workflow execution with real embedder and llm"""
        request = GeneratePresentationRequest(
            content="深度学习基础知识介绍",
            instructions="包含神经网络的基本概念和应用场景",
            tone=Tone.EDUCATIONAL,
            verbosity=Verbosity.STANDARD,
            web_search=False,
            n_slides=5,
            language="Chinese",
            user_id=TEST_USER_ID,
        )

        try:
            result = await run_slidegen_workflow(request, llm=llm, embedder=embedder)

            assert result is not None
            assert isinstance(result, MarkdownDocument)
            assert len(result.main.contents) > 0 or result.main.children

            logger.info("workflow execution with real embedder and llm passed")
            logger.info(f"generated document length: {len(result.text)} characters")
            logger.info(f"contains {len(result.main.contents)} content blocks")

        except Exception as e:
            logger.exception("workflow execution with real embedder and llm failed")
            pytest.fail(f"workflow execution failed: {e!s}")


@pytest.mark.integration
class TestWorkflowIntegration:
    """workflow integration test"""

    @pytest.fixture
    def llm(self):
        """Create a real LLM instance for integration testing"""
        llm = Gemini(id="gemini-3-flash-preview")
        return llm

    @pytest.fixture
    def embedder(self):
        """Create a real embedder instance for integration testing (optional)"""
        return OpenAIEmbedder(api_key="dummy", id="null", base_url="http://192.168.1.144:8000/v1")

    async def test_end_to_end_workflow(self, llm, embedder):
        """end to end workflow test"""
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
            result = await run_slidegen_workflow(request, llm=llm, embedder=embedder)

            # verify result structure
            assert result is not None
            assert isinstance(result, MarkdownDocument)
            assert len(result.main.contents) > 0 or result.main.children

            logger.info("End to end workflow test passed")
            logger.info(f"Generated document length: {len(result.text)} characters")
            logger.info(f"Contains {len(result.main.contents)} content blocks")

        except Exception as e:
            logger.exception("End to end workflow test failed")
            pytest.fail(f"Integration test failed: {e!s}")
