from typing import Any

from pydantic_settings import BaseSettings
from rich import print

from slidegen.config.conf import BASE_DIR, Settings


def generate_env_sample(settings_class: type[BaseSettings], output_file: str = BASE_DIR.parent / ".env.sample") -> None:
    fields: dict[str, Any] = settings_class.model_fields
    lines = ["PYTHONPATH=."]

    for name, field in fields.items():
        env_name = field.alias or name.upper()
        if field.default is not None:
            line = f"{env_name}={field.default}"
        else:
            line = f"{env_name}="
        lines.append(line)

    with open(output_file, "w") as f:
        f.write("\n".join(lines))

    print(f"[green]{output_file} generated successfully.[/green]")


# 使用示例
generate_env_sample(Settings)
