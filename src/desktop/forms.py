from typing import Optional

from pydantic import BaseModel, model_validator
from pydantic_core import PydanticCustomError

from db.connection import create_session
from db.models import User


class LoginForm(BaseModel):
    username: str
    password: str

    @model_validator(mode="after")
    def validate_username(self) -> User:
        with create_session() as session:
            users = User.filter(session, User.username == self.username)
        if not users:
            raise PydanticCustomError(
                "value_error",
                "пользователь не найден",
                {"field": "username"}
            )
        user: User = users[0]
        if not user.check_password(self.password):
            raise PydanticCustomError(
                "value_error",
                "пароль не подходит",
                {"field": "password"}

            )
        setattr(self, "_user", user)
        return self

    @property
    def user(self) -> Optional[User]:
        if hasattr(self, "_user"):
            return getattr(self, "_user")
        return None


class SearchProductForm(BaseModel):
    q: str = ""
    min_price: float = 0
    max_price: float = float('inf')
