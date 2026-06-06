from types import SimpleNamespace

import pytest

from slidegen.services.presentation import image_generator as image_generator_module
from slidegen.services.presentation.image_generator import ImageGenerator


@pytest.mark.anyio
async def test_generate_image_openai_uses_gpt_image_model(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    class FakeImages:
        async def generate(self, **kwargs: object) -> SimpleNamespace:
            calls.append(kwargs)
            return SimpleNamespace(data=[SimpleNamespace(url="https://example.com/generated.png")])

    class FakeClient:
        def __init__(self) -> None:
            self.images = FakeImages()

    async def fake_download_file(url: str, output_directory: str) -> str:
        assert url == "https://example.com/generated.png"
        assert output_directory == "/tmp/output"
        return "/tmp/output/generated.png"

    monkeypatch.setattr(image_generator_module, "AsyncOpenAI", FakeClient)
    monkeypatch.setattr(image_generator_module, "download_file", fake_download_file)
    monkeypatch.setattr(image_generator_module.settings, "OPENAI_IMAGE_MODEL", "gpt-image-1.5")

    generator = ImageGenerator("/tmp/output")

    result = await generator.generate_image_openai("draw a fox", "/tmp/output")

    assert result == "/tmp/output/generated.png"
    assert calls == [
        {
            "model": "gpt-image-1.5",
            "prompt": "draw a fox",
            "n": 1,
            "quality": "standard",
            "size": "1024x1024",
        }
    ]
