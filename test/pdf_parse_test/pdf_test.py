import pytest
import base64
from pathlib import Path
import os
import sys
project_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(project_root)

from unittest.mock import Mock, patch
from slidegen.core.docparse.parsers.pdf_parser import PdfParser
from slidegen.core.docparse.parsers.base import DocumentParseResult

# TEST_FILES_DIR = Path(__file__).parent / "test_files"
TEST_FILES_DIR = Path(__file__).parent 

class TestPdfParser:
    @pytest.fixture
    def parser(self):
        """创建解析器实例"""
        return PdfParser()

    @pytest.fixture
    def sample_pdf_path(self):
        """准备测试用PDF文件路径"""
        return TEST_FILES_DIR / "test.pdf"

    def test_init(self, parser):
        """测试初始化"""
        assert isinstance(parser, PdfParser)

    def test_convert_wrong_extension(self, parser):
        """测试处理错误的文件扩展名"""
        result = parser.convert("test.txt", file_extension=".txt")
        assert result is None

    @pytest.mark.parametrize("file_extension", [".PDF", ".pdf"])
    def test_convert_case_insensitive(self, parser, file_extension):
        """测试文件扩展名大小写不敏感"""
        with patch("pdfplumber.open") as mock_open:
            mock_pdf = Mock()
            mock_pdf.metadata = {}
            mock_pdf.pages = []
            mock_open.return_value.__enter__.return_value = mock_pdf
            
            result = parser.convert("test.pdf", file_extension=file_extension)
            assert isinstance(result, DocumentParseResult)

    def test_image_to_markdown_png(self, parser):
        """测试PNG图片转换"""
        # 创建模拟的PNG图片数据
        png_header = b'\x89PNG\r\n\x1a\n'
        mock_image = {
            'stream': Mock(get_data=lambda: png_header + b'dummy_data')
        }
        
        result = parser._image_to_markdown(mock_image, 1, 1)
        assert result.startswith('![图片 1-1](data:image/png;base64,')

    def test_image_to_markdown_jpeg(self, parser):
        """测试JPEG图片转换"""
        jpeg_header = b'\xff\xd8\xff'
        mock_image = {
            'stream': Mock(get_data=lambda: jpeg_header + b'dummy_data')
        }
        
        result = parser._image_to_markdown(mock_image, 1, 1)
        assert result.startswith('![图片 1-1](data:image/jpeg;base64,')

    def test_table_to_html(self, parser):
        """测试表格转HTML"""
        test_table = [
            ['Header 1', 'Header 2'],
            ['Data 1', 'Data 2']
        ]
        
        html_result = parser._table_to_html(test_table)
        assert '<table' in html_result
        assert '<thead>' in html_result
        assert '<tbody>' in html_result
        assert 'Header 1' in html_result
        assert 'Data 1' in html_result

    @pytest.mark.integration
    def test_full_pdf_conversion(self, parser, sample_pdf_path):
        """集成测试：完整PDF转换"""
        if not sample_pdf_path.exists():
            pytest.skip("测试PDF文件不存在")

        result = parser.convert(str(sample_pdf_path), file_extension=".pdf")
        assert isinstance(result, DocumentParseResult)
        assert result.text_content is not None
        # 检查是否包含预期的内容（根据测试PDF文件的具体内容调整）
        assert len(result.text_content) > 0

    def test_empty_table(self, parser):
        """测试空表格处理"""
        empty_table = []
        result = parser._table_to_html(empty_table)
        assert result == ""

    def test_invalid_image_data(self, parser):
        """测试无效图片数据处理"""
        mock_image = {
            'stream': Mock(get_data=lambda: b'invalid_data')
        }
        result = parser._image_to_markdown(mock_image, 1, 1)
        assert 'image/png' in result  # 应该使用默认的PNG类型
