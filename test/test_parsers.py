"""Test parsers"""

import os
from pathlib import Path

import pytest
from loguru import logger

from slidegen.workflows.docparse import DocumentReader
from slidegen.workflows.docparse.reader import (
    DocumentParseResult,
    PdfParser,
    TextParser,
)


class TestTextParser:
    """Test TextParser"""

    @pytest.fixture
    def text_parser(self):
        """Create TextParser instance"""
        return TextParser()

    @pytest.fixture
    def test_txt_file(self):
        """Test txt file path"""
        test_dir = Path(__file__).parent / "data"
        return str(test_dir / "test_sample.txt")

    def test_get_supported_content_types(self, text_parser):
        """Test get supported content types"""
        content_types = text_parser.get_supported_content_types()
        assert len(content_types) == 1
        assert content_types[0].value == ".txt"
        logger.info(f"TextParser supported content types: {[ct.value for ct in content_types]}")

    def test_convert_txt_file(self, text_parser, test_txt_file):
        """Test convert txt file"""
        if not os.path.exists(test_txt_file):
            pytest.skip(f"Test file not found: {test_txt_file}")

        result = text_parser.convert(test_txt_file, file_extension=".txt")

        assert result is not None
        assert isinstance(result, DocumentParseResult)
        assert result.text_content is not None
        assert len(result.text_content) > 0
        assert "Python" in result.text_content

        logger.info(f"Successfully parsed txt file, content length: {len(result.text_content)} characters")
        logger.debug(f"Parsed content preview: {result.text_content[:200]}...")

    def test_convert_wrong_extension(self, text_parser, test_txt_file):
        """Test wrong file extension"""
        if not os.path.exists(test_txt_file):
            pytest.skip(f"Test file not found: {test_txt_file}")

        result = text_parser.convert(test_txt_file, file_extension=".pdf")
        assert result is None
        logger.info("Successfully rejected wrong file extension")

    def test_convert_empty_file(self, text_parser, tmp_path):
        """Test empty file"""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")

        result = text_parser.convert(str(empty_file), file_extension=".txt")

        assert result is not None
        assert result.text_content == ""
        logger.info("Successfully handled empty file")

    def test_convert_file_with_unicode(self, text_parser, tmp_path):
        """Test file with Unicode characters"""
        unicode_file = tmp_path / "unicode.txt"
        unicode_content = "This is a test file\ncontains Chinese characters 🚀\nand various symbols: α β γ"
        unicode_file.write_text(unicode_content, encoding="utf-8")

        result = text_parser.convert(str(unicode_file), file_extension=".txt")

        assert result is not None
        assert "Chinese characters" in result.text_content
        assert "🚀" in result.text_content
        logger.info("Successfully handled file with Unicode characters")


class TestPdfParser:
    """Test PdfParser"""

    @pytest.fixture
    def pdf_parser(self):
        """Create PdfParser instance"""
        return PdfParser()

    @pytest.fixture
    def test_pdf_file(self):
        """Test pdf file path"""
        test_dir = Path(__file__).parent / "data"
        pdf_file = test_dir / "Introduction.to.KAG-en-tc-20241111.pdf"
        return str(pdf_file)

    def test_get_supported_content_types(self, pdf_parser):
        """Test get supported content types"""
        content_types = pdf_parser.get_supported_content_types()
        assert len(content_types) == 1
        assert content_types[0].value == ".pdf"
        logger.info(f"PdfParser supported content types: {[ct.value for ct in content_types]}")

    def test_convert_pdf_file(self, pdf_parser, test_pdf_file):
        """Test convert pdf file"""
        if not os.path.exists(test_pdf_file):
            pytest.skip(f"Test file not found: {test_pdf_file}")

        result = pdf_parser.convert(test_pdf_file, file_extension=".pdf")

        assert result is not None
        assert isinstance(result, DocumentParseResult)
        assert result.text_content is not None
        assert len(result.text_content) > 0

        logger.info(f"Successfully parsed pdf file, content length: {len(result.text_content)} characters")
        if result.title:
            logger.info(f"PDF title: {result.title}")
        logger.debug(f"Parsed content preview: {result.text_content[:200]}...")

    def test_convert_wrong_extension(self, pdf_parser, test_pdf_file):
        """Test wrong file extension"""
        if not os.path.exists(test_pdf_file):
            pytest.skip(f"Test file not found: {test_pdf_file}")

        result = pdf_parser.convert(test_pdf_file, file_extension=".txt")
        assert result is None
        logger.info("Successfully rejected wrong file extension")

    def test_convert_nonexistent_file(self, pdf_parser):
        """Test nonexistent file"""
        nonexistent_file = "/nonexistent/path/file.pdf"
        result = pdf_parser.convert(nonexistent_file, file_extension=".pdf")
        assert result is None
        logger.info("Successfully handled nonexistent file")

    def test_pdf_with_password(self, pdf_parser, tmp_path):
        """Test encrypted pdf file"""
        # Note: This test needs an encrypted pdf file
        # This is just to demonstrate how to test password functionality
        pytest.skip("Test file with password is needed")

    def test_pdf_parser_with_default_password(self):
        """Test pdf parser with default password"""
        parser_with_password = PdfParser(password="test_password")
        assert parser_with_password.password == "test_password"
        logger.info("Successfully created pdf parser with password")


