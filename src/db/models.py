from db.base import Base
from db.connection import engine


class User(Base):
    pass


if __name__ == '__main__':
    Base.metadata.create_all(engine)
