from typing import Annotated

from fastapi import Path

from slidegen.controller.example.prompt import ExamplePrompt
from slidegen.view.core import BaseView, api_description


class ExamplePromptView(BaseView):
    @api_description(summary="获取提示语", description="支持多种模式...")
    async def get(
        self,
        is_activate: Annotated[int | None, Path(title="是否启用")] = None,
        page: Annotated[int | None, Path(title="分页页数", ge=1)] = None,
    ):
        prompt_items, pager = await ExamplePrompt.get_prompt_items(is_activate=is_activate)
        return self.response(data=prompt_items, pager=pager)
