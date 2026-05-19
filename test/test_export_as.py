"""Tests for export_as format support in PresentationGenerator."""

from unittest.mock import patch

import pytest

from slidegen.services.presentation.generator import PresentationGenerator


async def test_generate_from_markdown_accepts_pdf() -> None:
    """Verify export_as='pdf' no longer raises ValueError.
    Template lookup will fail with FileNotFoundError, not ValueError."""
    generator = PresentationGenerator(templates_dir=".")
    with pytest.raises(FileNotFoundError, match="template"):
        await generator.generate_from_markdown(
            markdown_content="# Title",
            template_name="does-not-matter",
            output_path="out.pdf",
            export_as="pdf",
        )


async def test_generate_from_markdown_stream_accepts_pdf() -> None:
    """Verify stream no longer yields export_as error for PDF.
    Template lookup will yield a different error."""
    generator = PresentationGenerator(templates_dir=".")
    events = [
        event
        async for event in generator.generate_from_markdown_stream(
            markdown_content="# Title",
            template_name="does-not-matter",
            output_path="out.pdf",
            export_as="pdf",
        )
    ]
    assert len(events) == 1
    assert events[0].event == "workflow_error"
    # Error should be about template, not about export_as
    assert "export_as" not in events[0].error
    assert "template" in events[0].error.lower() or "Template" in events[0].error
