import os
import sys

import pytz
from dotenv import load_dotenv

# 将 BASE_DIR 加入python搜索路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# [读取.env文件，转化为环境变量]
# 当启用Docker secret功能时,读取secret ENV
secret_dir = "/run/secrets"
if os.path.isdir(secret_dir):
    for secret_filename in os.listdir(secret_dir):
        load_dotenv(os.path.join(secret_dir, secret_filename))
load_dotenv()

# [BASE]
UIDGID = os.getenv("USER", "1101:1100")
ENV = os.getenv("ENV")
DEBUG = ENV == "dev"
TZ = pytz.timezone(os.getenv("TZ", "Asia/Shanghai"))
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")
SYNC_THREAD_COUNT = int(os.getenv("SYNC_THREAD_COUNT", 10))
SHOW_DOCS = os.getenv("SHOW_DOCS", False)

# [REDIS]
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
CELERY_BROKER_DB = int(os.getenv("REDIS_DB", 0))

# [DB_TYPE]
DB_TYPE = os.getenv("DB_TYPE", "MYSQL")

# [MYSQL]
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_ROOT_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")
MYSQL_CHARSET = os.getenv("MYSQL_CHARSET")

# [CELERY]
SCHEDULE_PERIOD = int(os.getenv("SCHEDULE_PERIOD", 60))
