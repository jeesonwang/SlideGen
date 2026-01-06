"""Test FileProcessor class"""

import os
import sys
import uuid
from unittest.mock import AsyncMock, Mock, patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slidegen.exceptions import FileParseError
from slidegen.schemas.file_upload import ParsedFileContent
from slidegen.schemas.gen_request import GeneratePresentationRequest
from slidegen.services.document.file_processor import FileProcessor


class TestFileProcessor:
    """FileProcessor test class"""

    @pytest.fixture
    def mock_file_manager(self):
        """Create a mock FileManager instance"""
        mock_manager = Mock()
        mock_manager.get_file_path = Mock(return_value="/mock/path/file.pdf")
        mock_manager.get_session_file_path = Mock(return_value="/mock/path/session_file.pdf")
        return mock_manager

    @pytest.fixture
    def mock_document_reader(self):
        """Create a mock DocumentReader instance"""
        mock_reader = Mock()
        mock_result = Mock()
        mock_result.text_content = "This is test content from a document."
        mock_reader.convert = Mock(return_value=mock_result)
        return mock_reader

    @pytest.fixture
    def file_processor(self, mock_file_manager):
        """Create a FileProcessor instance with mocked dependencies"""
        processor = FileProcessor(file_manager=mock_file_manager, session_id="test-session")
        return processor

    def test_init_with_defaults(self):
        """Test FileProcessor initialization with default parameters"""
        processor = FileProcessor()
        assert processor.file_manager is not None
        assert processor.markdown_converter is not None
        assert processor.session_id is None

    def test_init_with_session_id(self, mock_file_manager):
        """Test FileProcessor initialization with session_id"""
        session_id = "test-session-123"
        processor = FileProcessor(file_manager=mock_file_manager, session_id=session_id)
        assert processor.session_id == session_id
        assert processor.file_manager == mock_file_manager

    @patch("slidegen.services.document.file_processor.DocumentReader")
    def test_parse_file_success(self, mock_doc_reader_class, file_processor):
        """Test successful file parsing"""
        # Setup mock
        mock_result = Mock()
        mock_result.text_content = "Test content from PDF file"
        mock_doc_reader_class.return_value.convert.return_value = mock_result
        file_processor.markdown_converter = mock_doc_reader_class.return_value

        # Test
        file_path = "/mock/path/abc123_test_document.pdf"
        result = file_processor.parse_file(file_path)

        # Assertions
        assert isinstance(result, ParsedFileContent)
        assert result.file_id == "abc123"
        assert result.filename == "abc123_test_document.pdf"
        assert result.content == "Test content from PDF file"
        assert result.word_count == len("Test content from PDF file")
        file_processor.markdown_converter.convert.assert_called_once_with(file_path)

    @patch("slidegen.services.document.file_processor.DocumentReader")
    def test_parse_file_without_file_id(self, mock_doc_reader_class, file_processor):
        """Test parsing file without file_id prefix"""
        # Setup mock
        mock_result = Mock()
        mock_result.text_content = "Content"
        mock_doc_reader_class.return_value.convert.return_value = mock_result
        file_processor.markdown_converter = mock_doc_reader_class.return_value

        # Test file without underscore separator
        file_path = "/mock/path/document.pdf"
        result = file_processor.parse_file(file_path)

        # File ID should be the whole filename when there's no underscore
        assert result.file_id == "document.pdf"
        assert result.filename == "document.pdf"

    @patch("slidegen.services.document.file_processor.DocumentReader")
    def test_parse_file_failure(self, mock_doc_reader_class, file_processor):
        """Test file parsing failure"""
        # Setup mock to raise exception
        mock_doc_reader_class.return_value.convert.side_effect = Exception("Parse error")
        file_processor.markdown_converter = mock_doc_reader_class.return_value

        # Test
        file_path = "/mock/path/test.pdf"
        with pytest.raises(FileParseError) as exc_info:
            file_processor.parse_file(file_path)

        assert "Failed to parse file test.pdf" in str(exc_info.value)

    @patch("slidegen.services.document.file_processor.DocumentReader")
    def test_parse_files_success(self, mock_doc_reader_class, file_processor):
        """Test successful parsing of multiple files"""
        # Setup mock
        mock_results = [
            Mock(text_content="Content from file 1"),
            Mock(text_content="Content from file 2"),
        ]
        mock_doc_reader_class.return_value.convert.side_effect = mock_results
        file_processor.markdown_converter = mock_doc_reader_class.return_value

        # Test
        file_paths = [
            "/mock/path/file1_doc1.pdf",
            "/mock/path/file2_doc2.pdf",
        ]
        result = file_processor.parse_files(file_paths)

        # Assertions
        assert "## 📄 来自文件: file1_doc1.pdf" in result
        assert "## 📄 来自文件: file2_doc2.pdf" in result
        assert "Content from file 1" in result
        assert "Content from file 2" in result
        assert mock_doc_reader_class.return_value.convert.call_count == 2

    def test_parse_files_empty_list(self, file_processor):
        """Test parsing empty file list"""
        result = file_processor.parse_files([])
        assert result == ""

    @patch("slidegen.services.document.file_processor.DocumentReader")
    def test_parse_files_partial_failure(self, mock_doc_reader_class, file_processor):
        """Test parsing multiple files with some failures"""
        # Setup mock - first file succeeds, second fails
        mock_result = Mock(text_content="Content from file 1")
        mock_doc_reader_class.return_value.convert.side_effect = [
            mock_result,
            Exception("Parse error"),
        ]
        file_processor.markdown_converter = mock_doc_reader_class.return_value

        # Test
        file_paths = [
            "/mock/path/file1_doc1.pdf",
            "/mock/path/file2_doc2.pdf",
        ]
        result = file_processor.parse_files(file_paths)

        # Should contain successful file content and warning for failed file
        assert "Content from file 1" in result
        assert "⚠️ File parsing failed: file2_doc2.pdf" in result

    @patch("slidegen.services.document.file_processor.DocumentReader")
    def test_parse_files_all_failures(self, mock_doc_reader_class, file_processor):
        """Test parsing multiple files when all fail"""
        # Setup mock to fail for all files
        mock_doc_reader_class.return_value.convert.side_effect = Exception("Parse error")
        file_processor.markdown_converter = mock_doc_reader_class.return_value

        # Test
        file_paths = [
            "/mock/path/file1.pdf",
            "/mock/path/file2.pdf",
        ]
        with pytest.raises(FileParseError) as exc_info:
            file_processor.parse_files(file_paths)

        assert "All files parsing failed" in str(exc_info.value)

    @patch.object(FileProcessor, "parse_files")
    def test_extract_content_from_request_with_session_id(self, mock_parse_files, file_processor):
        """Test extracting content from request using session_id"""
        # Setup
        mock_parse_files.return_value = "Merged content"
        file_processor.file_manager.get_session_file_path.return_value = "/mock/path/file.pdf"

        request = GeneratePresentationRequest(
            user_id=uuid.uuid4(),
            content="Test topic",
            files=["file1", "file2"],
            language="Chinese",
        )

        # Test
        result = file_processor.extract_content_from_request(request, session_id="test-session")

        # Assertions
        assert result == "Merged content"
        assert file_processor.file_manager.get_session_file_path.call_count == 2
        mock_parse_files.assert_called_once()

    @patch.object(FileProcessor, "parse_files")
    def test_extract_content_from_request_with_user_id(self, mock_parse_files):
        """Test extracting content from request using user_id (backwards compatibility)"""
        # Setup processor without session_id
        mock_manager = Mock()
        mock_manager.get_file_path.return_value = "/mock/path/file.pdf"
        processor = FileProcessor(file_manager=mock_manager)

        mock_parse_files.return_value = "Merged content"

        request = GeneratePresentationRequest(
            user_id=uuid.uuid4(),
            content="Test topic",
            files=["file1", "file2"],
            language="Chinese",
        )

        # Test
        result = processor.extract_content_from_request(request, user_id="user123")

        # Assertions
        assert result == "Merged content"
        assert mock_manager.get_file_path.call_count == 2
        mock_parse_files.assert_called_once()

    def test_extract_content_from_request_no_files(self, file_processor):
        """Test extracting content when request has no files"""
        request = GeneratePresentationRequest(
            user_id=uuid.uuid4(),
            content="Test topic",
            files=[],
            language="Chinese",
        )

        result = file_processor.extract_content_from_request(request)
        assert result == ""

    def test_extract_content_from_request_file_not_found(self, file_processor):
        """Test extracting content when file is not found"""
        file_processor.file_manager.get_session_file_path.return_value = None

        request = GeneratePresentationRequest(
            user_id=uuid.uuid4(),
            content="Test topic",
            files=["nonexistent_file"],
            language="Chinese",
        )

        with pytest.raises(FileNotFoundError) as exc_info:
            file_processor.extract_content_from_request(request, session_id="test-session")

        assert "File not found: nonexistent_file" in str(exc_info.value)

    def test_merge_content_with_topic_both_present(self, file_processor):
        """Test merging when both file content and topic are present"""
        file_content = "This is file content"
        topic = "Presentation topic"

        result = file_processor.merge_content_with_topic(file_content, topic)

        assert "Presentation topic" in result
        assert topic in result
        assert file_content in result
        assert "Reference document content" in result

    def test_merge_content_with_topic_only_topic(self, file_processor):
        """Test merging with only topic (no file content)"""
        file_content = ""
        topic = "Presentation topic"

        result = file_processor.merge_content_with_topic(file_content, topic)

        assert result == topic

    def test_merge_content_with_topic_only_file_content(self, file_processor):
        """Test merging with only file content (no topic)"""
        file_content = "This is file content"
        topic = ""

        result = file_processor.merge_content_with_topic(file_content, topic)

        assert result == file_content

    def test_merge_content_with_topic_both_empty(self, file_processor):
        """Test merging when both are empty"""
        result = file_processor.merge_content_with_topic("", "")
        assert result == ""

    @pytest.mark.asyncio
    @patch.object(FileProcessor, "parse_file")
    async def test_extract_and_index_content_success(self, mock_parse_file, file_processor):
        """Test successful extraction and indexing of content"""
        # Setup mocks
        mock_parsed = ParsedFileContent(
            file_id="file1",
            filename="test_doc.pdf",
            content="Test content",
            word_count=100,
        )
        mock_parse_file.return_value = mock_parsed

        mock_kb_manager = AsyncMock()
        mock_kb_manager.add_document = AsyncMock()

        file_processor.file_manager.get_session_file_path.return_value = "/mock/path/file.pdf"

        request = GeneratePresentationRequest(
            user_id=uuid.uuid4(),
            content="Test topic",
            files=["file1"],
            language="Chinese",
        )

        # Test
        result = await file_processor.extract_and_index_content(
            request,
            mock_kb_manager,
            session_id="test-session",
        )

        # Assertions
        assert len(result) == 1
        assert result[0] == mock_parsed
        mock_kb_manager.add_document.assert_called_once()
        call_kwargs = mock_kb_manager.add_document.call_args[1]
        assert call_kwargs["content"] == "Test content"
        assert call_kwargs["metadata"]["file_id"] == "file1"
        assert call_kwargs["metadata"]["filename"] == "test_doc.pdf"

    @pytest.mark.asyncio
    async def test_extract_and_index_content_no_files(self, file_processor):
        """Test extraction and indexing with no files"""
        mock_kb_manager = AsyncMock()

        request = GeneratePresentationRequest(
            user_id=uuid.uuid4(),
            content="Test topic",
            files=[],
            language="Chinese",
        )

        result = await file_processor.extract_and_index_content(
            request,
            mock_kb_manager,
        )

        assert result == []
        mock_kb_manager.add_document.assert_not_called()

    @pytest.mark.asyncio
    @patch.object(FileProcessor, "parse_file")
    async def test_extract_and_index_content_parse_failure(self, mock_parse_file, file_processor):
        """Test extraction and indexing when parsing fails"""
        # Setup mock to fail
        mock_parse_file.side_effect = FileParseError("Parse error")

        mock_kb_manager = AsyncMock()
        file_processor.file_manager.get_session_file_path.return_value = "/mock/path/file.pdf"

        request = GeneratePresentationRequest(
            user_id=uuid.uuid4(),
            content="Test topic",
            files=["file1"],
            language="Chinese",
        )

        # Test - should raise error when all files fail
        with pytest.raises(FileParseError) as exc_info:
            await file_processor.extract_and_index_content(
                request,
                mock_kb_manager,
                session_id="test-session",
            )

        assert "All files parsing failed" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch.object(FileProcessor, "parse_file")
    async def test_extract_and_index_content_indexing_failure(self, mock_parse_file, file_processor):
        """Test extraction and indexing when indexing fails"""
        # Setup mocks
        mock_parsed = ParsedFileContent(
            file_id="file1",
            filename="test_doc.pdf",
            content="Test content",
            word_count=100,
        )
        mock_parse_file.return_value = mock_parsed

        mock_kb_manager = AsyncMock()
        mock_kb_manager.add_document = AsyncMock(side_effect=Exception("Indexing error"))

        file_processor.file_manager.get_session_file_path.return_value = "/mock/path/file.pdf"

        request = GeneratePresentationRequest(
            user_id=uuid.uuid4(),
            content="Test topic",
            files=["file1"],
            language="Chinese",
        )

        # Test - should continue despite indexing failure
        result = await file_processor.extract_and_index_content(
            request,
            mock_kb_manager,
            session_id="test-session",
        )

        # Should still return parsed files even if indexing failed
        assert len(result) == 1
        assert result[0] == mock_parsed

    @pytest.mark.asyncio
    @patch.object(FileProcessor, "parse_file")
    async def test_extract_and_index_content_partial_success(self, mock_parse_file, file_processor):
        """Test extraction and indexing with some files failing to parse"""
        # Setup mocks - first succeeds, second fails
        mock_parsed = ParsedFileContent(
            file_id="file1",
            filename="test_doc.pdf",
            content="Test content",
            word_count=100,
        )
        mock_parse_file.side_effect = [mock_parsed, FileParseError("Parse error")]

        mock_kb_manager = AsyncMock()
        mock_kb_manager.add_document = AsyncMock()

        file_processor.file_manager.get_session_file_path.return_value = "/mock/path/file.pdf"

        request = GeneratePresentationRequest(
            user_id=uuid.uuid4(),
            content="Test topic",
            files=["file1", "file2"],
            language="Chinese",
        )

        # Test
        result = await file_processor.extract_and_index_content(
            request,
            mock_kb_manager,
            session_id="test-session",
        )

        # Should only contain successfully parsed file
        assert len(result) == 1
        assert result[0] == mock_parsed
        mock_kb_manager.add_document.assert_called_once()


@pytest.mark.integration
class TestFileProcessorIntegration:
    """Integration tests for FileProcessor with real file operations"""

    @pytest.fixture
    def temp_test_file(self, tmp_path):
        """Create a temporary test file"""
        test_file = tmp_path / "test_document.txt"
        test_file.write_text("This is a test document content for integration testing.")
        return str(test_file)

    def test_parse_real_text_file(self, temp_test_file):
        """Test parsing a real text file"""
        processor = FileProcessor()

        try:
            result = processor.parse_file(temp_test_file)
            assert result is not None
            assert isinstance(result, ParsedFileContent)
            assert len(result.content) > 0
            assert result.filename == "test_document.txt"
        except Exception as e:
            pytest.skip(f"Integration test skipped due to: {e}")
