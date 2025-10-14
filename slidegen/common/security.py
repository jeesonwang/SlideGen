import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext  # type: ignore

from slidegen.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    expire = datetime.now(UTC) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def generate_api_key() -> tuple[str, str]:
    """
    生成API密钥
    返回: (原始密钥, 密钥哈希)
    """
    raw_key = secrets.token_urlsafe(32)
    api_key = f"ck_{raw_key}"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return api_key, key_hash


def verify_api_key(api_key: str, stored_hash: str) -> bool:
    """
    验证API密钥
    """
    computed_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return computed_hash == stored_hash


def extract_user_id_from_api_key(api_key: str) -> str | None:
    """
    从API密钥中提取用户ID（这里我们需要从数据库查询）
    这个函数主要用于标识API密钥的格式
    """
    if api_key.startswith("ck_"):
        return api_key  # 返回完整的API密钥，用于数据库查询
    return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
