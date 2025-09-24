from typing import Any, cast

from agno.agent import Agent
from agno.models.base import Model
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.workflow import Loop, Step, Workflow
from agno.workflow.types import StepInput, StepOutput
from loguru import logger
from sqlmodel import select

from slidegen.controller.llm_factory import LLMFactory
from slidegen.engine.database import AsyncSessionLocal
from slidegen.models.llm_config import LLMConfigModel
from slidegen.schemas.gen_request import GeneratePresentationRequest


async def get_llm_instance(request: GeneratePresentationRequest) -> Model:
    """Get LLM instance based on request parameters"""
    try:
        # If user ID is specified, try to get user's LLM configuration
        if request.user_id:
            async with AsyncSessionLocal() as session:
                # Use specified configuration ID first
                if request.llm_config_id:
                    config = await session.get(LLMConfigModel, request.llm_config_id)
                    if config and config.user_id == request.user_id and config.is_active:
                        return LLMFactory.create_llm(config)

                # Otherwise use user's default configuration
                statement = select(LLMConfigModel).where(
                    LLMConfigModel.user_id == request.user_id,
                    LLMConfigModel.is_default == True,  # noqa: E712
                    LLMConfigModel.is_active == True,  # noqa: E712
                )
                config = (await session.execute(statement)).scalars().first()
                if config:
                    return LLMFactory.create_llm(config)

        return OpenAIChat(id="gpt-4o-mini")
    except Exception as e:
        logger.warning(f"Failed to get LLM instance, using default configuration: {e!s}")
        return OpenAIChat(id="gpt-4o-mini")


class SlideGenWorkflow:
    """SlideGenWorkflow class"""

    def __init__(self, outline_agent: Agent, content_agent: Agent) -> None:
        self.outline_agent = outline_agent
        self.content_agent = content_agent

    @classmethod
    async def from_request(cls, request: GeneratePresentationRequest) -> "SlideGenWorkflow":
        """Async factory: create LLM and initialize two agents based on request"""
        try:
            llm = await get_llm_instance(request)
        except Exception:
            logger.exception("LLM initialization failed")
            llm = OpenAIChat(id="gpt-4o-mini")

        outline_agent = Agent(
            name="Outline generation expert",
            instructions=[
                "Generate a detailed outline of the article based on the topic",
                "Decompose the outline into multiple independent sections",
                "Each section should contain a clear title and key points",
            ],
            model=llm,
        )

        content_agent = Agent(
            name="Content writing expert",
            tools=[DuckDuckGoTools()],
            instructions=[
                "Write detailed content based on the provided section titles and key points",
                "Use web search tools to get relevant information support",
                "Ensure the content is detailed and accurate",
            ],
            model=llm,
        )

        return cls(outline_agent=outline_agent, content_agent=content_agent)

    create = from_request

    async def outline_processor(self, step_input: StepInput) -> StepOutput:
        """生成大纲。"""
        execution_input = cast(GeneratePresentationRequest, step_input.input)
        try:
            outline = self.outline_agent.run(execution_input.content)
        except Exception as e:
            logger.exception("大纲生成失败")
            return StepOutput(content="大纲生成失败", success=False, error=str(e))
        return StepOutput(content=outline, success=True)

    async def section_processor(self, step_input: StepInput) -> StepOutput:
        """处理大纲中的每个小节。"""
        outline = step_input.get_step_content("生成大纲")

        # 解析大纲，提取各个小节
        try:
            sections = self.parse_outline(outline)
        except Exception as e:
            logger.exception("解析大纲失败")
            return StepOutput(content="解析大纲失败", success=False, error=str(e))

        # 使用官方支持的共享容器 additional_data 在 Step/Loop 间共享状态
        if step_input.additional_data is None:
            step_input.additional_data = {}

        current_index = int(step_input.additional_data.get("current_section_index", 0))

        if current_index < len(sections):
            current_section = sections[current_index]

            # 为当前小节撰写内容
            try:
                response = self.content_agent.run(f"为以下小节撰写详细内容：{current_section}")
            except Exception as e:
                logger.exception("小节内容撰写失败")
                return StepOutput(content="小节内容撰写失败", success=False, error=str(e))

            step_input.additional_data["current_section_index"] = current_index + 1

            return StepOutput(content=getattr(response, "content", response), success=True)

        return StepOutput(content="所有小节处理完成", success=True)

    @staticmethod
    def parse_outline(outline: str | dict[str, str] | None) -> list[str]:
        """将上一步产出的大纲解析为小节标题列表。"""
        if outline is None:
            return []
        if isinstance(outline, dict):
            merged = "\n".join(v for v in outline.values() if v)
        else:
            merged = outline

        lines = [line.strip() for line in merged.splitlines()]
        sections = [line for line in lines if line and not all(ch in "-=*#>·•\t " for ch in line)]
        return sections

    @staticmethod
    def check_completion(outputs: list[StepOutput]) -> bool:
        """检查是否完成所有小节的撰写。"""
        if not outputs:
            return False
        last_content = outputs[-1].content
        text = str(last_content) if last_content is not None else ""
        return "所有小节处理完成" in text

    def create_writing_workflow(self) -> Workflow:
        """创建写作工作流。"""
        return Workflow(
            name="循环撰写工作流",
            steps=[
                Step(name="生成大纲", executor=self.outline_processor),
                Loop(
                    name="循环撰写小节",
                    steps=[Step(name="处理小节", executor=self.section_processor)],
                    end_condition=self.check_completion,
                    max_iterations=10,
                ),
            ],
        )


async def run_slidegen_workflow(request: GeneratePresentationRequest) -> dict[str, Any]:
    """运行幻灯片生成工作流"""
    try:
        workflow_instance = await SlideGenWorkflow.from_request(request)
        workflow = workflow_instance.create_writing_workflow()
        result = await workflow.arun(request)
        return {"success": True, "result": result, "message": "Workflow executed successfully"}
    except Exception as e:
        logger.exception("Workflow execution failed")
        return {"success": False, "error": str(e), "message": "Workflow execution failed"}


# Example usage (for testing)
if __name__ == "__main__":
    import asyncio

    async def test_workflow() -> None:
        request = GeneratePresentationRequest(
            content="Python programming language introduction",
            template="general",
        )
        result = await run_slidegen_workflow(request)
        print(result)

    asyncio.run(test_workflow())
