import traceback
from typing import Any, cast

from agno.agent import Agent
from agno.knowledge.embedder.base import Embedder
from agno.models.base import Model
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.workflow import Loop, Step, Workflow
from agno.workflow.types import StepInput, StepOutput
from loguru import logger
from sqlmodel import select

from slidegen.core.database import AsyncSessionLocal
from slidegen.models.embedding_config import EmbeddingConfigModel
from slidegen.models.llm_config import LLMConfigModel
from slidegen.schemas.gen_request import GeneratePresentationRequest, LLMConfigRequest
from slidegen.services.document.file_processor import FileProcessor
from slidegen.services.document.markdown import MarkdownDocument
from slidegen.services.factories import EmbeddingFactory, LLMFactory
from slidegen.services.knowledge.kb_manager import KnowledgeBaseManager

# Maximum number of sections to generate
MAX_ITERATIONS = 35


async def get_llm_instance(request: GeneratePresentationRequest | LLMConfigRequest) -> Model:
    """Get LLM instance based on request parameters"""
    try:
        # If user ID is specified, try to get user's LLM configuration
        if isinstance(request, GeneratePresentationRequest):
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
                else:
                    raise ValueError("No active LLM configuration found")

        elif isinstance(request, LLMConfigRequest):
            return LLMFactory.create_llm(request)

    except Exception as e:
        logger.warning(f"Failed to get LLM instance, using default configuration: {e!s}")
        return OpenAIChat(id="gpt-4o-mini")


async def get_embedding_instance(request: GeneratePresentationRequest) -> Embedder | None:
    """Get embedder instance based on request parameters"""
    try:
        async with AsyncSessionLocal() as session:
            # If embedding_config_id is specified, try to get the configuration
            if request.embedding_config_id:
                config = await session.get(EmbeddingConfigModel, request.embedding_config_id)
                if config and config.user_id == request.user_id and config.is_active:
                    return EmbeddingFactory.create_embedder(config)

            # Otherwise use user's default configuration
            statement = select(EmbeddingConfigModel).where(
                EmbeddingConfigModel.user_id == request.user_id,
                EmbeddingConfigModel.is_default == True,  # noqa: E712
                EmbeddingConfigModel.is_active == True,  # noqa: E712
            )
            config = (await session.execute(statement)).scalars().first()
            if config:
                return EmbeddingFactory.create_embedder(config)

    except Exception as e:
        logger.warning(f"Failed to get embedder instance: {e!s}")

    return None


