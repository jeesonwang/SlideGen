import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext

from slidegen.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    expire = datetime.now(UTC) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def generate_api_key() -> tuple[str, str]:
    """
    Generate API key
    Returns: (original key, key hash)
    """
    raw_key = secrets.token_urlsafe(32)
    api_key = f"ck_{raw_key}"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return api_key, key_hash


def verify_api_key(api_key: str, stored_hash: str) -> bool:
    """
    Verify API key
    """
    computed_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return computed_hash == stored_hash


def extract_user_id_from_api_key(api_key: str) -> str | None:
    """
    Extract user ID from API key (here we need to query from database)
    This function is mainly used to identify the format of the API key
    """
    if api_key.startswith("ck_"):
        return api_key  # Return the complete API key for database query
    return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
