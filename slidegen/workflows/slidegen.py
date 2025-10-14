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
from slidegen.workflows.docparse.markdown_parser import MarkdownDocument


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
        """从GeneratePresentationRequest创建工作流实例"""

        llm = await get_llm_instance(request)

        tone_instructions = {
            "default": "Use a neutral, professional tone",
            "casual": "Use a friendly, conversational tone",
            "professional": "Use a formal, business-like tone",
            "funny": "Use a humorous, engaging tone",
            "educational": "Use a clear, educational tone suitable for learning",
            "sales_pitch": "Use a persuasive, sales-oriented tone",
        }

        verbosity_instructions = {
            "concise": "Keep content brief and to the point",
            "standard": "Provide balanced content with sufficient detail",
            "text-heavy": "Provide comprehensive, detailed content",
        }

        base_instructions = [
            f"Generate content in {tone_instructions.get(request.tone, 'neutral, professional tone')}",
            f"Use {verbosity_instructions.get(request.verbosity, 'balanced')} level of detail",
        ]

        if request.instructions:
            base_instructions.append(f"Additional instructions: {request.instructions}")

        if request.web_search:
            base_instructions.append("Use web search to gather relevant information and facts")

        outline_agent = Agent(
            name="Outline generation expert",
            description="You are an outline generation expert. You are responsible for generating a detailed outline based on the provided content.",
            instructions=[
                "Generate a detailed outline based on the provided content.",
                "Decompose the outline into multiple independent sections.",
                "Each section should contain a clear title.",
                f"Create exactly {request.n_slides} slides/sections.",
                f"Always respond in {request.language}",
            ],
            expected_output=(
                "Output the content outline for this PowerPoint section in Markdown, using headings up to level 3 only. Do not use level-4 or deeper headings.\n"
                "Must follow:\n"
                "- Top-level (#): Use the current section title and include it exactly once\n"
                "- Second-level (##): Split this section into 1-4 clear subsections\n"
                "- Output Markdown only; do not add explanations, prefixes, or unrelated text\n"
                "Example structure (illustrative; do not copy the content):\n"
                "# PowerPoint Title\n"
                "## Subsection A\n"
                "### Key point 1\n"
                "### Key point 2\n"
                "## Subsection B\n"
                "### Key point 1\n"
                "### Key point 2\n"
            ),
            model=llm,
        )

        content_agent = Agent(
            name="Content writing expert",
            tools=[DuckDuckGoTools()] if request.web_search else [],  # Use duckduckgo to search the internet
            description="You are a content writing expert. You are responsible for writing detailed content for the provided section titles and key points.",
            instructions=[
                "Write detailed content based on the provided section titles and key points",
                "Ensure the content matches the specified tone and verbosity",
                "Use web search tools if enabled to get relevant information support",
                "Ensure the content is detailed and accurate",
                f"Always respond in {request.language}",
                *base_instructions,
            ],
            model=llm,
        )

        return cls(outline_agent=outline_agent, content_agent=content_agent)

    create = from_request

    async def outline_processor(self, step_input: StepInput) -> StepOutput:
        """Generate the outline."""
        execution_input = cast(GeneratePresentationRequest, step_input.input)
        # TODO: Input file content
        outline = self.outline_agent.run(execution_input.content)
        return StepOutput(content=outline, success=True)

    async def section_processor(self, step_input: StepInput) -> StepOutput:
        """Process each section in the outline."""

        outline = step_input.get_step_content("Outline generation")
        execution_input = cast(GeneratePresentationRequest, step_input.input)

        # Parse the outline, extract each section
        doc = self.parse_outline(outline)
        sections = [section.element_text for section in doc.children]

        # If the number of sections does not match the expected number, adjust it
        if len(sections) != execution_input.n_slides:
            logger.warning(f"Expected {execution_input.n_slides} sections, got {len(sections)}")

        if step_input.additional_data is None:
            step_input.additional_data = {}

        current_index = int(step_input.additional_data.get("current_section_index", 0))

        # initialize the completed sections
        if "completed_sections" not in step_input.additional_data:
            step_input.additional_data["completed_sections"] = []

        if current_index < len(sections):
            current_section = sections[current_index]

            # build the context with the previous sections
            completed_sections = step_input.additional_data["completed_sections"]
            context_parts = []

            if completed_sections:
                context_parts.append("The following is the content of the previous sections:\n")
                for idx, section_data in enumerate(completed_sections):
                    context_parts.append(f"\n--- Section {idx + 1}: {section_data['title']} ---")
                    context_parts.append(section_data["content"])
                context_parts.append("\n\nWrite detailed content for the following powerpoint section:")

            # Build the complete prompt
            context = "\n".join(context_parts) if context_parts else ""
            prompt = f"{context}\n\n{current_section}."

            response = self.content_agent.run(prompt)

            # save the current section info
            section_data = {
                "title": current_section,
                "content": response.content if hasattr(response, "content") else str(response),
                "index": current_index,
            }
            step_input.additional_data["completed_sections"].append(section_data)
            step_input.additional_data["current_section_index"] = current_index + 1

            logger.debug(f"Completed section {current_index + 1}/{len(sections)}: {current_section}")

            return StepOutput(content=response.content, success=True)

        return StepOutput(content="All sections processed", success=True, stop=True)

    @staticmethod
    def parse_outline(outline: str | dict[str, str] | None) -> MarkdownDocument:
        """Parse the outline into a list of sections using MarkdownDocument

        Args:
            outline: The outline text or dict to parse. Can be:
                - str: Markdown text
                - dict: Dictionary with text values
                - None: Returns empty MarkdownDocument

        Returns:
            MarkdownDocument
        """
        if outline is None:
            return MarkdownDocument(source="")

        # Convert dict to string if needed
        if isinstance(outline, dict):
            merged = "\n".join(v for v in outline.values() if v)
        else:
            merged = outline

        # Parse the outline using MarkdownDocument
        try:
            doc = MarkdownDocument(merged)

            return doc
        except Exception as e:
            # Fallback to simple line-based parsing if markdown parsing fails
            logger.exception(f"Markdown parsing failed, using fallback: {e!s}")
            raise e

    @staticmethod
    def check_completion(outputs: list[StepOutput]) -> bool:
        """Check if all sections are processed"""
        if not outputs:
            return False
        last_content = outputs[-1].content
        text = str(last_content) if last_content is not None else ""
        return "All sections processed" in text

    def create_writing_workflow(self) -> Workflow:
        """Create the writing workflow"""
        return Workflow(
            name="Loop writing workflow",
            session_state={"current_section_index": 0},
            steps=[
                Step(name="Outline generation", executor=self.outline_processor),
                Loop(
                    name="Loop writing sections",
                    steps=[Step(name="Section processing", executor=self.section_processor)],
                    end_condition=self.check_completion,
                    max_iterations=10,
                ),
            ],
        )


