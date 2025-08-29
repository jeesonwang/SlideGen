from sqlalchemy import TEXT, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from slidegen.models.base import Base


class User(Base):
    __tablename__: str = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, comment="用户ID")
    username: Mapped[str] = mapped_column(
        String(length=150), unique=True, index=True, nullable=False, comment="用户帐号"
    )
    nickname: Mapped[str] = mapped_column(String(length=255), index=True, nullable=True, comment="用户昵称")
    email: Mapped[str] = mapped_column(String(length=150), index=True, nullable=False, comment="用户邮箱")
    avatar: Mapped[str] = mapped_column(TEXT, nullable=True, comment="用户头像")
    password: Mapped[str] = mapped_column(String, nullable=True, comment="用户密码")
    is_active: Mapped[bool] = mapped_column(Boolean(), default=True, nullable=False, comment="是否是激活状态")

    def __repr__(self):
        return f"<User {self.username}>"

    def __str__(self):
        return f"<User {self.username}>"
