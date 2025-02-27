import pdfplumber
import base64
import pandas as pd

from .base import DocumentParseResult
from .html_parser import HtmlParser

class PdfParser(HtmlParser):
    """
    Parser for PDF files.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def convert(self, local_path, **kwargs) -> None | DocumentParseResult:
        extension = kwargs.get("file_extension", "").lower()
        if extension != ".pdf":
            return None

        md_content = ""
        
        with pdfplumber.open(local_path) as pdf:
            title = pdf.metadata.get('Title', None)
            
            for page_num, page in enumerate(pdf.pages, 1):
                # 提取文本
                text = page.extract_text()
                if text:
                    md_content += text + "\n\n"
                
                # 提取表格
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        html_table = self._table_to_html(table)
                        md_content += f"\n{html_table}\n\n"
                
                # 提取图片
                images = page.images
                if images:
                    for img_num, img in enumerate(images, 1):
                        img_markdown = self._image_to_markdown(img, page_num, img_num)
                        if img_markdown:
                            md_content += img_markdown + "\n\n"

        return DocumentParseResult(
            title=title,
            text_content=md_content.strip(),
        )

    def _table_to_html(self, table) -> str:
        """
        excel to html
        """
        if not table or not table[0]:
            return ""

        df = pd.DataFrame(table)
        
        # 带样式HTML表格
        html = '<table style="border-collapse: collapse; width: 100%; margin: 10px 0;">\n'
        
        # 表头
        html += '  <thead>\n    <tr>\n'
        for header in df.iloc[0]:
            cell_content = str(header) if header is not None else ''
            html += f'      <th style="border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2; text-align: left;">{cell_content}</th>\n'
        html += '    </tr>\n  </thead>\n'
        
        # 表格内容
        html += '  <tbody>\n'
        for _, row in df.iloc[1:].iterrows():
            html += '    <tr>\n'
            for cell in row:
                cell_content = str(cell) if cell is not None else ''
                html += f'      <td style="border: 1px solid #ddd; padding: 8px;">{cell_content}</td>\n'
            html += '    </tr>\n'
        html += '  </tbody>\n'
        html += '</table>'
        
        return html

    def _image_to_markdown(self, image, page_num, img_num) -> str:
        """
        images to base64(PNG, JPEG, GIF, TIFF, BMP, ICO)
        """
        try:
            if 'stream' in image:
                img_data = image['stream'].get_data()
            elif 'image' in image:
                img_data = image['image']
            else:
                return None

            # 通过魔数（magic numbers）判断类型
            magic_numbers = {
                b'\x89PNG\r\n\x1a\n': 'image/png',
                b'\xff\xd8\xff': 'image/jpeg',
                b'GIF87a': 'image/gif',
                b'GIF89a': 'image/gif',
                b'MM\x00*': 'image/tiff',  # TIFF (big-endian)
                b'II*\x00': 'image/tiff',  # TIFF (little-endian)
                b'BM': 'image/bmp',
                b'\x00\x00\x01\x00': 'image/x-icon',
                b'\x00\x00\x02\x00': 'image/x-icon'
            }

            mime_type = 'image/png'  # 默认
            for magic, mime in magic_numbers.items():
                if img_data.startswith(magic):
                    mime_type = mime
                    break

            # 如果图片对象中包含格式信息，优先使用
            if 'format' in image:
                format_mime = {
                    'PNG': 'image/png',
                    'JPEG': 'image/jpeg',
                    'GIF': 'image/gif',
                    'TIFF': 'image/tiff',
                    'BMP': 'image/bmp',
                    'ICO': 'image/x-icon'
                }
                mime_type = format_mime.get(image['format'].upper(), mime_type)

            img_base64 = base64.b64encode(img_data).decode('utf-8')
            
            return f"![图片 {page_num}-{img_num}](data:{mime_type};base64,{img_base64})"
            
        except Exception as e:
            print(f"处理图片时出错: {e}")
            return None