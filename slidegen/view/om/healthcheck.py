from view.core import BaseView


class HealthCheckView(BaseView):
    path = "/healthcheck"

    async def get(self):
        return self.response(message="ok")
