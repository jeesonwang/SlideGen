from datetime import tzinfo
from pathlib import Path
from typing import Annotated, Any, Literal

import pytz
from pydantic import (
    AnyUrl,
    BeforeValidator,
    MySQLDsn,
    RedisDsn,
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

# 将 BASE_DIR 加入python搜索路径, 使用.env文件中的PYTHONPATH替代了，注释掉备用
BASE_DIR = Path(__file__).parent.parent
# sys.path.insert(0, BASE_DIR)


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


def parse_timezone(v: str) -> tzinfo:
    try:
        return pytz.timezone(v)
    except pytz.exceptions.UnknownTimeZoneError:
        raise ValueError(f"Unknown timezone: {v}")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # 验证默认值是否正确
        validate_default=False,
        # 优先级：后面文件的配置会覆盖前面文件的配置
        env_file=[".env"],
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        # 忽略未定义的配置
        extra="ignore",
    )
    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = []

    # [BASE]
    PROJECT_NAME: str = "SlideGen"
    COMPONENTS_BASE_PATH: Path = BASE_DIR.parent / "components"
    COMPONENTS_PATH: Path = COMPONENTS_BASE_PATH / "shapes" / "shapes.json"
    # 设置 dockerfile 中的环境变量
    UIDGID: str = "1101:1100"
    DEBUG: bool = False
    # 设置 dockerfile 中的环境变量
    TZ: Annotated[tzinfo, BeforeValidator(parse_timezone)] = pytz.timezone("Asia/Shanghai")
    LOGGING_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    SYNC_THREAD_COUNT: int = 10
    SHOW_DOCS: bool = False
    DB_TYPE: Literal["MYSQL"] = "MYSQL"

    # [REDIS]
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str
    CELERY_BROKER_DB: int = 0
    REDIS_CACHE_DB: int = 1

    @computed_field  # type: ignore[prop-decorator]
    @property
    def CELERY_REDIS_URL(self) -> RedisDsn:
        return RedisDsn.build(
            scheme="redis",
            host=self.REDIS_HOST,
            port=self.REDIS_PORT,
            password=self.REDIS_PASSWORD,
            path=f"/{self.CELERY_BROKER_DB}",
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def REDIS_CACHE_URL(self) -> RedisDsn:
        return RedisDsn.build(
            scheme="redis",
            host=self.REDIS_HOST,
            port=self.REDIS_PORT,
            password=self.REDIS_PASSWORD,
            path=f"/{self.REDIS_CACHE_DB}",
        )

    # [MYSQL]
    MYSQL_HOST: str
    MYSQL_PORT: int = 3306
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DB: str
    MYSQL_CHARSET: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> MySQLDsn:
        return MySQLDsn.build(
            scheme="mysql+pymysql",
            username=self.MYSQL_USER,
            password=self.MYSQL_PASSWORD,
            host=self.MYSQL_HOST,
            port=self.MYSQL_PORT,
            path=self.MYSQL_DB,
            query=f"charset={self.MYSQL_CHARSET}",
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_ASYNC_DATABASE_URI(self) -> MySQLDsn:
        return MySQLDsn.build(
            scheme="mysql+aiomysql",
            username=self.MYSQL_USER,
            password=self.MYSQL_PASSWORD,
            host=self.MYSQL_HOST,
            port=self.MYSQL_PORT,
            path=self.MYSQL_DB,
            query=f"charset={self.MYSQL_CHARSET}",
        )

    # [CELERY]
    SCHEDULE_PERIOD: int = 60


settings: Settings = Settings()  # type: ignore
