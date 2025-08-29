from celery import Celery

from slidegen.config import Config

celery_app = Celery()
celery_app.config_from_object(Config)
celery_app.set_default()
celery_app.autodiscover_tasks(["app"], "tasks", True)
