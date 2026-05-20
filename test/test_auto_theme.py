import os
import uuid
from inspect import signature
from types import SimpleNamespace
from typing import get_args

os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PASSWORD", "test")
os.environ.setdefault("MYSQL_HOST", "localhost")
os.environ.setdefault("MYSQL_USER", "test")
os.environ.setdefault("MYSQL_PASSWORD", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("FIRST_SUPERUSER", "admin@example.com")
os.environ.setdefault("FIRST_SUPERUSER_PASSWORD", "12345678")

from slidegen.schemas.theme import ThemePresets
from slidegen.services.presentation.generator import PresentationGenerator


class RecordingThemeSelector:
    def __init__(self) -> None:
        self.messages = []
        self.used_async_response = False

    def response(self, messages):
        raise AssertionError("Auto Theme should use aresponse instead of response")

    async def aresponse(self, messages):
        self.messages = messages
        self.used_async_response = True
        return SimpleNamespace(content='{"theme_preset": "tech_innovation"}')


async def test_auto_theme_uses_llm_to_select_theme() -> None:
    generator = PresentationGenerator()
    selector = RecordingThemeSelector()

    theme = await generator._resolve_theme(
        theme_preset="auto",
        auto_content="Quarterly roadmap for a logistics platform.",
        auto_theme_llm=selector,
    )

    assert theme == ThemePresets.TECH_INNOVATION
    assert selector.used_async_response
    assert selector.messages
    assert "tech_innovation" in selector.messages[0].content


def test_auto_theme_text_fallback_rejects_ambiguous_mentions() -> None:
    generator = PresentationGenerator()

    selected = generator._extract_theme_preset_id(
        "I considered golden_hour, but the final answer is tech_innovation."
    )

    assert selected is None


def test_markdown_generation_user_id_annotation_matches_uuid_contract() -> None:
    generator = PresentationGenerator()

    user_id_annotation = signature(generator.generate_from_markdown).parameters["user_id"].annotation
    stream_user_id_annotation = signature(generator.generate_from_markdown_stream).parameters["user_id"].annotation

    assert uuid.UUID in get_args(user_id_annotation)
    assert uuid.UUID in get_args(stream_user_id_annotation)
