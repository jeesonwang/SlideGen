import shutil
import tempfile
import unittest
from pathlib import Path

from slidegen.schemas.theme import ThemePresets
from slidegen.services.theme_applier import ThemeApplier


class TestThemeApplier(unittest.TestCase):
    def setUp(self):
        # Setup paths
        self.test_dir = Path(__file__).parent
        self.data_dir = self.test_dir / "data"
        self.input_pptx = self.data_dir / "template_0.pptx"

        # Create a temporary output file
        self.temp_dir = tempfile.mkdtemp()
        # Output to current directory for manual inspection
        self.output_pptx = self.test_dir / "output_test_theme.pptx"

    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir)

    def test_apply_theme_to_pptx(self):
        """Test applying a theme to a PPTX file."""
        # Ensure input file exists
        self.assertTrue(self.input_pptx.exists(), f"Input file not found: {self.input_pptx}")

        # Choose a theme
        theme = ThemePresets.OCEAN_DEPTHS

        # Apply theme
        ThemeApplier.apply_theme_to_pptx(self.input_pptx, self.output_pptx, theme)

        # Verify output file exists
        self.assertTrue(self.output_pptx.exists(), "Output file was not created")

        # Verify output file size is greater than 0
        self.assertGreater(self.output_pptx.stat().st_size, 0, "Output file is empty")

    def test_apply_theme_inplace(self):
        """Test applying a theme to a PPTX file in-place."""
        # Create a copy of the input file for in-place testing
        temp_input_pptx = Path(self.temp_dir) / "temp_input.pptx"
        shutil.copy2(self.input_pptx, temp_input_pptx)

        # Choose a theme
        theme = ThemePresets.SUNSET_BOULEVARD

        # Apply theme in-place
        ThemeApplier.apply_theme_inplace(temp_input_pptx, theme)

        # Verify file still exists
        self.assertTrue(temp_input_pptx.exists(), "File disappeared after in-place update")

        # Verify file size is greater than 0
        self.assertGreater(temp_input_pptx.stat().st_size, 0, "File became empty after in-place update")


if __name__ == "__main__":
    unittest.main()
