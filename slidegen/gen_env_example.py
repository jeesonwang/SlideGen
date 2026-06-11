from pathlib import Path
from typing import Any

from pydantic_core import PydanticUndefined
from pydantic_settings import BaseSettings
from rich import print

from slidegen.core.config import PROJECT_ROOT, Settings


def _format_value(value: Any) -> str:
    """Convert a default value to its .env representation.

    Paths (or path-like strings) that live under ``PROJECT_ROOT`` are emitted
    as repo-relative paths so the example file is portable across machines.
    """
    if value is None or value is PydanticUndefined:
        return ""

    if isinstance(value, Path):
        try:
            return value.relative_to(PROJECT_ROOT).as_posix()
        except ValueError:
            return value.as_posix()

    if isinstance(value, str):
        project_root_str = PROJECT_ROOT.as_posix()
        if value == project_root_str or value.startswith(project_root_str + "/"):
            return Path(value).relative_to(PROJECT_ROOT).as_posix()
        return value

    return str(value)


def generate_env_example(
    settings_class: type[BaseSettings], output_file: str | Path = PROJECT_ROOT / ".env.example"
) -> None:
    fields: dict[str, Any] = settings_class.model_fields
    lines = ["PYTHONPATH=."]

    for name, field in fields.items():
        env_name = field.alias or name.upper()
        if field.is_required():
            lines.append(f"{env_name}=")
        else:
            lines.append(f"{env_name}={_format_value(field.default)}")

    with open(output_file, "w") as f:
        f.write("\n".join(lines))

    print(f"[green]{output_file} generated successfully.[/green]")


generate_env_example(Settings)
