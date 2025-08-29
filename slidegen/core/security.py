import secrets
import string
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import jwt
from passlib.context import CryptContext  # type: ignore

from slidegen.core import settings

pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

ALGORITHM = "HS512"


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    if not isinstance(encoded_jwt, str):
        raise ValueError("Failed to encode access token")
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    verify_ret = pwd_context.verify(plain_password, hashed_password)
    if not isinstance(verify_ret, bool):
        return False
    return verify_ret


def get_password_hash(password: str) -> str:
    hash_pwd = pwd_context.hash(password)
    if not isinstance(hash_pwd, str):
        raise ValueError("Failed to hash password")
    return hash_pwd


def verify_token(token: str) -> dict:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    return payload


def generate_password(length: int) -> str:
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = "".join(secrets.choice(alphabet) for _ in range(length))
    return password
