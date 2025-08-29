from typing import Annotated

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from slidegen.common import security
from slidegen.config import settings
from slidegen.engine.database import get_db_session, get_sync_db_session
from slidegen.exception.custom_exception import AuthDenyError, PermissionDenyError, UserLockError, UserNotExistsError
from slidegen.models.user import TokenPayload, UserModel

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login/access-token")
TokenDep = Annotated[str, Depends(reusable_oauth2)]


SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
SyncSessionDep = Annotated[Session, Depends(get_sync_db_session)]


async def get_current_user(session: SessionDep, token: TokenDep) -> UserModel:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise AuthDenyError("Could not validate credentials")
    user = await session.get(UserModel, token_data.sub)
    if not user:
        raise UserNotExistsError("User not found")
    if not user.is_active:
        raise UserLockError("Inactive user")
    return user


CurrentUser = Annotated[UserModel, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> UserModel:
    if not current_user.is_superuser:
        raise PermissionDenyError("The user doesn't have enough privileges")
    return current_user


def valid_api_key_dependency(
    request: Request,
    credential: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> None:
    """Validate the API token.

    Args:
        request (Request): The incoming request.
        credential (HTTPAuthorizationCredentials, optional): The extracted credentials. Defaults to Depends(HTTPBearer(auto_error=False)).

    Raises:
        HTTPException: Raised if the token is missing or invalid.
    """
    if request.app.state.api_key:
        if not credential or credential.credentials != request.app.state.api_key:
            raise AuthDenyError("Unauthorized")
