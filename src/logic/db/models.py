from datetime import datetime

from sqlalchemy import insert
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Set


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column()
    extra: Set = set()

    @classmethod
    def get_columns(cls):
        return set([column.key for column in cls.__table__.columns])

    def as_dict(self):
        data = dict()
        for attr_name in self.get_columns() | self.extra:
            if not hasattr(self, attr_name):
                continue
            obj = getattr(self, attr_name)
            if Base in obj.__class__.__base__:
                data[attr_name] = obj.as_dict()
                continue
            if isinstance(obj, list):
                data[attr_name] = [item.as_dict() for item in obj]
                continue
            data[attr_name] = getattr(self, attr_name)
        return data

    def update(self, session):
        pass

    def insert(self, session):
        session.add(self)
        return True

    def save(self, session):
        if self.id:
            return self.update(session)
        return self.insert(session)