class TestDocumentReader:
    """Test DocumentReader integration"""

    @pytest.fixture
    def converter(self):
        """Create DocumentReader instance"""
        return DocumentReader()

    @pytest.fixture
    def test_txt_file(self):
        """Test txt file path"""
        test_dir = Path(__file__).parent / "data"
        return str(test_dir / "test_sample.txt")

    @pytest.fixture
    def test_pdf_file(self):
        """Test pdf file path"""
        test_dir = Path(__file__).parent / "data"
        return str(test_dir / "Introduction.to.KAG-en-tc-20241111.pdf")

    def test_converter_initialization(self, converter):
        """Test converter initialization"""
        assert converter is not None
        assert len(converter.document_parsers) > 0
        logger.info(f"Converter registered {len(converter.document_parsers)} parsers")

    def test_convert_txt_file_with_converter(self, converter, test_txt_file):
        """Test using converter to convert txt file"""
        if not os.path.exists(test_txt_file):
            pytest.skip(f"Test file not found: {test_txt_file}")

        result = converter.convert_local(test_txt_file)

        assert result is not None
        assert isinstance(result, DocumentParseResult)
        assert len(result.text_content) > 0
        logger.info("DocumentReader successfully converted txt file")

    def test_convert_pdf_file_with_converter(self, converter, test_pdf_file):
        """Test using converter to convert pdf file"""
        if not os.path.exists(test_pdf_file):
            pytest.skip(f"Test file not found: {test_pdf_file}")

        result = converter.convert_local(test_pdf_file)

        assert result is not None
        assert isinstance(result, DocumentParseResult)
        assert len(result.text_content) > 0
        logger.info("DocumentReader successfully converted pdf file")

    def test_convert_with_path_object(self, converter, test_txt_file):
        """Test using Path object to convert"""
        if not os.path.exists(test_txt_file):
            pytest.skip(f"Test file not found: {test_txt_file}")

        path_obj = Path(test_txt_file)
        result = converter.convert_local(path_obj)

        assert result is not None
        assert isinstance(result, DocumentParseResult)
        logger.info("DocumentReader successfully handled Path object")

    def test_convert_multiple_files(self, converter, test_txt_file, test_pdf_file):
        """Test converting multiple different types of files"""
        files_to_test = []

        if os.path.exists(test_txt_file):
            files_to_test.append(("txt", test_txt_file))
        if os.path.exists(test_pdf_file):
            files_to_test.append(("pdf", test_pdf_file))

        if not files_to_test:
            pytest.skip("No test files available")

        for file_type, file_path in files_to_test:
            result = converter.convert_local(file_path)
            assert result is not None
            assert len(result.text_content) > 0
            logger.info(f"Successfully converted {file_type} file: {Path(file_path).name}")

    def test_convert_stream(self, converter, test_txt_file):
        """Test using stream to convert"""
        if not os.path.exists(test_txt_file):
            pytest.skip(f"Test file not found: {test_txt_file}")

        with open(test_txt_file, "rb") as fh:
            result = converter.convert_stream(fh, file_extension=".txt")

        assert result is not None
        assert isinstance(result, DocumentParseResult)
        assert len(result.text_content) > 0
        logger.info("DocumentReader successfully used stream to convert file")

    def test_parser_registration_order(self, converter):
        """Test parser registration order"""
        # Register a new parser
        custom_parser = TextParser()
        original_count = len(converter.document_parsers)

        converter.register_parser(custom_parser)

        assert len(converter.document_parsers) == original_count + 1
        # Newly registered parser should be at the beginning of the list
        assert converter.document_parsers[0] == custom_parser
        logger.info("Parser registration order correct (LIFO)")

    def test_builtin_parsers_registered(self, converter):
        """Test builtin parsers are registered"""
        parser_types = [type(parser).__name__ for parser in converter.document_parsers]

        assert "TextParser" in parser_types
        assert "PdfParser" in parser_types
        assert "HtmlParser" in parser_types
        assert "DocxParser" in parser_types
        assert "ExcelParser" in parser_types

        logger.info(f"Registered parsers: {', '.join(parser_types)}")


class TestParserEdgeCases:
    """Test parser edge cases"""

    def test_text_parser_with_very_large_file(self, tmp_path):
        """Test parsing large file"""
        parser = TextParser()
        large_file = tmp_path / "large.txt"

        # Create a larger file (about 1MB)
        large_content = "This is a test content.\n" * 50000
        large_file.write_text(large_content, encoding="utf-8")

        result = parser.convert(str(large_file), file_extension=".txt")

        assert result is not None
        assert len(result.text_content) > 0
        logger.info(f"Successfully parsed large file, size: {len(result.text_content)} characters")

    def test_text_parser_with_special_characters(self, tmp_path):
        """Test file with special characters"""
        parser = TextParser()
        special_file = tmp_path / "special.txt"

        special_content = """
        Special characters test:
        - Tab: \t\tTab
        - Newline: \n\n
        - Quotes: " " ' ' 「 」
        - Math symbols: ± × ÷ √ ∞
        - Currency symbols: $ € ¥ £
        """

        special_file.write_text(special_content, encoding="utf-8")

        result = parser.convert(str(special_file), file_extension=".txt")

        assert result is not None
        assert "Special characters test" in result.text_content
        logger.info("Successfully handled file with special characters")

    def test_converter_with_unsupported_extension(self):
        """Test unsupported file extension"""
        converter = DocumentReader()

        with pytest.raises(Exception):  # Should raise an exception
            converter.convert_local("/tmp/unsupported.xyz")
