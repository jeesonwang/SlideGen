from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import or_, select

from slidegen.common.security import get_password_hash, verify_password
from slidegen.models.user import UserCreate, UserModel, UserUpdate


class UserCenter:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, user_create: UserCreate) -> UserModel:
        db_obj = UserModel.model_validate(
            user_create, update={"hashed_password": get_password_hash(user_create.password)}
        )
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def update_user(self, db_user: UserModel, user_in: UserUpdate) -> UserModel:
        user_data = user_in.model_dump(exclude_unset=True)
        extra_data = {}
        if "password" in user_data:
            password = user_data["password"]
            hashed_password = get_password_hash(password)
            extra_data["hashed_password"] = hashed_password
        db_user.sqlmodel_update(user_data, update=extra_data)
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user

    async def get_user_by_username_or_email(self, username: str) -> UserModel | None:
        statement = select(UserModel).where(or_(UserModel.email == username, UserModel.username == username))
        result = await self.session.execute(statement)
        session_user = result.scalar_one_or_none()
        return session_user

    async def authenticate(self, username: str, password: str) -> UserModel | None:
        db_user = await self.get_user_by_username_or_email(username=username)
        if not db_user:
            return None
        if not verify_password(password, str(db_user.hashed_password)):
            return None
        return db_user
