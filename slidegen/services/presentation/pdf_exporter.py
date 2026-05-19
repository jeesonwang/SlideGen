"""PDF export service for presentations.

Converts PPTX files to PDF using LibreOffice headless.
"""

import platform
import shutil
import subprocess
from pathlib import Path

from loguru import logger


class LibreOfficeNotFoundError(Exception):
    """Raised when LibreOffice is not installed or not found."""

    pass


class PdfExportError(Exception):
    """Raised when PDF conversion fails."""

    pass


class PdfExporter:
    """Convert PPTX files to PDF using LibreOffice headless."""

    def __init__(self) -> None:
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

        # Check PATH
        for cmd in ["soffice", "libreoffice"]:
            path = shutil.which(cmd)
            if path:
                self._libreoffice_path = path
                logger.debug(f"Found LibreOffice at: {path}")
                return path

        # Check known paths
        for candidate in candidates:
            if Path(candidate).exists():
                self._libreoffice_path = candidate
                logger.debug(f"Found LibreOffice at: {candidate}")
                return candidate

        raise LibreOfficeNotFoundError(
            "LibreOffice is not installed or not found. "
            "Please install LibreOffice: https://www.libreoffice.org/download/"
        )

    def convert(self, pptx_path: str, output_path: str) -> str:
        """Convert a PPTX file to PDF using LibreOffice.

        Args:
            pptx_path: Path to the source PPTX file.
            output_path: Desired path for the output PDF file.

        Returns:
            The output path of the generated PDF.

        Raises:
            LibreOfficeNotFoundError: If LibreOffice is not installed.
            PdfExportError: If conversion fails.
        """
        libreoffice = self._find_libreoffice()
        output_dir = str(Path(output_path).parent)

        cmd = [
            libreoffice,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            output_dir,
            pptx_path,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                error_msg = "LibreOffice conversion failed"
                if result.stderr:
                    error_msg += f": {result.stderr.strip()}"
                logger.error(error_msg)
                raise PdfExportError(error_msg)

            # LibreOffice names the PDF same as input file with .pdf extension
            expected_pdf = Path(output_dir) / f"{Path(pptx_path).stem}.pdf"

            if not expected_pdf.exists():
                error_msg = f"PDF file not created at expected path: {expected_pdf}"
                logger.error(error_msg)
                raise PdfExportError(error_msg)

            # If the expected path differs from output_path, rename
            if str(expected_pdf) != output_path:
                expected_pdf.rename(output_path)

            logger.debug(f"PDF created successfully: {output_path}")
            return output_path

        except subprocess.TimeoutExpired:
            raise PdfExportError("LibreOffice conversion timed out after 120 seconds")
        except FileNotFoundError:
            raise LibreOfficeNotFoundError(f"LibreOffice executable not found at: {libreoffice}")


# Singleton instance
pdf_exporter = PdfExporter()
