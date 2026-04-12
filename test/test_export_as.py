import pytest

from slidegen.services.presentation.generator import PresentationGenerator


async def test_generate_from_markdown_rejects_pdf() -> None:
    generator = PresentationGenerator(templates_dir=".")
    with pytest.raises(ValueError, match="export_as"):
        await generator.generate_from_markdown(
            markdown_content="# Title",
            template_name="does-not-matter",
            output_path="out.pptx",
            export_as="pdf",
        )


async def test_generate_from_markdown_stream_rejects_pdf() -> None:
    generator = PresentationGenerator(templates_dir=".")
    events = [
        event
        async for event in generator.generate_from_markdown_stream(
            markdown_content="# Title",
            template_name="does-not-matter",
            output_path="out.pptx",
            export_as="pdf",
        )
    ]
    assert len(events) == 1
    assert events[0].event == "workflow_error"
    assert "export_as" in events[0].error
