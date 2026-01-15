from celery import Celery

from slidegen.core.celery_config import Config

celery_app = Celery()
celery_app.config_from_object(Config)
celery_app.set_default()
celery_app.autodiscover_tasks(["slidegen.tasks"], "slidegen_tasks", True)
