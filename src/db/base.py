import re
from datetime import datetime

from sqlalchemy import update, text, select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    Session,
    declared_attr
)
from typing import Set


class Base(DeclarativeBase):
    __abstract__ = True

    DATETIME_FORMAT: str = "%d-%m-%Y %H:%M"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    extra: Set = set()
    exclude: Set = set()

    @declared_attr
    def __tablename__(cls):
        return "_".join(
            word.lower() for word in
            re.findall(
                r'\b[A-Z][A-Za-z]*\b',
                cls.__name__.capitalize()
            )
        )

    def __repr__(self):
        return f"{self.model.__name__}(" + ", ".join([
            f"{k}={getattr(self, k)}" for k in self.get_columns()
        ]) + ")"

    def __new__(cls, **kwargs):
        obj = super().__new__(cls)
        obj._update_values = dict()
        return obj

    @classmethod
    def get_columns(cls):
        return set([column.key for column in cls.__table__.columns])

    def __iter__(self):
        for attr_name in (self.get_columns() | self.extra) - self.exclude:
            if not hasattr(self, attr_name):
                continue
            obj = getattr(self, attr_name)
            if Base in obj.__class__.mro():
                value = obj.as_dict()
            elif isinstance(obj, list):
                value = [
                    (item.as_dict() if Base in item.__class__.mro() else item)
                    for item in obj
                ]
            elif isinstance(obj, datetime):
                value = getattr(self, attr_name).strftime(
                    self.DATETIME_FORMAT
                )
            else:
                value = getattr(self, attr_name)
            yield attr_name, value

    @property
    def model(self):
        return self.__class__

    def __setattr__(self, key, value):
        if hasattr(self, "_update_values"):
            self._update_values[key] = value
        super().__setattr__(key, value)

    @classmethod
    def get(cls, session: Session, _id: int):
        return session.get(cls, _id)

    @classmethod
    def filter(cls, session: Session, *args):
        res = session.execute(select(cls).where(*args))
        return res.scalars().all()

    def delete(self, session: Session):
        session.delete(self)

    def update(self, session: Session):
        sql = update(self.model).values(
            **self._update_values
        ).where(self.model.id == self.id)
        session.execute(sql)

    def insert(self, session: Session):
        session.add(self)

    def save(self, session: Session):
        if self.id:
            return self.update(session)
        self.insert(session)
