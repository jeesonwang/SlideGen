import pytest

from slidegen.core.config import Settings, parse_cors


def test_parse_cors_json_array_string_returns_list() -> None:
    value = '["http://localhost:5173","http://127.0.0.1:5173"]'

    assert parse_cors(value) == ["http://localhost:5173", "http://127.0.0.1:5173"]


def test_parse_cors_comma_separated_string_returns_list() -> None:
    value = "http://localhost:5173,http://127.0.0.1:5173"

    assert parse_cors(value) == ["http://localhost:5173", "http://127.0.0.1:5173"]


def test_settings_cors_origins_always_validates_to_list() -> None:
    settings = Settings(BACKEND_CORS_ORIGINS='["http://localhost:5173","http://127.0.0.1:5173"]')

    assert settings.BACKEND_CORS_ORIGINS == ["http://localhost:5173", "http://127.0.0.1:5173"]
    assert isinstance(settings.BACKEND_CORS_ORIGINS, list)


@pytest.mark.parametrize(
    ("env_value", "expected"),
    [
        ("*", ["*"]),
        ("http://localhost:5173,http://127.0.0.1:5173", ["http://localhost:5173", "http://127.0.0.1:5173"]),
        ('["http://localhost:5173","http://127.0.0.1:5173"]', ["http://localhost:5173", "http://127.0.0.1:5173"]),
    ],
)
def test_settings_cors_origins_accepts_env_formats(monkeypatch: pytest.MonkeyPatch, env_value: str, expected: list[str]) -> None:
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", env_value)

    settings = Settings()

    assert settings.BACKEND_CORS_ORIGINS == expected
    assert isinstance(settings.BACKEND_CORS_ORIGINS, list)


def test_settings_reads_image_and_temp_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEMP_DIRECTORY", "/tmp/slidegen")
    monkeypatch.setenv("IMAGE_PROVIDER", "pexels")
    monkeypatch.setenv("PEXELS_API_KEY", "pexels-key")
    monkeypatch.setenv("PIXABAY_API_KEY", "pixabay-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")

    settings = Settings()

    assert settings.TEMP_DIRECTORY == "/tmp/slidegen"
    assert settings.IMAGE_PROVIDER == "pexels"
    assert settings.PEXELS_API_KEY == "pexels-key"
    assert settings.PIXABAY_API_KEY == "pixabay-key"
    assert settings.GOOGLE_API_KEY == "google-key"
    assert settings.OPENAI_API_KEY == "openai-key"


def test_settings_accepts_gpt_image_provider_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IMAGE_PROVIDER", "gpt-image")
    monkeypatch.setenv("OPENAI_IMAGE_MODEL", "gpt-image-1.5")

    settings = Settings()

    assert settings.IMAGE_PROVIDER == "gpt-image"
    assert settings.OPENAI_IMAGE_MODEL == "gpt-image-1.5"
