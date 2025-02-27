import os
import sys
project_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(project_root)
from pathlib import Path
from slidegen.core.docparse.parsers.pdf_parser import PdfParser

def test_real_conversion():
    parser = PdfParser()
    
    current_dir = Path(__file__).parent
    input_pdf = current_dir / "test.pdf"
    output_md = current_dir / "output.md"
    
    # 转换PDF
    result = parser.convert(str(input_pdf), file_extension=".pdf")
    
    if result:
        with open(output_md, "w", encoding="utf-8") as f:
            f.write(result.text_content)
        print(f"转换成功！输出文件：{output_md}")
        
        preview = result.text_content[:500] + "..." if len(result.text_content) > 500 else result.text_content
        print("\n内容预览：")
        print("-" * 50)
        print(preview)
        print("-" * 50)
    else:
        print("转换失败！")

if __name__ == "__main__":
    test_real_conversion() 