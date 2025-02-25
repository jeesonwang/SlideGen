from typing import Any
import inspect

from fastapi import APIRouter, Depends

from core import g
from engine.rdb import get_db

base_router = APIRouter()


class BaseView:
    method_decorators = []
    path: str = None

    def __init__(self, path: str, tags: list[str]):
        self.path = path or getattr(self, "path")
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


    def get_dependencies(self, extra_params: dict, method):
        custom_permission_classes = extra_params.pop('permission_classes', None)
        custom_authentication_classes = extra_params.pop('authentication_classes', None)
        authentication_classes = (custom_authentication_classes if custom_authentication_classes is not None
                                  else self.authentication_classes)
        permission_classes = (custom_permission_classes if custom_permission_classes is not None else
                              self.permissions_classes)
        dependencies = [Depends(_(name='')(method)) for _ in authentication_classes] + \
                       [Depends(_(method)) for _ in permission_classes]
        depend_session: bool = extra_params.pop("depend_session", True)
        if depend_session:
            dependencies.append(Depends(get_db))
        return dependencies

    def register_routes(self):
        method_map = {
            "get": ["GET"],
            "post": ["POST"],
            "put": ["PUT"],
            "delete": ["DELETE"],
        }
        for func_name, methods in method_map.items():
            endpoint = getattr(self, func_name, None)
            if not endpoint:
                continue
            for decorator in self.method_decorators:
                endpoint = decorator(endpoint)
            if self.is_method_overridden(func_name):
                extra_params = getattr(endpoint, "_extra_params", {})
                base_router.add_api_route(path=self.path,
                                          endpoint=endpoint,
                                          methods=methods,
                                          tags=self.tags,
                                          **extra_params)

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

