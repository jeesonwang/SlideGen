"""Test thumbnail generation service"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from PIL import Image

from slidegen.services.presentation.thumbnail import (
    LibreOfficeNotFoundError,
    ThumbnailGenerationError,
    ThumbnailGenerator,
)


class TestThumbnailGenerator:
    """Test ThumbnailGenerator class"""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing"""
        with tempfile.TemporaryDirectory() as templates_dir, tempfile.TemporaryDirectory() as thumbnails_dir:
            templates_path = Path(templates_dir)
            thumbnails_path = Path(thumbnails_dir)
            yield templates_path, thumbnails_path

    @pytest.fixture
    def generator(self, temp_dirs):
        """Create ThumbnailGenerator instance with temporary directories"""
        templates_dir, thumbnails_dir = temp_dirs
        return ThumbnailGenerator(
            templates_dir=templates_dir,
            thumbnails_dir=thumbnails_dir,
            thumbnail_width=300,
        )

    @pytest.fixture
    def mock_template(self, temp_dirs):
        """Create a mock template file"""
        templates_dir, _ = temp_dirs
        template_path = templates_dir / "template_general.pptx"
        template_path.touch()
        return template_path

    def test_init(self, generator, temp_dirs):
        """Test ThumbnailGenerator initialization"""
        templates_dir, thumbnails_dir = temp_dirs
        assert generator.templates_dir == templates_dir
        assert generator.thumbnails_dir == thumbnails_dir
        assert generator.thumbnail_width == 300
        assert thumbnails_dir.exists()

    def test_check_dependencies(self, generator):
        """Test dependency checking"""
        with patch.object(generator, "_find_libreoffice") as mock_find:
            mock_find.return_value = "/path/to/soffice"
            deps = generator.check_dependencies()

            assert "libreoffice" in deps
            assert "pymupdf" in deps
            assert "python-pptx" in deps
            assert "pillow" in deps
            assert deps["libreoffice"] is True
            assert deps["pymupdf"] is True  # Already imported
            assert deps["python-pptx"] is True  # Already imported
            assert deps["pillow"] is True  # Already imported

    def test_check_dependencies_libreoffice_not_found(self, generator):
        """Test dependency checking when LibreOffice is not found"""
        with patch.object(generator, "_find_libreoffice") as mock_find:
            mock_find.side_effect = LibreOfficeNotFoundError("Not found")
            deps = generator.check_dependencies()

            assert deps["libreoffice"] is False

    @patch("slidegen.services.presentation.pdf_exporter.pdf_exporter._find_libreoffice")
    def test_find_libreoffice_in_path(self, mock_find, generator):
        """Test finding LibreOffice in PATH"""
        mock_find.return_value = "/usr/bin/soffice"
        path = generator._find_libreoffice()
        assert path == "/usr/bin/soffice"

    @patch("slidegen.services.presentation.pdf_exporter.pdf_exporter._find_libreoffice")
    def test_find_libreoffice_not_found(self, mock_find, generator):
        """Test error when LibreOffice is not found"""
        from slidegen.services.presentation.pdf_exporter import LibreOfficeNotFoundError as PdfLibreOfficeNotFound
        mock_find.side_effect = PdfLibreOfficeNotFound("Not found")
        with pytest.raises(LibreOfficeNotFoundError) as exc_info:
            generator._find_libreoffice()
        assert "not found" in str(exc_info.value).lower()

    def test_is_thumbnail_valid_missing_thumbnail(self, generator, mock_template):
        """Test thumbnail validation when thumbnail doesn't exist"""
        assert generator.is_thumbnail_valid("general") is False

    def test_is_thumbnail_valid_missing_template(self, generator, temp_dirs):
        """Test thumbnail validation when template doesn't exist"""
        _, thumbnails_dir = temp_dirs
        thumbnail_path = thumbnails_dir / "general.png"
        thumbnail_path.touch()

        assert generator.is_thumbnail_valid("general") is False

    def test_is_thumbnail_valid_outdated(self, generator, mock_template, temp_dirs):
        """Test thumbnail validation when thumbnail is older than template"""
        _, thumbnails_dir = temp_dirs
        thumbnail_path = thumbnails_dir / "general.png"
        thumbnail_path.touch()

        # Make template newer
        import time

        time.sleep(0.01)
        mock_template.touch()

        assert generator.is_thumbnail_valid("general") is False

    def test_is_thumbnail_valid_up_to_date(self, generator, mock_template, temp_dirs):
        """Test thumbnail validation when thumbnail is up to date"""
        _, thumbnails_dir = temp_dirs
        thumbnail_path = thumbnails_dir / "general.png"

        # Make thumbnail newer
        import time

        time.sleep(0.01)
        thumbnail_path.touch()

        assert generator.is_thumbnail_valid("general") is True

    def test_get_thumbnail_path_exists(self, generator, temp_dirs):
        """Test getting thumbnail path when it exists"""
        _, thumbnails_dir = temp_dirs
        thumbnail_path = thumbnails_dir / "general.png"
        thumbnail_path.touch()

        result = generator.get_thumbnail_path("general")
        assert result == thumbnail_path

    def test_get_thumbnail_path_not_exists(self, generator):
        """Test getting thumbnail path when it doesn't exist"""
        result = generator.get_thumbnail_path("general")
        assert result is None

    def test_generate_thumbnail_template_not_found(self, generator):
        """Test error when template doesn't exist"""
        with pytest.raises(FileNotFoundError) as exc_info:
            generator.generate_thumbnail("nonexistent")
        assert "not found" in str(exc_info.value).lower()

    @patch("slidegen.services.presentation.thumbnail.fitz")
    @patch("subprocess.run")
    def test_generate_thumbnail_success(self, mock_subprocess, mock_fitz, generator, mock_template, temp_dirs):
        """Test successful thumbnail generation"""
        _, thumbnails_dir = temp_dirs

        # Create a side effect function to create the PDF file
        def create_pdf(*args, **_kwargs):
            # Extract the output directory from the command
            cmd = args[0]
            outdir_idx = cmd.index("--outdir")
            output_dir = Path(cmd[outdir_idx + 1])
            pdf_path = output_dir / "template_general.pdf"
            pdf_path.touch()
            return Mock(returncode=0, stderr="")

        # Mock subprocess (LibreOffice conversion)
        mock_subprocess.side_effect = create_pdf

        # Mock PyMuPDF with side effect to create PNG file
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.rect.width = 1920
        mock_pixmap = MagicMock()

        def save_png(path):
            # Create a real PNG file
            img = Image.new("RGB", (300, 225), "white")
            img.save(path)

        mock_pixmap.save.side_effect = save_png
        mock_page.get_pixmap.return_value = mock_pixmap
        mock_doc.__len__.return_value = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz.open.return_value = mock_doc

        # Generate thumbnail
        result = generator.generate_thumbnail("general")

        assert result == thumbnails_dir / "general.png"
        assert result.exists()
        mock_subprocess.assert_called_once()
        mock_fitz.open.assert_called_once()
        mock_pixmap.save.assert_called_once()

    @patch("subprocess.run")
    def test_convert_pptx_to_pdf_failure(self, mock_subprocess, generator, mock_template):
        """Test PDF conversion failure"""
        mock_subprocess.return_value = Mock(returncode=1, stderr="Conversion error")

        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ThumbnailGenerationError) as exc_info:
                generator._convert_pptx_to_pdf(mock_template, Path(temp_dir))
            assert "conversion failed" in str(exc_info.value).lower()

    @patch("subprocess.run")
    def test_convert_pptx_to_pdf_timeout(self, mock_subprocess, generator, mock_template):
        """Test PDF conversion timeout"""
        import subprocess

        mock_subprocess.side_effect = subprocess.TimeoutExpired("cmd", 60)

        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ThumbnailGenerationError) as exc_info:
                generator._convert_pptx_to_pdf(mock_template, Path(temp_dir))
            assert "timed out" in str(exc_info.value).lower()

    @patch("slidegen.services.presentation.pdf_exporter.pdf_exporter._find_libreoffice")
    def test_convert_pptx_to_pdf_libreoffice_not_found(self, mock_find, generator, mock_template):
        """Test LibreOffice lookup failures stay mapped to thumbnail errors."""
        from slidegen.services.presentation.pdf_exporter import LibreOfficeNotFoundError as PdfLibreOfficeNotFound

        mock_find.side_effect = PdfLibreOfficeNotFound("Not found")

        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(LibreOfficeNotFoundError) as exc_info:
                generator._convert_pptx_to_pdf(mock_template, Path(temp_dir))
            assert "not found" in str(exc_info.value).lower()

    def test_render_pdf_page_no_pages(self, generator):
        """Test rendering when PDF has no pages"""
        pdf_path = Path("/tmp/test.pdf")
        output_path = Path("/tmp/test_output.png")

        with patch("slidegen.services.presentation.thumbnail.fitz") as mock_fitz:
            # Mock fitz.FileDataError to be a real exception
            mock_fitz.FileDataError = Exception

            mock_doc = MagicMock()
            mock_doc.__len__.return_value = 0
            mock_fitz.open.return_value = mock_doc

            with pytest.raises(ThumbnailGenerationError) as exc_info:
                generator._render_pdf_page(pdf_path, output_path, 300, 0)
            assert "no pages" in str(exc_info.value).lower()

    def test_render_pdf_page_invalid_page_num(self, generator):
        """Test rendering with invalid page number"""
        pdf_path = Path("/tmp/test.pdf")
        output_path = Path("/tmp/test_output.png")

        with patch("slidegen.services.presentation.thumbnail.fitz") as mock_fitz:
            # Mock fitz.FileDataError to be a real exception
            mock_fitz.FileDataError = Exception

            mock_doc = MagicMock()
            mock_doc.__len__.return_value = 1
            mock_fitz.open.return_value = mock_doc

            with pytest.raises(ThumbnailGenerationError) as exc_info:
                generator._render_pdf_page(pdf_path, output_path, 300, 5)
            assert "does not exist" in str(exc_info.value).lower()

    @patch("slidegen.services.presentation.thumbnail.Presentation")
    def test_get_placeholder_regions(self, mock_presentation_class, generator, mock_template):
        """Test extracting placeholder regions"""
        # Create mock presentation with shapes
        mock_prs = MagicMock()
        mock_slide = MagicMock()
        mock_shape = MagicMock(spec=["text_frame", "left", "top", "width", "height"])

        # Configure shape with text - need to ensure all hasattr checks pass
        mock_text_frame = MagicMock()
        mock_text = MagicMock()
        mock_text.strip.return_value = "Sample text"
        mock_text_frame.text = mock_text
        mock_shape.text_frame = mock_text_frame
        mock_shape.left = 914400  # 1 inch in EMU
        mock_shape.top = 914400
        mock_shape.width = 914400
        mock_shape.height = 914400

        mock_slide.shapes = [mock_shape]
        mock_prs.slides = [mock_slide]
        mock_prs.slide_width = 9144000  # 10 inches
        mock_prs.slide_height = 6858000  # 7.5 inches

        mock_presentation_class.return_value = mock_prs

        regions, dimensions = generator._get_placeholder_regions(mock_template)

        assert 0 in regions
        assert len(regions[0]) == 1
        assert regions[0][0]["left"] == 1.0
        assert regions[0][0]["top"] == 1.0
        assert regions[0][0]["width"] == 1.0
        assert regions[0][0]["height"] == 1.0
        assert dimensions == (10.0, 7.5)

    def test_apply_placeholder_outlines(self, generator):
        """Test applying placeholder outlines to image"""
        # Create a test image
        img = Image.new("RGB", (800, 600), "white")

        regions = [
            {"left": 1.0, "top": 1.0, "width": 2.0, "height": 1.5},
            {"left": 5.0, "top": 3.0, "width": 3.0, "height": 2.0},
        ]
        slide_dimensions = (10.0, 7.5)

        result = generator._apply_placeholder_outlines(img, regions, slide_dimensions)

        assert result.mode == "RGB"
        assert result.size == (800, 600)

    @patch("slidegen.services.presentation.thumbnail.fitz")
    @patch("subprocess.run")
    def test_generate_thumbnail_with_cache(
        self, mock_subprocess, mock_fitz, generator, mock_template, temp_dirs
    ):
        """Test that cached thumbnail is used when valid"""
        _, thumbnails_dir = temp_dirs
        thumbnail_path = thumbnails_dir / "general.png"

        # Create a valid cached thumbnail
        import time

        time.sleep(0.01)
        thumbnail_path.touch()

        # Generate thumbnail (should use cache)
        result = generator.generate_thumbnail("general", force=False)

        assert result == thumbnail_path
        # Subprocess should not be called since we're using cache
        mock_subprocess.assert_not_called()
        mock_fitz.open.assert_not_called()

    @patch("slidegen.services.presentation.thumbnail.fitz")
    @patch("subprocess.run")
    def test_generate_thumbnail_force_regenerate(
        self, mock_subprocess, mock_fitz, generator, mock_template, temp_dirs
    ):
        """Test forcing thumbnail regeneration"""
        _, thumbnails_dir = temp_dirs
        thumbnail_path = thumbnails_dir / "general.png"

        # Create a valid cached thumbnail
        import time

        time.sleep(0.01)
        thumbnail_path.touch()

        # Create a side effect function to create the PDF file
        def create_pdf(*args, **_kwargs):
            cmd = args[0]
            outdir_idx = cmd.index("--outdir")
            output_dir = Path(cmd[outdir_idx + 1])
            pdf_path = output_dir / "template_general.pdf"
            pdf_path.touch()
            return Mock(returncode=0, stderr="")

        # Mock subprocess and PyMuPDF
        mock_subprocess.side_effect = create_pdf
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.rect.width = 1920
        mock_pixmap = MagicMock()

        def save_png(path):
            img = Image.new("RGB", (300, 225), "white")
            img.save(path)

        mock_pixmap.save.side_effect = save_png
        mock_page.get_pixmap.return_value = mock_pixmap
        mock_doc.__len__.return_value = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz.open.return_value = mock_doc

        # Generate thumbnail with force=True
        result = generator.generate_thumbnail("general", force=True)

        assert result == thumbnail_path
        # Should regenerate even with valid cache
        mock_subprocess.assert_called_once()
        mock_fitz.open.assert_called_once()

    @patch("slidegen.services.presentation.thumbnail.fitz")
    @patch("slidegen.services.presentation.thumbnail.Presentation")
    @patch("subprocess.run")
    def test_generate_thumbnail_with_placeholders(
        self, mock_subprocess, mock_presentation_class, mock_fitz, generator, mock_template, temp_dirs
    ):
        """Test generating thumbnail with placeholder outlines"""
        _, thumbnails_dir = temp_dirs

        # Create a side effect function to create the PDF file
        def create_pdf(*args, **_kwargs):
            cmd = args[0]
            outdir_idx = cmd.index("--outdir")
            output_dir = Path(cmd[outdir_idx + 1])
            pdf_path = output_dir / "template_general.pdf"
            pdf_path.touch()
            return Mock(returncode=0, stderr="")

        # Mock subprocess
        mock_subprocess.side_effect = create_pdf

        # Mock Presentation
        mock_prs = MagicMock()
        mock_slide = MagicMock()
        mock_shape = MagicMock(spec=["text_frame", "left", "top", "width", "height"])
        mock_text_frame = MagicMock()
        mock_text = MagicMock()
        mock_text.strip.return_value = "Text"
        mock_text_frame.text = mock_text
        mock_shape.text_frame = mock_text_frame
        mock_shape.left = 914400
        mock_shape.top = 914400
        mock_shape.width = 914400
        mock_shape.height = 914400
        mock_slide.shapes = [mock_shape]
        mock_prs.slides = [mock_slide]
        mock_prs.slide_width = 9144000
        mock_prs.slide_height = 6858000
        mock_presentation_class.return_value = mock_prs

        # Mock PyMuPDF
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.rect.width = 1920
        mock_pixmap = MagicMock()

        def save_png(path):
            img = Image.new("RGB", (300, 225), "white")
            img.save(path)

        mock_pixmap.save.side_effect = save_png
        mock_page.get_pixmap.return_value = mock_pixmap
        mock_doc.__len__.return_value = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz.open.return_value = mock_doc

        # Generate with placeholders
        result = generator.generate_thumbnail("general", outline_placeholders=True)

        assert result == thumbnails_dir / "general.png"
        assert result.exists()
        mock_presentation_class.assert_called()

    @patch("slidegen.services.presentation.thumbnail.fitz")
    @patch("subprocess.run")
    def test_generate_grid_thumbnail_success(
        self, mock_subprocess, mock_fitz, generator, mock_template, temp_dirs
    ):
        """Test successful grid thumbnail generation"""
        _, thumbnails_dir = temp_dirs

        # Create a side effect function to create the PDF file
        def create_pdf(*args, **_kwargs):
            cmd = args[0]
            outdir_idx = cmd.index("--outdir")
            output_dir = Path(cmd[outdir_idx + 1])
            pdf_path = output_dir / "template_general.pdf"
            pdf_path.touch()
            return Mock(returncode=0, stderr="")

        # Mock subprocess
        mock_subprocess.side_effect = create_pdf

        # Mock PyMuPDF for 3 pages
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.rect.width = 1920
        mock_pixmap = MagicMock()

        # Counter for PNG saves
        save_counter = {"count": 0}

        def save_png(path):
            # Create real PNG files for each page
            img = Image.new("RGB", (300, 225), "white")
            img.save(path)
            save_counter["count"] += 1

        mock_pixmap.save.side_effect = save_png
        mock_page.get_pixmap.return_value = mock_pixmap
        mock_doc.__len__.return_value = 3
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz.open.return_value = mock_doc

        # Generate grid
        results = generator.generate_grid_thumbnail("general", cols=2)

        assert len(results) == 1
        assert results[0] == thumbnails_dir / "general_grid.png"
        assert results[0].exists()

    def test_generate_grid_thumbnail_template_not_found(self, generator):
        """Test grid generation when template doesn't exist"""
        with pytest.raises(FileNotFoundError) as exc_info:
            generator.generate_grid_thumbnail("nonexistent")
        assert "not found" in str(exc_info.value).lower()

    @patch("slidegen.services.presentation.thumbnail.fitz")
    @patch("subprocess.run")
    def test_generate_grid_thumbnail_max_cols(
        self, mock_subprocess, mock_fitz, generator, mock_template, temp_dirs
    ):
        """Test grid generation respects max columns"""
        _, thumbnails_dir = temp_dirs

        # Create a side effect function to create the PDF file
        def create_pdf(*args, **_kwargs):
            cmd = args[0]
            outdir_idx = cmd.index("--outdir")
            output_dir = Path(cmd[outdir_idx + 1])
            pdf_path = output_dir / "template_general.pdf"
            pdf_path.touch()
            return Mock(returncode=0, stderr="")

        mock_subprocess.side_effect = create_pdf
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.rect.width = 1920
        mock_pixmap = MagicMock()

        def save_png(path):
            img = Image.new("RGB", (300, 225), "white")
            img.save(path)

        mock_pixmap.save.side_effect = save_png
        mock_page.get_pixmap.return_value = mock_pixmap
        mock_doc.__len__.return_value = 2
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz.open.return_value = mock_doc

        # Try to set cols > MAX_COLS (6)
        results = generator.generate_grid_thumbnail("general", cols=10)

        assert len(results) == 1
        # Should use MAX_COLS=6 instead of 10

    @patch("slidegen.services.presentation.thumbnail.fitz")
    @patch("subprocess.run")
    def test_generate_grid_thumbnail_cached(
        self, mock_subprocess, mock_fitz, generator, mock_template, temp_dirs
    ):
        """Test grid thumbnail uses cache when valid"""
        _, thumbnails_dir = temp_dirs
        grid_path = thumbnails_dir / "general_grid.png"

        # Create valid cached grid
        import time

        time.sleep(0.01)
        grid_path.touch()

        results = generator.generate_grid_thumbnail("general", force=False)

        assert len(results) == 1
        assert grid_path in results
        # Should not call subprocess or fitz
        mock_subprocess.assert_not_called()
        mock_fitz.open.assert_not_called()

    def test_create_single_grid(self, generator):
        """Test creating a single grid from images"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test images
            image_paths = []
            for i in range(4):
                img_path = temp_path / f"slide_{i}.png"
                img = Image.new("RGB", (800, 600), "white")
                img.save(img_path)
                image_paths.append(img_path)

            # Create grid
            from PIL import ImageFont

            try:
                font = ImageFont.load_default(size=36)
            except Exception:
                font = ImageFont.load_default()

            grid = generator._create_single_grid(
                image_paths, cols=2, width=300, font=font, font_size=36, label_padding=14, start_slide_num=0
            )

            assert grid.mode == "RGB"
            assert grid.size[0] > 0
            assert grid.size[1] > 0


class TestThumbnailGeneratorEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing"""
        with tempfile.TemporaryDirectory() as templates_dir, tempfile.TemporaryDirectory() as thumbnails_dir:
            yield Path(templates_dir), Path(thumbnails_dir)

    @pytest.fixture
    def generator(self, temp_dirs):
        """Create ThumbnailGenerator instance"""
        templates_dir, thumbnails_dir = temp_dirs
        return ThumbnailGenerator(
            templates_dir=templates_dir,
            thumbnails_dir=thumbnails_dir,
        )

    def test_thumbnail_with_suffix(self, generator, temp_dirs):
        """Test thumbnail generation with custom suffix"""
        templates_dir, thumbnails_dir = temp_dirs
        template_path = templates_dir / "template_general.pptx"
        template_path.touch()

        # Check with suffix
        assert generator.is_thumbnail_valid("general", "_debug") is False

        # Create thumbnail with suffix
        thumb_path = thumbnails_dir / "general_debug.png"

        import time

        time.sleep(0.01)
        thumb_path.touch()

        assert generator.is_thumbnail_valid("general", "_debug") is True

    def test_get_placeholder_regions_no_text(self, generator, temp_dirs):
        """Test placeholder extraction when shapes have no text"""
        templates_dir, _ = temp_dirs
        template_path = templates_dir / "template_general.pptx"
        template_path.touch()

        with patch("slidegen.services.presentation.thumbnail.Presentation") as mock_pres_class:
            mock_prs = MagicMock()
            mock_slide = MagicMock()
            mock_shape = MagicMock()
            mock_shape.text_frame.text.strip.return_value = ""  # Empty text
            mock_slide.shapes = [mock_shape]
            mock_prs.slides = [mock_slide]
            mock_prs.slide_width = 9144000
            mock_prs.slide_height = 6858000
            mock_pres_class.return_value = mock_prs

            regions, dimensions = generator._get_placeholder_regions(template_path)

            assert len(regions) == 0  # No regions since text is empty
            assert dimensions == (10.0, 7.5)

    def test_get_placeholder_regions_error(self, generator, temp_dirs):
        """Test placeholder extraction handles errors gracefully"""
        templates_dir, _ = temp_dirs
        template_path = templates_dir / "template_general.pptx"
        template_path.touch()

        with patch("slidegen.services.presentation.thumbnail.Presentation") as mock_pres_class:
            mock_pres_class.side_effect = Exception("Failed to open presentation")

            regions, dimensions = generator._get_placeholder_regions(template_path)

            # Should return empty dict and default dimensions
            assert regions == {}
            assert dimensions == (10.0, 7.5)

    def test_apply_placeholder_outlines_rgb_image(self, generator):
        """Test applying outlines to RGB image (should convert to RGBA)"""
        img = Image.new("RGB", (800, 600), "white")
        regions = [{"left": 1.0, "top": 1.0, "width": 2.0, "height": 1.5}]
        slide_dimensions = (10.0, 7.5)

        result = generator._apply_placeholder_outlines(img, regions, slide_dimensions)

        assert result.mode == "RGB"  # Should be converted back to RGB

    def test_render_pdf_first_page_deprecated(self, generator):
        """Test deprecated _render_pdf_first_page method"""
        with tempfile.NamedTemporaryFile(suffix=".pdf") as pdf_file, tempfile.NamedTemporaryFile(
            suffix=".png"
        ) as output_file:
            pdf_path = Path(pdf_file.name)
            output_path = Path(output_file.name)

            with patch.object(generator, "_render_pdf_page") as mock_render:
                generator._render_pdf_first_page(pdf_path, output_path, 300)
                mock_render.assert_called_once_with(pdf_path, output_path, 300, page_num=0)
