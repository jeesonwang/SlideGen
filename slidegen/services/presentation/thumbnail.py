"""Thumbnail generation service for PPTX templates.

Uses LibreOffice to convert PPTX to PDF, then PyMuPDF to render the first page as PNG.
"""

import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

import fitz  # PyMuPDF
from loguru import logger

from slidegen.core.config import settings


class ThumbnailGenerationError(Exception):
    """Exception raised when thumbnail generation fails."""

    pass


class LibreOfficeNotFoundError(ThumbnailGenerationError):
    """Exception raised when LibreOffice is not installed."""

    pass


class ThumbnailGenerator:
    """Generates thumbnails for PPTX templates using LibreOffice and PyMuPDF."""

    def __init__(
        self,
        templates_dir: Path | None = None,
        thumbnails_dir: Path | None = None,
        thumbnail_width: int | None = None,
    ):
        self.templates_dir = templates_dir or (settings.COMPONENTS_BASE_PATH / "templates")
        self.thumbnails_dir = thumbnails_dir or settings.THUMBNAILS_DIR
        self.thumbnail_width = thumbnail_width or settings.THUMBNAIL_WIDTH

        # Ensure thumbnails directory exists
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)

        # Cache the LibreOffice path
        self._libreoffice_path: str | None = None

    def _find_libreoffice(self) -> str:
        """Find the LibreOffice executable path.

        Returns:
            Path to the LibreOffice executable.

        Raises:
            LibreOfficeNotFoundError: If LibreOffice is not found.
        """
        if self._libreoffice_path:
            return self._libreoffice_path

        system = platform.system()

        # Common paths for LibreOffice
        if system == "Darwin":  # macOS
            candidates = [
                "/Applications/LibreOffice.app/Contents/MacOS/soffice",
                "/opt/homebrew/bin/soffice",
                "/usr/local/bin/soffice",
            ]
        elif system == "Linux":
            candidates = [
                "/usr/bin/libreoffice",
                "/usr/bin/soffice",
                "/usr/local/bin/libreoffice",
                "/usr/local/bin/soffice",
            ]
        elif system == "Windows":
            candidates = [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            ]
        else:
            candidates = []

        # Also check if soffice or libreoffice is in PATH
        for cmd in ["soffice", "libreoffice"]:
            path = shutil.which(cmd)
            if path:
                self._libreoffice_path = path
                logger.debug(f"Found LibreOffice at: {path}")
                return path

        # Check predefined paths
        for candidate in candidates:
            if Path(candidate).exists():
                self._libreoffice_path = candidate
                logger.debug(f"Found LibreOffice at: {candidate}")
                return candidate

        raise LibreOfficeNotFoundError(
            "LibreOffice is not installed or not found. "
            "Please install LibreOffice: https://www.libreoffice.org/download/"
        )

    def _convert_pptx_to_pdf(self, pptx_path: Path, output_dir: Path) -> Path:
        """Convert PPTX file to PDF using LibreOffice.

        Args:
            pptx_path: Path to the PPTX file.
            output_dir: Directory to save the PDF.

        Returns:
            Path to the generated PDF file.

        Raises:
            ThumbnailGenerationError: If conversion fails.
        """
        libreoffice = self._find_libreoffice()

        # LibreOffice command to convert to PDF
        cmd = [
            libreoffice,
            "--headless",
            "--invisible",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_dir),
            str(pptx_path),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,  # 60 second timeout
            )

            if result.returncode != 0:
                logger.error(f"LibreOffice conversion failed: {result.stderr}")
                raise ThumbnailGenerationError(f"LibreOffice conversion failed: {result.stderr}")

            # The output PDF will have the same name as the input with .pdf extension
            pdf_path = output_dir / f"{pptx_path.stem}.pdf"

            if not pdf_path.exists():
                raise ThumbnailGenerationError(f"PDF file not created: {pdf_path}")

            return pdf_path

        except subprocess.TimeoutExpired:
            raise ThumbnailGenerationError("LibreOffice conversion timed out")
        except FileNotFoundError:
            raise LibreOfficeNotFoundError(f"LibreOffice executable not found at: {libreoffice}")

    def _render_pdf_first_page(self, pdf_path: Path, output_path: Path, width: int) -> None:
        """Render the first page of a PDF as PNG.

        Args:
            pdf_path: Path to the PDF file.
            output_path: Path to save the PNG thumbnail.
            width: Target width in pixels.

        Raises:
            ThumbnailGenerationError: If rendering fails.
        """
        try:
            doc = fitz.open(pdf_path)
            if len(doc) == 0:
                raise ThumbnailGenerationError("PDF has no pages")

            page = doc[0]

            # Calculate zoom factor to achieve target width
            zoom = width / page.rect.width
            matrix = fitz.Matrix(zoom, zoom)

            # Render page to pixmap
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)

            # Save as PNG
            pixmap.save(str(output_path))

            doc.close()
            logger.debug(f"Thumbnail saved to: {output_path}")

        except fitz.FileDataError as e:
            raise ThumbnailGenerationError(f"Failed to open PDF: {e}")

    def is_thumbnail_valid(self, template_name: str) -> bool:
        """Check if a cached thumbnail is still valid.

        A thumbnail is valid if:
        1. The thumbnail file exists
        2. The thumbnail was created after the template was last modified

        Args:
            template_name: Name of the template (e.g., "general").

        Returns:
            True if the thumbnail is valid, False otherwise.
        """
        thumbnail_path = self.thumbnails_dir / f"{template_name}.png"
        template_path = self.templates_dir / f"template_{template_name}.pptx"

        if not thumbnail_path.exists():
            return False

        if not template_path.exists():
            return False

        # Compare modification times
        thumbnail_mtime = thumbnail_path.stat().st_mtime
        template_mtime = template_path.stat().st_mtime

        return thumbnail_mtime > template_mtime

    def generate_thumbnail(self, template_name: str, force: bool = False) -> Path:
        """Generate a thumbnail for a template.

        Args:
            template_name: Name of the template (e.g., "general").
            force: If True, regenerate even if cached thumbnail is valid.

        Returns:
            Path to the thumbnail PNG file.

        Raises:
            FileNotFoundError: If the template does not exist.
            LibreOfficeNotFoundError: If LibreOffice is not installed.
            ThumbnailGenerationError: If generation fails.
        """
        thumbnail_path = self.thumbnails_dir / f"{template_name}.png"
        template_path = self.templates_dir / f"template_{template_name}.pptx"

        # Check if template exists
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        # Check cache validity
        if not force and self.is_thumbnail_valid(template_name):
            logger.debug(f"Using cached thumbnail for: {template_name}")
            return thumbnail_path

        logger.info(f"Generating thumbnail for template: {template_name}")

        # Use temporary directory for intermediate files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Convert PPTX to PDF
            pdf_path = self._convert_pptx_to_pdf(template_path, temp_path)

            # Render first page to PNG
            self._render_pdf_first_page(pdf_path, thumbnail_path, self.thumbnail_width)

        logger.info(f"Thumbnail generated: {thumbnail_path}")
        return thumbnail_path

    def get_thumbnail_path(self, template_name: str) -> Path | None:
        """Get the path to a cached thumbnail without generating.

        Args:
            template_name: Name of the template.

        Returns:
            Path to thumbnail if it exists, None otherwise.
        """
        thumbnail_path = self.thumbnails_dir / f"{template_name}.png"
        if thumbnail_path.exists():
            return thumbnail_path
        return None


# Singleton instance
thumbnail_generator = ThumbnailGenerator()
