import base64
import hashlib
from datetime import datetime

from sqlalchemy import Integer, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from db.connection import engine, create_session
from settings import app_settings


class User(Base):
    username: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str] = mapped_column()

    exclude = {"password_hash", "id"}
    extra = {"encrypt_user_id"}

    @property
    def encrypt_user_id(self) -> str:
        data = f"{self.id}:{app_settings.salt}:{datetime.utcnow()}".encode('utf-8')
        return base64.urlsafe_b64encode(data).decode('utf-8')

    @classmethod
    def decrypt_user_id(cls, encrypted_id: str) -> int:
        decoded = base64.urlsafe_b64decode(encrypted_id).decode('utf-8')
        user_id_str, received_salt, _ = decoded.split(':')
        if received_salt != app_settings.salt:
            raise ValueError("Неверная соль")
        return int(user_id_str)

    @staticmethod
    def hash_string(string: str):
        return hashlib.sha256(string.encode("utf-8")).hexdigest()

    def set_password(self, password: str):
        self.password_hash = self.hash_string(password)

    def check_password(self, password: str):
        return self.password_hash == self.hash_string(password)


if __name__ == '__main__':
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with create_session() as session:
        user = User(username="user")
        user.set_password("user")
        user.save(session)