class SlideGenWorkflow:
    """SlideGenWorkflow class"""

    def __init__(
        self,
        outline_agent: Agent,
        content_agent: Agent,
        summary_agent: Agent | None = None,
        kb_manager: KnowledgeBaseManager | None = None,
    ) -> None:
        self.outline_agent = outline_agent
        self.content_agent = content_agent
        self.summary_agent = summary_agent
        self.kb_manager = kb_manager

    @classmethod
    async def from_request(
        cls,
        request: GeneratePresentationRequest,
        llm: Model | None = None,
        embedder: Embedder | None = None,
    ) -> "SlideGenWorkflow":
        """
        Create workflow instance from GeneratePresentationRequest

        Args:
            request: Presentation generation request
            session_id: Session ID (from validated SessionModel)
            llm: Optional LLM instance
            embedder: Optional embedder instance

        Returns:
            SlideGenWorkflow instance
        """

        if llm is None:
            llm = await get_llm_instance(request)
        session_id = request.session_id
        # create knowledge base manager(if there are files)
        kb_manager = None
        if request.files and len(request.files) > 0:
            # Use persisted session ID instead of random UUID
            # Get embedder instance
            if embedder is None:
                embedder = await get_embedding_instance(request)
            kb_manager = KnowledgeBaseManager(
                user_id=str(request.user_id), session_id=str(session_id) if session_id else None, embedder=embedder
            )

            # extract file content and index to knowledge base
            file_processor = FileProcessor(session_id=str(session_id) if session_id else None)
            try:
                await file_processor.extract_and_index_content(
                    request, kb_manager, str(request.user_id), str(session_id) if session_id else None
                )
                logger.info(
                    f"Successfully indexed {len(request.files)} files to knowledge base for session {session_id}"
                )
            except Exception as e:
                logger.error(f"Failed to index files to knowledge base: {e}")
                raise ValueError(f"Failed to parse and index uploaded files: {e}") from e

        tone_instructions = {
            "default": "Use a neutral, professional tone",
            "casual": "Use a friendly, conversational tone",
            "professional": "Use a formal, professional tone",
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
                "If a 'Knowledge Base Summary' section is provided, use it as the primary source of information for the outline.",
                "The knowledge base summary contains comprehensive information synthesized from reference documents.",
                "Decompose the outline into multiple independent sections.",
                "Each section should contain a clear title.",
                f"Create exactly {request.n_slides} slides/sections.",
                "Ensure the outline covers all important topics mentioned in the knowledge base summary.",
                f"Always respond in {request.language}",
            ],
            expected_output=(
                "Output the content outline for this PowerPoint section in Markdown, using headings up to level 3 only. Do not use level-4 or deeper headings.\n"
                "Must follow:\n"
                "- Top-level (#): Use the current section title and include it exactly once\n"
                "- Second-level (##): Split this section into 1-4 clear subsections\n"
                "- Third-level (###): For each subsection, provide 1-4 key points based on the content's depth and relevance\n"
                "- Output Markdown only; do not add explanations, prefixes, or unrelated text\n"
                "Example structure (illustrative; do not copy the content):\n"
                "# PowerPoint Title\n"
                "## Subsection A\n"
                "### Key point 1\n"
                "### Key point 2\n"
                "## Subsection B\n"
                "### Key point 1\n"
                "### Key point 2\n"
                "### Key point 3\n"
            ),
            model=llm,
        )

        content_agent = Agent(
            name="Content writing expert",
            tools=[DuckDuckGoTools()] if request.web_search else [],  # Use duckduckgo to search the internet
            knowledge=kb_manager.knowledge if kb_manager else None,
            add_knowledge_to_context=True,
            description="You are a content writing expert. You are responsible for writing detailed content for the provided section titles and key points.",
            instructions=[
                "Write detailed content based on the provided section titles and key points",
                "Ensure the content matches the specified tone and verbosity",
                "Use web search tools if enabled to get relevant information support",
                "When reference content is provided, use it to support your writing and ensure accuracy",
                "Incorporate information from the reference sources naturally into your content",
                "Ensure the content is detailed and accurate",
                f"Always respond in {request.language}",
                *base_instructions,
            ],
            expected_output=(
                "You must strictly maintain the original outline structure provided in the input:\n"
                "- Keep all heading levels (##, ###) exactly as given\n"
                "- Do NOT change, add, or remove any headings\n"
                "- Do NOT add numbered lists or bullet points under level-3 headings (###)\n"
                "- Write content directly as paragraph text under each heading\n"
                "- Output Markdown only; do not add explanations, prefixes, or unrelated text\n"
                "\n"
                "Example:\n"
                "Input:\n"
                "## Section A\n"
                "### Key point 1\n"
                "### Key point 2\n"
                "\n"
                "Output:\n"
                "## Section A\n"
                "### Key point 1\n"
                "Write detailed paragraph content here without using numbered lists or bullet points.\n"
                "### Key point 2\n"
                "Write detailed paragraph content here without using numbered lists or bullet points.\n"
            ),
            model=llm,
        )

        # summary agent(only used when there is a knowledge base)
        summary_agent = None
        if kb_manager:
            summary_agent = Agent(
                name="Knowledge summarization expert",
                description="You are a knowledge summarization expert. You synthesize information from multiple document fragments into coherent, comprehensive summaries.",
                instructions=[
                    "Read and analyze all provided document fragments carefully",
                    "Identify the main themes, key concepts, and important details",
                    "Synthesize the information into a coherent, well-structured summary",
                    "Preserve important facts, figures, and specific details",
                    "Eliminate redundancy while maintaining completeness",
                    "Organize the summary logically to facilitate outline generation",
                    f"Always respond in {request.language}",
                ],
                expected_output=(
                    "Provide a comprehensive summary that:\n"
                    "- Captures all main topics and themes from the documents\n"
                    "- Preserves specific details, data, and examples\n"
                    "- Organizes information in a logical structure\n"
                    "- Is coherent and easy to understand\n"
                    "- Output in clear paragraph form or structured markdown\n"
                    "- Do not add explanations or meta-commentary about the summarization process\n"
                ),
                model=llm,
            )
            logger.info("Created summary agent for knowledge base processing")

        return cls(
            outline_agent=outline_agent,
            content_agent=content_agent,
            summary_agent=summary_agent,
            kb_manager=kb_manager,
        )

    create = from_request

    async def outline_processor(self, step_input: StepInput) -> StepOutput:
        """Generate the outline using a two-stage approach: retrieve → summarize → generate outline."""

        execution_input = cast(GeneratePresentationRequest, step_input.input)
        content = execution_input.content

        if self.kb_manager and self.summary_agent:
            try:
                logger.debug("Stage 1: Retrieving relevant documents from knowledge base")
                relevant_docs: list[dict[str, Any]] = await self.kb_manager.search(
                    query=content,
                    limit=25,  # retrieve top 25 relevant fragments to get a comprehensive understanding
                )

                if relevant_docs:
                    logger.debug(f"Retrieved {len(relevant_docs)} relevant documents for summarization")

                    logger.debug("Stage 2: Summarizing retrieved documents")
                    # build the prompt for summarization
                    summary_prompt_parts = [
                        f"Topic: {content}\n\n",
                        "Please synthesize the following document fragments into a comprehensive summary that will be used to create a presentation outline:\n\n",
                    ]

                    for idx, result in enumerate(relevant_docs, 1):
                        summary_prompt_parts.append(f"--- Fragment {idx} ---\n{result['content']}\n\n")

                    summary_prompt_parts.append(
                        "\nPlease provide a comprehensive summary that captures all main topics, key concepts, and important details from these fragments."
                    )

                    summary_prompt = "".join(summary_prompt_parts)

                    summary_response = await self.summary_agent.arun(summary_prompt)
                    knowledge_summary = str(
                        summary_response.content if hasattr(summary_response, "content") else summary_response
                    )

                    logger.info("Successfully generated knowledge summary")
                    logger.debug(f"Summary length: {len(str(knowledge_summary))} characters")

                    logger.debug("Stage 3: Generating outline based on summary")
                    # add the knowledge summary to the Knowledge Base
                    await self.kb_manager.add_document(knowledge_summary, metadata={"source": "Knowledge Base Summary"})
                    content = f"{content}\n\n## Knowledge Base Summary\n\n{knowledge_summary}"

                else:
                    logger.warning("No relevant documents found in knowledge base")

            except Exception as e:
                # if error, continue using original topic(content）
                logger.error(f"Failed to process knowledge base: {e} {traceback.format_exc()}")
                raise e

        outline = await self.outline_agent.arun(content)
        return StepOutput(content=outline.content, success=True)

    async def section_processor(self, step_input: StepInput) -> StepOutput:
        """Process each section in the outline."""

        if step_input.additional_data is None:
            step_input.additional_data = {}

        # Only parse outline and extract sections on the first iteration
        if "sections" not in step_input.additional_data:
            outline = step_input.get_step_content("Outline generation")
            execution_input = cast(GeneratePresentationRequest, step_input.input)

            # Parse the outline, extract each section
            doc = self.parse_outline(outline)
            if doc.main is None:
                return StepOutput(content="No main section found", success=False)
            sections = [section for section in doc.main.children]

            # If the number of sections does not match the expected number, adjust it
            if len(sections) != execution_input.n_slides:
                logger.warning(f"Expected {execution_input.n_slides} sections, got {len(sections)}")

            # Save sections to additional_data for reuse
            step_input.additional_data["sections"] = sections
        else:
            # Reuse parsed sections from previous iterations
            sections = step_input.additional_data["sections"]

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
            prompt = f"{context}\n\n{current_section.element_text_source}\n{current_section.text}."

            response = await self.content_agent.arun(prompt)

            # save the current section info
            section_data = {
                "title": current_section.element_text,
                "content": response.content if hasattr(response, "content") else str(response),
                "index": current_index,
            }
            step_input.additional_data["completed_sections"].append(section_data)
            step_input.additional_data["current_section_index"] = current_index + 1

            logger.debug(f"Completed section {current_index + 1}/{len(sections)}: {current_section.element_text}")

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
        last_output = outputs[-1]
        if last_output.success and last_output.stop:
            return True
        return False

    async def merge_sections_processor(self, step_input: StepInput) -> StepOutput:
        """Merge all completed sections into a complete Markdown document"""
        try:
            # Get outline content
            outline_content = step_input.get_step_content("Outline generation")

            loop_output = step_input.get_step_output("Loop writing sections")
            if loop_output is None or loop_output.steps is None:
                return StepOutput(content="No completed sections found", success=False)
            completed_outputs: list[StepOutput] = loop_output.steps

            # Build the complete Markdown document
            markdown_parts = []

            # Parse outline to get the title (H1)
            doc = self.parse_outline(outline_content)
            if doc.main and doc.main.element_text:
                markdown_parts.append(f"{doc.main.element_text_source}\n")

            # Add each section's content
            for step in completed_outputs:
                if step.stop:
                    break
                # Add a blank line between sections for better readability
                markdown_parts.append(str(step.content))
                markdown_parts.append("\n")

            # Join all parts into a complete Markdown document
            complete_markdown = "\n".join(markdown_parts).strip()

            logger.info(f"Successfully merged {len(completed_outputs)} sections into complete Markdown document")

            return StepOutput(content=complete_markdown, success=True)

        except Exception as e:
            logger.exception(f"Failed to merge sections: {e!s}")
            return StepOutput(content=f"Failed to merge sections: {e!s}", success=False)

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
                    max_iterations=MAX_ITERATIONS,
                ),
                Step(name="Merge sections", executor=self.merge_sections_processor),
            ],
        )


async def run_slidegen_workflow(request: GeneratePresentationRequest) -> MarkdownDocument:
    """Run the slide generation workflow"""
    try:
        workflow_instance = await SlideGenWorkflow.from_request(request)
        workflow = workflow_instance.create_writing_workflow()
        result = await workflow.arun(request)
        last_step_result = result.step_results[-1]

        if isinstance(last_step_result, StepOutput):
            return SlideGenWorkflow.parse_outline(str(last_step_result.content))
        elif isinstance(last_step_result, list):
            return SlideGenWorkflow.parse_outline(str(last_step_result[-1].content))
    except Exception as e:
        logger.exception("Workflow execution failed")
        raise e
