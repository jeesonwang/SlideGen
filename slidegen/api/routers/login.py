from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from slidegen.api.deps import CurrentUser, SessionDep
from slidegen.common.security import create_access_token, get_password_hash
from slidegen.common.user_center import UserCenter
from slidegen.config import settings
from slidegen.exception.custom_exception import ExpireTokenError, PasswordError, UserLockError, UserNotExistsError
from slidegen.models.user import Message, NewPassword, Token, UserPublic
from slidegen.utils import verify_password_reset_token

router = APIRouter()


@router.post("/access-token")
async def login_access_token(session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """

    user_center = UserCenter(session=session)
    user = await user_center.authenticate(username=form_data.username, password=form_data.password)
    if not user:
        raise PasswordError("email or password is incorrect")
    elif not user.is_active:
        raise UserLockError("Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(access_token=create_access_token(user.id, expires_delta=access_token_expires))


@router.post("/test-token", response_model=UserPublic)
def test_token(current_user: CurrentUser) -> Any:
    """
    Test access token
    """
    return current_user


@router.post("/reset-password/")
async def reset_password(session: SessionDep, body: NewPassword) -> Message:
    """
    Reset password
    """
    email = verify_password_reset_token(token=body.token)
    if not email:
        raise ExpireTokenError("Invalid token")
    user_center = UserCenter(session=session)
    user = await user_center.get_user_by_username_or_email(username=email)
    if not user:
        raise UserNotExistsError("The user with this email does not exist in the system.")
    elif not user.is_active:
        raise UserLockError("Inactive user")
    hashed_password = get_password_hash(password=body.new_password)
    user.hashed_password = hashed_password  # type: ignore
    session.add(user)
    await session.commit()
    return Message(message="Password updated successfully")
