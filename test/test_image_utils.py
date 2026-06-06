import pytest

from slidegen.core.config import settings
from slidegen.utils.image import ImageProvider, get_image_provider_api_key, get_selected_image_provider


def test_get_selected_image_provider_reads_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "IMAGE_PROVIDER", "pixabay")

    assert get_selected_image_provider() == ImageProvider.PIXABAY


def test_get_selected_image_provider_uses_generic_gpt_provider_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "IMAGE_PROVIDER", "gpt-image")

    assert get_selected_image_provider() == ImageProvider.GPT_IMAGE


@pytest.mark.parametrize(
    ("provider", "setting_name", "api_key"),
    [
        ("pexels", "PEXELS_API_KEY", "pexels-key"),
        ("pixabay", "PIXABAY_API_KEY", "pixabay-key"),
        ("gemini_flash", "GOOGLE_API_KEY", "google-key"),
        ("gpt-image", "OPENAI_API_KEY", "openai-key"),
    ],
)
def test_get_image_provider_api_key_reads_settings(
    monkeypatch: pytest.MonkeyPatch,
    provider: str,
    setting_name: str,
    api_key: str,
) -> None:
    monkeypatch.setattr(settings, "IMAGE_PROVIDER", provider)
    monkeypatch.setattr(settings, setting_name, api_key)

    assert get_image_provider_api_key() == api_key
