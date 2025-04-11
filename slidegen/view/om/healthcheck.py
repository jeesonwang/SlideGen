from typing import Any

from slidegen.view.core import BaseView


class HealthCheckView(BaseView):
    path = "/healthcheck"

    async def get(self) -> dict[str, Any]:
        return self.response(message="ok")
