from pydantic import BaseModel, model_validator
from db.models import User
from db.connection import create_session
from forms.base import BaseForm


class LoginForm(BaseModel, metaclass=BaseForm):
    username: str
    password: str

    @model_validator(mode="after")
    def validate_user(self):
        with create_session() as session:
            users = User.filter(session, User.username == self.username)
        if not users or not users[0].check_password(self.password):
            raise ValueError("пользователь не найден или неверный пароль")
        return self
