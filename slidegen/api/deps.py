from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from slidegen.core import security, settings
from slidegen.core.engine import get_db, get_db_async
from slidegen.models import User

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/login")


SyncDB = Annotated[AsyncSession, Depends(get_db)]
AsyncDB = Annotated[AsyncSession, Depends(get_db_async)]

TokenDep = Annotated[str, Depends(reusable_oauth2)]


async def get_current_user(session: AsyncDB, token: TokenDep) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    user = await session.get(User, payload)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


ActiveCurrentUser = Annotated[User, Depends(get_current_active_superuser)]