async def run_slidegen_workflow(request: GeneratePresentationRequest) -> dict[str, Any]:
    """Run the slide generation workflow"""
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
    from slidegen.schemas.gen_request import GeneratePresentationRequest, Tone, Verbosity

    async def test_workflow() -> None:
        """Test the workflow"""
        request = GeneratePresentationRequest(
            content="Python programming language introduction with detailed examples",
            instructions="Focus on practical applications and best practices",
            tone=Tone.EDUCATIONAL,
            verbosity=Verbosity.STANDARD,
            web_search=True,
            n_slides=8,
            language="English",
        )
        result = await run_slidegen_workflow(request)
        print("Workflow execution result:", result)

    # 也可以直接测试GeneratePresentationRequest的创建
    def test_gen_request() -> None:
        request = GeneratePresentationRequest(
            content="Python programming language introduction",
            instructions="Focus on practical applications",
            tone=Tone.EDUCATIONAL,
            verbosity=Verbosity.STANDARD,
            n_slides=8,
            web_search=True,
            language="English",
        )
        print("GeneratePresentationRequest created successfully with parameters:")
        print(f"  Content: {request.content}")
        print(f"  Instructions: {request.instructions}")
        print(f"  Tone: {request.tone}")
        print(f"  Verbosity: {request.verbosity}")
        print(f"  N_slides: {request.n_slides}")
        print(f"  Web search: {request.web_search}")

    print("Testing GeneratePresentationRequest...")
    test_gen_request()

    print("\nTesting workflow...")
    # asyncio.run(test_workflow())  # 注释掉避免实际运行
