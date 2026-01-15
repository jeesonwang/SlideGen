from typing import Any

from loguru import logger

from .base import ContentType, DocumentParser, DocumentParseResult

try:
    from pypdf import PdfReader
    from pypdf.errors import PdfStreamError
except ImportError:
    raise ImportError("`pypdf` not installed. Please install it via `pip install pypdf`.")


class PdfParser(DocumentParser):
    """Parser for PDF files (.pdf)."""

    def __init__(self, password: str | None = None, **kwargs: Any):
        """Initialize PDF parser.

        Args:
            password: Optional password for encrypted PDFs
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(**kwargs)
        self.password = password

    @classmethod
    def get_supported_content_types(self) -> list[ContentType]:
        return [ContentType.PDF]

    def convert(self, local_path: str, **kwargs: Any) -> None | DocumentParseResult:
        # Bail if not pdf
        extension = kwargs.get("file_extension", "").lower()
        supported_extensions = [ct.value for ct in PdfParser.get_supported_content_types()]
        if extension not in supported_extensions:
            return None

        # Get password from kwargs or use instance password
        password = kwargs.get("password", self.password)

        try:
            pdf_reader = PdfReader(local_path)

            # Handle encrypted PDFs
            if pdf_reader.is_encrypted:
                if not password:
                    logger.error(f'PDF file "{local_path}" is password protected but no password provided')
                    return None

                try:
                    decrypted = pdf_reader.decrypt(password)
                    if not decrypted:
                        logger.error(f'Failed to decrypt PDF file "{local_path}": incorrect password')
                        return None
                except Exception as e:
                    logger.error(f'Error decrypting PDF file "{local_path}": {e}')
                    return None

            # Extract text from all pages
            pdf_content = []
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pdf_content.append(page_text)

            # Join all pages with double newline
            text_content = "\n\n".join(pdf_content)

            # Strip leading and trailing whitespace
            text_content = text_content.strip()

            # Try to get title from PDF metadata
            title = None
            if pdf_reader.metadata:
                title = pdf_reader.metadata.get("/Title")

            return DocumentParseResult(
                title=title,
                text_content=text_content,
            )

        except PdfStreamError as e:
            logger.error(f"Error reading PDF file '{local_path}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing PDF file '{local_path}': {e}")
            return None
