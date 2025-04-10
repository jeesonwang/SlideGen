from .conf import settings

broker_url = settings.CELERY_REDIS_URL
result_backend = settings.CELERY_REDIS_URL

task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = settings.TZ
enable_utc = False
worker_hijack_root_logger = False  # 禁止celery拦截日志配置(使用loguru的任务配置)

# task config
# task_ignore_result = True  # 是否全局设置任务忽略结果
task_track_started = False  # 当任务启动时报告,需要注意此设置和ignore_result相关配置冲突

# worker config
worker_prefetch_multiplier = 1  # 每个worker每次IO所获取的任务数量
worker_max_tasks_per_child = 1000  # 执行该任务数后销毁重建新进程
worker_cancel_long_running_tasks_on_connection_loss = False

# broker
broker_transport_options = {"visibility_timeout": 3600 * 24 * 7, "max_retries": 0}  # 7 days

task_queues = ()

task_routes = ()

beat_schedule = {}
