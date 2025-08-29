from typing import Any

from kombu import Queue

from slidegen.config import settings

# Queue
backend_doc_process_queue = "doc_process"
backend_kb_process_queue = "kb_process"

# Task
parse_add_to_kb = "parse_add_to_kb"
add_to_kb = "add_to_kb"


class Config:
    broker_url = settings.CELERY_REDIS_URL.encoded_string()
    result_backend = broker_url

    task_serializer = "json"
    result_serializer = "json"
    accept_content = ["json"]
    timezone = settings.TZ
    enable_utc = False
    worker_hijack_root_logger = True  # forbid celery to use root logger

    # task config
    # task_ignore_result = True  # Whether to ignore the result of the task
    task_track_started = False  # When the task starts, report, note that this setting conflicts with ignore_result
    task_acks_late = False

    # worker config
    worker_prefetch_multiplier = 1  # The number of tasks each worker gets per IO
    worker_max_tasks_per_child = 1000  # After executing this number of tasks, destroy and rebuild a new process
    worker_cancel_long_running_tasks_on_connection_loss = False

    # Enable monitoring
    worker_send_task_events = True
    task_send_sent_event = True

    # broker
    broker_transport_options = {
        "visibility_timeout": 3600 * 24 * 7,  # 7 days
        "max_retries": 0,
    }

    task_queues = (
        Queue(backend_doc_process_queue),
        Queue(backend_kb_process_queue),
    )

    task_routes = {
        "parse_add_to_kb": {"queue": backend_doc_process_queue},
        "add_to_kb": {"queue": backend_kb_process_queue},
    }

    beat_schedule: dict[str, Any] = {}
