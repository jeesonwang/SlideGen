import subprocess
import tempfile
from pathlib import Path
from shutil import which

from loguru import logger


def is_soffice_available() -> bool:
    """Return whether LibreOffice's soffice binary is available."""
    return which("soffice") is not None


def convert_with_soffice(local_path: str, target_extension: str) -> str | None:
    """Convert a file with LibreOffice and return the converted file path."""
    if not is_soffice_available():
        logger.warning(f"LibreOffice is required to convert '{local_path}' to '{target_extension}', but soffice was not found")
        return None

    input_path = Path(local_path)
    output_dir = Path(tempfile.mkdtemp(prefix="slidegen-lo-"))
    filter_name = target_extension.lstrip(".")

    try:
        command = [
            "soffice",
            f"-env:UserInstallation=file://{output_dir / 'profile'}",
            "--headless",
            "--convert-to",
            filter_name,
            "--outdir",
            str(output_dir),
            str(input_path),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            logger.warning(
                f"LibreOffice failed to convert '{local_path}' to '{target_extension}': {completed.stderr.strip() or completed.stdout.strip()}"
            )
            return None

        converted_path = output_dir / f"{input_path.stem}{target_extension}"
        if not converted_path.exists():
            logger.warning(f"LibreOffice reported success but did not create '{converted_path}'")
            return None
        return str(converted_path)
    except Exception as exc:
        logger.warning(f"LibreOffice conversion failed for '{local_path}': {exc}")
        return None
