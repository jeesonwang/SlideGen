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
