import uuid
from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import func, select

from slidegen.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from slidegen.common.security import get_password_hash, verify_password
from slidegen.common.user_center import UserCenter
from slidegen.exception.custom_exception import (
    NotFoundError,
    ParamsCheckError,
    PasswordError,
    PermissionDenyError,
    UserExistsError,
)
from slidegen.models.user import (
    Message,
    UpdatePassword,
    UserCreate,
    UserModel,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
)

router = APIRouter(tags=["User"])


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
async def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """

    count_statement = select(func.count()).select_from(UserModel)
    count = (await session.execute(count_statement)).scalar_one()

    statement = select(UserModel).offset(skip).limit(limit)
    users = (await session.execute(statement)).scalars().all()

    return UsersPublic(data=users, count=count)


@router.post("/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic)
async def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
    """
    Create new user. Need to be superuser.
    """
    user_center = UserCenter(session=session)
    user = await user_center.get_user_by_username_or_email(username=user_in.email)
    if user:
        raise UserExistsError("The user with this email already exists in the system.")

    user = await user_center.create_user(user_create=user_in)

    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
async def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """
    user_center = UserCenter(session=session)
    db_user = await session.get(UserModel, user_id)
    if not db_user:
        raise NotFoundError("The user with this id does not exist in the system")
    if user_in.email:
        existing_user = await user_center.get_user_by_username_or_email(username=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise UserExistsError("User with this email already exists")

    db_user = await user_center.update_user(db_user=db_user, user_in=user_in)
    return db_user


@router.patch("/me/password", response_model=Message)
async def update_password_me(*, session: SessionDep, body: UpdatePassword, current_user: CurrentUser) -> Any:
    """
    Update own password.
    """
    if not verify_password(body.current_password, current_user.hashed_password):
        raise PasswordError("Incorrect password")
    if body.current_password == body.new_password:
        raise ParamsCheckError("New password cannot be the same as the current one")
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    await session.commit()
    return Message(message="Password updated successfully")


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@router.delete("/me", response_model=Message)
async def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own user.
    """
    if current_user.is_superuser:
        raise PermissionDenyError("Super users are not allowed to delete themselves")
    await session.delete(current_user)
    await session.commit()
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
async def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user_center = UserCenter(session=session)
    user = await user_center.get_user_by_username_or_email(username=user_in.email)
    if user:
        raise UserExistsError("The user with this email already exists in the system")
    user_create = UserCreate.model_validate(user_in)
    user = await user_center.create_user(user_create=user_create)
    return user


@router.get("/{user_id}", response_model=UserPublic)
async def read_user_by_id(user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Get a specific user by id.
    """
    user = await session.get(UserModel, user_id)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise PermissionDenyError("The user doesn't have enough privileges")
    return user


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
async def delete_user(session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID) -> Message:
    """
    Delete a user.
    """
    user = await session.get(UserModel, user_id)
    if not user:
        raise NotFoundError("User not found")
    if user == current_user:
        raise PermissionDenyError("Super users are not allowed to delete themselves")
    await session.delete(user)
    await session.commit()
    return Message(message="User deleted successfully")
