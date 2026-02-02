"""Apply theme colors to PowerPoint presentations."""

import re
import shutil
import tempfile
from pathlib import Path

from slidegen.schemas.theme import PresentationTheme, ThemeColorMapping
from slidegen.services.presentation.pack import pack_document
from slidegen.services.presentation.unpack import unpack_document
from slidegen.services.presentation.validate import validate_document


class ThemeApplier:
    """Apply theme colors to PowerPoint presentations."""

    @staticmethod
    def apply_theme_to_pptx(
        input_pptx: str | Path,
        output_pptx: str | Path,
        theme: PresentationTheme,
        skills_path: str | Path | None = None,
    ) -> None:
        """
        Apply a theme to a PowerPoint presentation.

        Args:
            input_pptx: Path to input PPTX file
            output_pptx: Path to output PPTX file
            theme: PresentationTheme to apply
            skills_path: (Deprecated) Path to pptx skills directory. This argument is now ignored.

        Raises:
            FileNotFoundError: If input file not found
            Exception: If unpacking, validation, or packing fails
        """
        input_pptx = Path(input_pptx)
        output_pptx = Path(output_pptx)

        if not input_pptx.exists():
            raise FileNotFoundError(f"Input file not found: {input_pptx}")

        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            unpacked_dir = tmpdir_path / "unpacked"

            # Unpack PPTX
            unpack_document(input_pptx, unpacked_dir)

            # Apply theme to all theme files
            theme_dir = unpacked_dir / "ppt" / "theme"
            if theme_dir.exists():
                for theme_file in sorted(theme_dir.glob("theme*.xml")):
                    ThemeApplier._apply_theme_to_file(theme_file, theme.colors)

            # Validate
            if not validate_document(unpacked_dir, input_pptx):
                # We can choose to raise an error or just log a warning.
                # The original code would raise CalledProcessError if the script failed (exit code 1).
                # So raising an exception here preserves behavior.
                raise Exception("Validation failed after applying theme.")

            # Pack PPTX
            if not pack_document(unpacked_dir, output_pptx):
                raise Exception("Packing failed.")

    @staticmethod
    def _apply_theme_to_file(theme_file: Path, colors: ThemeColorMapping) -> None:
        """
        Apply theme colors to a single theme XML file.

        Args:
            theme_file: Path to theme XML file
            colors: ThemeColorMapping with color values
        """
        with open(theme_file, encoding="utf-8") as f:
            content = f.read()

        # Get only non-None colors
        color_dict = colors.model_dump_colors()

        # Apply each color
        for color_name, color_value in color_dict.items():
            # Pattern matches: <a:colorname> ... <a:srgbClr val="..."/> ... </a:colorname>
            pattern = f'(<a:{color_name}>.*?<a:srgbClr val=")[^"]*(".*?</a:{color_name}>)'
            replacement = f"\\g<1>{color_value}\\g<2>"
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        with open(theme_file, "w", encoding="utf-8") as f:
            f.write(content)

    @staticmethod
    def apply_theme_inplace(pptx_path: str | Path, theme: PresentationTheme) -> None:
        """
        Apply a theme to a PowerPoint presentation in-place.

        Args:
            pptx_path: Path to PPTX file (will be modified)
            theme: PresentationTheme to apply
        """
        pptx_path = Path(pptx_path)

        # Create backup
        backup_path = pptx_path.with_suffix(".pptx.bak")
        shutil.copy2(pptx_path, backup_path)

        try:
            # Apply theme to temporary file
            with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            ThemeApplier.apply_theme_to_pptx(pptx_path, tmp_path, theme)

            # Replace original file
            shutil.move(tmp_path, pptx_path)

            # Remove backup on success
            backup_path.unlink()

        except Exception as e:
            # Restore backup on failure
            if backup_path.exists():
                shutil.move(backup_path, pptx_path)
            raise e
