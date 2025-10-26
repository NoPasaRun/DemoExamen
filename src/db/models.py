import hashlib
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base
from db.connection import engine, create_session


class User(Base):
    username: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str] = mapped_column()

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
