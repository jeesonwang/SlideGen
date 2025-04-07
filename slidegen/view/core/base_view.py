import inspect

from fastapi import APIRouter, Depends

from contexts import g
from engine.rdb import get_db, get_db_sync
from contexts.schema import Pager

base_router = APIRouter()


class BaseView:
    permissions_classes = []
    path: str = None

    def __init__(self, path: str, tags: list[str]):
        self.path = path or self.path
        self.tags = tags or getattr(self, "tags", None)
        self.register_routes()

    @property
    def request(self):
        return g.request

    @property
    def user(self):
        return g.user

    @property
    def user_id(self):
        return g.user.id

    @property
    def role_ids(self):
        return g.user.role_ids

    @staticmethod
    def response(code: int = 0, message: str = "请求成功", data: dict | None | list | str = None, pager: Pager = None):
        if isinstance(data, list):
            if pager:
                data = {"items": data or [], **pager.model_dump()}
            else:
                data = {"items": data or []}

        return {"code": code, "message": message, "trace_id": g.trace_id, "data": data or {}}

    def get_dependencies(self, extra_params: dict, method):
        custom_permission_classes = extra_params.pop("permission_classes", None)
        custom_authentication_classes = extra_params.pop("authentication_classes", None)
        authentication_classes = (
            custom_authentication_classes if custom_authentication_classes is not None else self.authentication_classes
        )
        permission_classes = (
            custom_permission_classes if custom_permission_classes is not None else self.permissions_classes
        )
        dependencies = [Depends(_(name="")(method)) for _ in authentication_classes] + [
            Depends(_(method)) for _ in permission_classes
        ]
        if inspect.iscoroutinefunction(method):
            dependencies += [Depends(get_db)]
        else:
            dependencies += [Depends(get_db_sync)]
        return dependencies

    def register_routes(self):
        method_map = {
            "get": {
                "path": self.path,
                "methods": ["GET"],
            },
            "post": {
                "path": self.path,
                "methods": ["POST"],
            },
            "put": {
                "path": self.path,
                "methods": ["PUT"],
            },
            "delete": {
                "path": self.path,
                "methods": ["DELETE"],
            },
        }
        for method_name, router_info in method_map.items():
            method = getattr(self, method_name, None)
            if self.is_method_overridden(method_name):
                extra_params = getattr(method, "_extra_params", {})
                dependencies = self.get_dependencies(extra_params, method)
                base_router.add_api_route(
                    router_info["path"],
                    method,
                    methods=router_info["methods"],
                    dependencies=dependencies,
                    tags=self.tags,
                    **extra_params,
                )

    def is_method_overridden(self, method_name: str) -> bool:
        subclass_method = getattr(self, method_name, None)
        base_method = getattr(BaseView, method_name, None)
        if not subclass_method or not base_method:
            return False
        # Check if the method is overridden
        return inspect.getmodule(subclass_method) != inspect.getmodule(base_method)

    def get(self, *args, **kwargs):
        raise ImportError("Not implemented")

    def post(self, *args, **kwargs):
        raise ImportError("Not implemented")

    def put(self, *args, **kwargs):
        raise ImportError("Not implemented")

    def delete(self, *args, **kwargs):
        raise ImportError("Not implemented")
