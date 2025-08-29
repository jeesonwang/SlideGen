from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from slidegen.core.security import get_password_hash, verify_password
from slidegen.models import User
from slidegen.schemas.user import UserCreate, UserUpdate


async def create_user(*, session: AsyncSession, user_create: UserCreate) -> User:
    db_obj = User(**user_create.model_dump())
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def update_user(*, session: AsyncSession, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        db_user.password = hashed_password

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def get_user_by_username_or_email(*, session: AsyncSession, username: str) -> User | None:
    statement = select(User).where(or_(User.email == username, User.username == username))
    session_user = await session.execute(statement)
    return session_user.scalar_one_or_none()


async def authenticate(*, session: AsyncSession, username: str, password: str) -> User | None:
    db_user = await get_user_by_username_or_email(session=session, username=username)
    if not db_user:
        return None
    if not verify_password(password, db_user.password):
        return None
    return db_user
