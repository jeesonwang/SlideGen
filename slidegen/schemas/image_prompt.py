from __future__ import annotations

from pydantic import BaseModel, Field


class ImagePrompt(BaseModel):
    prompt: str = Field(..., description="基础文案提示")
    theme_prompt: str | None = Field(default=None, description="主题风格提示，可选")

    def get_image_prompt(self, with_theme: bool = True) -> str:
        base = self.prompt.strip()
        if with_theme and self.theme_prompt:
            theme = self.theme_prompt.strip()
            if theme:
                return f"{base}, {theme}"
        return base
