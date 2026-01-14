from pathlib import Path

from loguru import logger

from slidegen.exceptions import FileParseError
from slidegen.schemas.file_upload import ParsedFileContent
from slidegen.schemas.gen_request import BaseGenerationRequest
from slidegen.services.document import DocumentReader
from slidegen.services.knowledge.kb_manager import KnowledgeBaseManager
from slidegen.utils.file import FileManager


class FileProcessor:
    """Process uploaded files and extract content"""

    def __init__(self, file_manager: FileManager | None = None, session_id: str | None = None):
        """
        Initialize file processor

        Args:
            file_manager: File manager instance, if None, a new instance will be created
            session_id: Session ID (optional), for session-scoped file lookup
        """
        self.file_manager = file_manager or FileManager()
        self.markdown_converter = DocumentReader()
        self.session_id = session_id
        logger.info(f"FileProcessor initialized with session_id: {session_id}")

    def parse_file(self, file_path: str) -> ParsedFileContent:
        """
        Parse a single file and return Markdown content

        Args:
            file_path: File path

        Returns:
            ParsedFileContent object, containing parsed content

        Raises:
            FileParseError: File parsing failed
        """
        try:
            logger.info(f"Parsing file: {file_path}")

            # Use DocumentReader to parse file
            result = self.markdown_converter.convert(file_path)

            # Extract file name and ID
            path = Path(file_path)
            filename = path.name

            # Try to parse file_id from filename (format: {file_id}_{original_filename})
            file_id = filename.split("_")[0] if "_" in filename else filename

            # Count words
            word_count = len(result.text_content)

            parsed_content = ParsedFileContent(
                file_id=file_id,
                filename=filename,
                content=result.text_content,
                word_count=word_count,
            )

            logger.info(f"Successfully parsed {filename}: {word_count} words, {len(result.text_content)} characters")

            return parsed_content

        except Exception as e:
            logger.error(f"Failed to parse file {file_path}: {e}")
            raise FileParseError(f"Failed to parse file {Path(file_path).name}: {str(e)}")

    def parse_files(self, file_paths: list[str]) -> str:
        """
        Parse multiple files and merge content

        Args:
            file_paths: File path list

        Returns:
            Merged Markdown content

        Raises:
            FileParseError: File parsing failed
        """
        if not file_paths:
            return ""

        merged_content = []
        parsed_count = 0

        for file_path in file_paths:
            try:
                parsed = self.parse_file(file_path)

                # Add file source marker
                file_header = f"\n\n## 📄 来自文件: {parsed.filename}\n\n"
                merged_content.append(file_header)
                merged_content.append(parsed.content)

                parsed_count += 1

            except FileParseError as e:
                logger.warning(f"Skipping file due to parse error: {e}")
                # Continue processing other files, without interrupting the entire process
                merged_content.append(f"\n\n⚠️ File parsing failed: {Path(file_path).name}\n")

        if parsed_count == 0:
            raise FileParseError("All files parsing failed")

        result = "".join(merged_content)
        logger.info(f"Merged content from {parsed_count}/{len(file_paths)} files")

        return result

    def extract_content_from_request(
        self,
        request: BaseGenerationRequest,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> str:
        """
        Extract file content from generation request

        Args:
            request: Generation request (GeneratePresentationRequest or GenerateMarkdownRequest)
            user_id: User ID (optional, for old user-scoped lookup)
            session_id: Session ID (optional, for new session-scoped lookup)

        Returns:
            Extracted file content (Markdown format)

        Raises:
            FileNotFoundError: File not found
            FileParseError: File parsing failed
        """
        # Check if there are file IDs
        if not request.files or len(request.files) == 0:
            logger.info("No files provided in request")
            return ""

        logger.info(f"Extracting content from {len(request.files)} files")

        # Use session_id from instance or parameter
        session_id = session_id or self.session_id

        file_paths = []
        for file_id in request.files:
            # Use session-scoped lookup if session_id is provided
            if session_id:
                file_path = self.file_manager.get_session_file_path(file_id, session_id)
            else:
                # Fallback to user-scoped lookup for backwards compatibility
                file_path = self.file_manager.get_file_path(file_id, user_id)

            if file_path is None:
                raise FileNotFoundError(f"File not found: {file_id}")
            file_paths.append(file_path)

        # Parse all files and merge content
        content = self.parse_files(file_paths)

        logger.info(f"Extracted {len(content)} characters from files")
        return content

    def merge_content_with_topic(self, file_content: str, topic: str) -> str:
        """
        Merge file content with topic

        Args:
            file_content: Extracted file content
            topic: User provided topic

        Returns:
            Merged content
        """
        if not file_content:
            return topic

        if not topic or topic.strip() == "":
            return file_content

        # Merge format
        merged = f"""# Presentation topic

                {topic}

                ---

                # Reference document content

                {file_content}
                """
        return merged

    async def extract_and_index_content(
        self,
        request: BaseGenerationRequest,
        kb_manager: KnowledgeBaseManager,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> list[ParsedFileContent]:
        """
        Extract file content from request and index to knowledge base

        Args:
            request: Generation request (GeneratePresentationRequest or GenerateMarkdownRequest)
            kb_manager: Knowledge base manager instance
            user_id: User ID (optional, for old user-scoped lookup)
            session_id: Session ID (optional, for new session-scoped lookup)

        Returns:
            Parsed file content list

        Raises:
            FileNotFoundError: File not found
            FileParseError: File parsing failed
        """

        if not request.files or len(request.files) == 0:
            logger.info("No files provided in request")
            return []

        logger.info(f"Extracting and indexing content from {len(request.files)} files")

        # Use session_id from instance or parameter
        session_id = session_id or self.session_id

        # Get file paths
        file_paths = []
        for file_id in request.files:
            # Use session-scoped lookup if session_id is provided
            if session_id:
                file_path = self.file_manager.get_session_file_path(file_id, session_id)
            else:
                # Fallback to user-scoped lookup for backwards compatibility
                file_path = self.file_manager.get_file_path(file_id, user_id)

            if file_path is None:
                raise FileNotFoundError(f"File not found: {file_id}")
            file_paths.append(file_path)

        # Parse all files
        parsed_files: list[ParsedFileContent] = []
        for file_path in file_paths:
            try:
                parsed = self.parse_file(file_path)
                parsed_files.append(parsed)
            except FileParseError as e:
                logger.warning(f"Skipping file due to parse error: {e}")
                continue

        if len(parsed_files) == 0:
            raise FileParseError("All files parsing failed")

        # Index to knowledge base
        for parsed in parsed_files:
            metadata = {
                "file_id": parsed.file_id,
                "filename": parsed.filename,
                "word_count": parsed.word_count,
                "source": "uploaded_file",
            }

            try:
                await kb_manager.add_document(
                    content=parsed.content,
                    metadata=metadata,
                )
                logger.info(f"Indexed file to knowledge base: {parsed.filename}")
            except Exception as e:
                logger.error(f"Failed to index file {parsed.filename}: {e}")
                # Continue indexing other files

        logger.info(f"Successfully indexed {len(parsed_files)} files to knowledge base")
        return parsed_files
