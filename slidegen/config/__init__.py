from .celery_config import Config
from .conf import settings

conf_settings = settings

__all__ = ["conf_settings", "settings", "Config"]
