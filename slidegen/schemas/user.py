from pydantic import BaseModel, ConfigDict, EmailStr, Field

from slidegen.schemas.base_schemas import BaseSchema


class UserBase(BaseSchema):
    aid: str | None = Field(default=None, title="supabase用户ID", description="supabase用户ID")
    avatar: str | None = Field(default=None, title="头像", description="头像")
    email: EmailStr | None = Field(default=None, title="邮箱", description="邮箱")
    is_active: bool | None = Field(default=True, title="是否激活", description="是否激活")
    is_super: bool | None = Field(default=False, title="是否超级用户", description="是否超级用户")
    username: str | None = Field(default=None, title="用户名", description="用户名")
    nickname: str | None = Field(default=None, title="昵称", description="昵称")

    model_config = ConfigDict(from_attributes=True)


class UserInfo(BaseModel):
    roles: list[str] = Field(default=[], description="The user's roles")
    real_name: str = Field(default="", description="The user's real name")
    desc: str = Field(default="vben 用户自介绍", description="The user's description")
    home_path: str = Field(default="/dashboard", alias="homePath", description="The user's home path")


class UserCreate(UserBase):
    username: str = Field(..., description="The user's username")
    email: str = Field(..., description="The user's email")
    password: str = Field(..., description="The user's password")


class UserUpdate(UserBase):
    username: str | None = Field(None, description="The user's username")
    email: str | None = Field(None, description="The user's email")
    password: str | None = Field(None, description="The user's password")


class UserPublic(BaseModel):
    id: int = Field(..., description="The user's id")
    username: str = Field(..., description="The user's username")


class UserRegister(BaseModel):
    username: str = Field(..., description="The user's username")
    email: str = Field(..., description="The user's email")
    password: str = Field(..., description="The user's password")


class UserLogin(BaseModel):
    username: str = Field(..., description="The user's username")
    password: str = Field(..., description="The user's password")
