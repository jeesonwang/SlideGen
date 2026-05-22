import json
import secrets
import warnings
from datetime import tzinfo
from pathlib import Path
from typing import Annotated, Any, Literal, Self

import pytz
from pydantic import (
    BeforeValidator,
    EmailStr,
    MySQLDsn,
    PostgresDsn,
    RedisDsn,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

PROJECT_ROOT = Path(__file__).parent.parent.parent


def parse_cors(v: Any) -> list[str]:
    if isinstance(v, str):
        value = v.strip()
        if not value:
            return []
        if value.startswith("["):
            parsed = json.loads(value)
            if not isinstance(parsed, list):
                raise ValueError(v)
            return [str(i).strip() for i in parsed if str(i).strip()]
        return [i.strip() for i in value.split(",") if i.strip()]
    elif isinstance(v, list):
        return [str(i).strip() for i in v if str(i).strip()]
    raise ValueError(v)


def parse_timezone(v: str) -> tzinfo:
    try:
        return pytz.timezone(v)
    except pytz.exceptions.UnknownTimeZoneError:
        raise ValueError(f"Unknown timezone: {v}")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # validate default value
        validate_default=False,
        # priority: the configuration in the later file will override the configuration in the earlier file
        env_file=[".env"],
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        # ignore undefined configuration
        extra="ignore",
    )

    # [CORS]
    BACKEND_CORS_ORIGINS: Annotated[list[str], NoDecode, BeforeValidator(parse_cors)] = ["*"]

    # [BASE]
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "SlideGen"
    COMPONENTS_BASE_PATH: Path = PROJECT_ROOT / "components"
    COMPONENTS_PATH: Path = COMPONENTS_BASE_PATH / "shapes" / "shapes.json"
    LOG_DIR: str = (PROJECT_ROOT / "logs").as_posix()
    OUTPUT_DIR: Path = PROJECT_ROOT / "outputs" / "presentations"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    # set environment variables in dockerfile
    UIDGID: str = "1101:1100"
    DEBUG: bool = False
    # set environment variables in dockerfile
    TZ: Annotated[tzinfo, BeforeValidator(parse_timezone)] = pytz.timezone("Asia/Shanghai")
    LOGGING_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    SYNC_THREAD_COUNT: int = 10
    SHOW_DOCS: bool = False
    DB_TYPE: Literal["MYSQL", "POSTGRES"] = "POSTGRES"
    DB_ECHO: bool = False
    # [ICONS]
    ICONS_JSON_PATH: Path = PROJECT_ROOT / "components" / "icons.json"
    ICONS_DIR: Path = PROJECT_ROOT / "components" / "icons" / "bold"

    # [THUMBNAILS]
    THUMBNAILS_DIR: Path = COMPONENTS_BASE_PATH / "templates" / "thumbnails"
    THUMBNAIL_WIDTH: int = 400  # Thumbnail width in pixels

    # [USER TEMPLATES]
    USER_TEMPLATES_DIR: Path = PROJECT_ROOT / "uploads" / "presentation_templates"
    MAX_TEMPLATE_FILE_SIZE: int = 50 * 1024 * 1024

    # [CHROMA]
    CHROMA_BASE_PATH: Path = PROJECT_ROOT / "chroma"
    CHROMA_MODELS_PATH: Path = PROJECT_ROOT / "chroma" / "models"
    CHROMA_KNOWLEDGE_PATH: Path = PROJECT_ROOT / "chroma" / "knowledge"

    # [SESSION]
    MAX_ACTIVE_SESSIONS_PER_USER: int = 10
    SESSION_SOFT_DELETE_RETENTION_DAYS: int = 30

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
    MYSQL_DB: str = "slidegen"
    MYSQL_CHARSET: str = "utf8mb4"

    # [POSTGRES]
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "slidegen"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> MySQLDsn | PostgresDsn:
        if self.DB_TYPE == "MYSQL":
            return MySQLDsn.build(
                scheme="mysql+pymysql",
                username=self.MYSQL_USER,
                password=self.MYSQL_PASSWORD,
                host=self.MYSQL_HOST,
                port=self.MYSQL_PORT,
                path=self.MYSQL_DB,
                query=f"charset={self.MYSQL_CHARSET}",
            )
        elif self.DB_TYPE == "POSTGRES":
            return PostgresDsn.build(
                scheme="postgresql+psycopg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_HOST,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        else:
            raise ValueError(f"Invalid database type: {self.DB_TYPE}")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_ASYNC_DATABASE_URI(self) -> MySQLDsn | PostgresDsn:
        if self.DB_TYPE == "MYSQL":
            return MySQLDsn.build(
                scheme="mysql+aiomysql",
                username=self.MYSQL_USER,
                password=self.MYSQL_PASSWORD,
                host=self.MYSQL_HOST,
                port=self.MYSQL_PORT,
                path=self.MYSQL_DB,
                query=f"charset={self.MYSQL_CHARSET}",
            )
        elif self.DB_TYPE == "POSTGRES":
            return PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_HOST,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        else:
            raise ValueError(f"Invalid database type: {self.DB_TYPE}")

    # [CELERY]
    SCHEDULE_PERIOD: int = 60

    # [SLIDEGEN]
    # Maximum number of sections to generate
    MAX_ITERATIONS: int = 35

    # [RENDERER]
    ENABLE_RECIPE_RENDERER: bool = False
    ENABLE_RECIPE_AGENT: bool = True

    # [USER]
    EMAIL_TEST_USER: EmailStr = "test@example.com"
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", for security, please change it, at least for deployments.'
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self._check_default_secret("FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD)

        return self


settings: Settings = Settings()  # type: ignore
