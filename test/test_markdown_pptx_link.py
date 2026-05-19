import os
from pathlib import Path

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

from slidegen.schemas.gen_request import MarkdownToPPTRequest
from slidegen.schemas.theme import ThemePresets


def test_theme_presets_endpoint_returns_ids_and_display_names() -> None:
    router_source = Path("slidegen/api/routers/slidegen.py").read_text()

    assert '@router.get("/theme-presets"' in router_source
    assert "ThemePresets.list_presets()" in router_source
    assert "preset = ThemePresets.get_preset(preset_id)" in router_source
    assert '"name": preset.name' in router_source


def test_markdown_pptx_request_accepts_theme_preset() -> None:
    request = MarkdownToPPTRequest(
        markdown_content="# Title",
        template="general",
        export_as="pptx",
        theme_preset="ocean_depths",
    )

    assert request.theme_preset == "ocean_depths"


def test_theme_presets_keep_id_and_name_shape() -> None:
    assert [
        {"id": preset_id, "name": ThemePresets.get_preset(preset_id).name}
        for preset_id in ThemePresets.list_presets()
    ][0] == {"id": "ocean_depths", "name": "Ocean Depths"}


def test_markdown_routes_and_generator_forward_theme_preset() -> None:
    router_source = Path("slidegen/api/routers/slidegen.py").read_text()
    generator_source = Path("slidegen/services/presentation/generator.py").read_text()

    assert "theme_preset=request.theme_preset" in router_source
    assert "theme_preset: str | None = None" in generator_source
    assert "self._resolve_theme(theme, theme_preset)" in generator_source
