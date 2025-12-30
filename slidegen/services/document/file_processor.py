from pathlib import Path

from loguru import logger

from slidegen.exceptions import FileParseError
from slidegen.schemas.file_upload import ParsedFileContent
from slidegen.schemas.gen_request import GeneratePresentationRequest
from slidegen.services.document import DocumentReader
from slidegen.services.knowledge.kb_manager import KnowledgeBaseManager
from slidegen.utils.file import FileManager


class FileProcessor:
    """处理上传文件的解析和内容提取"""

    def __init__(self, file_manager: FileManager | None = None):
        """
        初始化文件处理器

        Args:
            file_manager: 文件管理器实例,如果为None则创建新实例
        """
        self.file_manager = file_manager or FileManager()
        self.markdown_converter = DocumentReader()
        logger.info("FileProcessor initialized")

    def parse_file(self, file_path: str) -> ParsedFileContent:
        """
        解析单个文件并返回Markdown内容

        Args:
            file_path: 文件路径

        Returns:
            ParsedFileContent对象,包含解析后的内容

        Raises:
            FileParseError: 文件解析失败
        """
        try:
            logger.info(f"Parsing file: {file_path}")

            # 使用DocumentReader解析文件
            result = self.markdown_converter.convert(file_path)

            # 提取文件名和ID
            path = Path(file_path)
            filename = path.name

            # 尝试从文件名解析file_id (格式: {file_id}_{original_filename})
            file_id = filename.split("_")[0] if "_" in filename else filename

            # 统计字数
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
            raise FileParseError(f"无法解析文件 {Path(file_path).name}: {str(e)}")

    def parse_files(self, file_paths: list[str]) -> str:
        """
        解析多个文件并合并内容

        Args:
            file_paths: 文件路径列表

        Returns:
            合并后的Markdown内容

        Raises:
            FileParseError: 文件解析失败
        """
        if not file_paths:
            return ""

        merged_content = []
        parsed_count = 0

        for file_path in file_paths:
            try:
                parsed = self.parse_file(file_path)

                # 添加文件来源标记
                file_header = f"\n\n## 📄 来自文件: {parsed.filename}\n\n"
                merged_content.append(file_header)
                merged_content.append(parsed.content)

                parsed_count += 1

            except FileParseError as e:
                logger.warning(f"Skipping file due to parse error: {e}")
                # 继续处理其他文件,不中断整个流程
                merged_content.append(f"\n\n⚠️ 文件解析失败: {Path(file_path).name}\n")

        if parsed_count == 0:
            raise FileParseError("所有文件解析均失败")

        result = "".join(merged_content)
        logger.info(f"Merged content from {parsed_count}/{len(file_paths)} files")

        return result

    def extract_content_from_request(
        self,
        request: GeneratePresentationRequest,
        user_id: str | None = None,
    ) -> str:
        """
        从GeneratePresentationRequest中提取文件内容

        Args:
            request: 演示文稿生成请求
            user_id: 用户ID(可选)

        Returns:
            提取的文件内容(Markdown格式)

        Raises:
            FileNotFoundError: 文件不存在
            FileParseError: 文件解析失败
        """
        # 检查是否有文件ID
        if not request.files or len(request.files) == 0:
            logger.info("No files provided in request")
            return ""

        logger.info(f"Extracting content from {len(request.files)} files")

        # 获取文件路径
        file_paths = []
        for file_id in request.files:
            file_path = self.file_manager.get_file_path(file_id, user_id)
            if file_path is None:
                raise FileNotFoundError(f"文件不存在: {file_id}")
            file_paths.append(file_path)

        # 解析所有文件并合并内容
        content = self.parse_files(file_paths)

        logger.info(f"Extracted {len(content)} characters from files")
        return content

    def merge_content_with_topic(self, file_content: str, topic: str) -> str:
        """
        将文件内容与主题合并

        Args:
            file_content: 从文件提取的内容
            topic: 用户提供的主题

        Returns:
            合并后的内容
        """
        if not file_content:
            return topic

        if not topic or topic.strip() == "":
            return file_content

        # 合并格式
        merged = f"""# 演示文稿主题

{topic}

---

# 参考文档内容

{file_content}
"""
        return merged

    async def extract_and_index_content(
        self,
        request: GeneratePresentationRequest,
        kb_manager: KnowledgeBaseManager,
        user_id: str | None = None,
    ) -> list[ParsedFileContent]:
        """
        从请求中提取文件内容并索引到知识库

        Args:
            request: 演示文稿生成请求
            kb_manager: 知识库管理器实例
            user_id: 用户ID(可选)

        Returns:
            解析后的文件内容列表

        Raises:
            FileNotFoundError: 文件不存在
            FileParseError: 文件解析失败
        """

        # 检查是否有文件ID
        if not request.files or len(request.files) == 0:
            logger.info("No files provided in request")
            return []

        logger.info(f"Extracting and indexing content from {len(request.files)} files")

        # 获取文件路径
        file_paths = []
        for file_id in request.files:
            file_path = self.file_manager.get_file_path(file_id, user_id)
            if file_path is None:
                raise FileNotFoundError(f"文件不存在: {file_id}")
            file_paths.append(file_path)

        # 解析所有文件
        parsed_files: list[ParsedFileContent] = []
        for file_path in file_paths:
            try:
                parsed = self.parse_file(file_path)
                parsed_files.append(parsed)
            except FileParseError as e:
                logger.warning(f"Skipping file due to parse error: {e}")
                continue

        if len(parsed_files) == 0:
            raise FileParseError("所有文件解析均失败")

        # 索引到知识库
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
                # 继续索引其他文件

        logger.info(f"Successfully indexed {len(parsed_files)} files to knowledge base")
        return parsed_files
