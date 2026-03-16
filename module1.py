import os
from datetime import datetime
from pathlib import Path
from typing import List, Any

from sqlalchemy import (
    Column, Integer, create_engine,
    String, Float, ForeignKey,
    UniqueConstraint, DateTime
)
from sqlalchemy.orm import (
    DeclarativeBase,
    relationship,
    sessionmaker)

import openpyxl


engine = create_engine("postgresql+psycopg2://{}:{}@{}:{}/{}".format(
    "bogdan", "bogdan", "localhost", "5432", "demo"
))
Session = sessionmaker(bind=engine)
ROOT = Path(__file__).parent.resolve()


def get_data(filepath: str, first_line_pass: bool = True) -> List[List[Any]]:
    sheet = openpyxl.load_workbook(filepath).active
    return [
        list(row) for row in sheet.iter_rows(
            min_row=int(first_line_pass) + 1,
            values_only=True
        ) if row[0]
    ]


def save_data(session, model, rows, exclude = None):
    session.add_all(
        [model(**{key: value for key, value in zip(
            model.get_columns(exclude), row
        )}) for row in rows]
    )
    session.flush()


class Base(DeclarativeBase):
    __abstract__ = True

    @classmethod
    def get_columns(cls, exclude = None):
        exclude = exclude or set()
        return [col.key for col in cls.__table__.columns if col.key not in exclude]

    @classmethod
    def get_fields(cls, exclude = None):
        return [
            (getattr(cls, col).info.get("label"), col)
            for col in cls.get_columns(exclude)
        ]


class Company(Base):
    __tablename__ = "company"
    name = Column(String, primary_key=True, info={"label": "компания", "display": True})


class Product(Base):
    __tablename__ = "product"
    articul = Column(String, primary_key=True, info={"label": "артикул"})
    name = Column(String, info={"label": "название"})
    measure_type = Column(String, info={"label": "единица измерения"})
    price = Column(Float, info={"label": "цена"})

    supplier_name = Column(String, ForeignKey("company.name"), info={"label": "поставщик"})
    supplier = relationship(Company, foreign_keys=[supplier_name])

    man_name = Column(String, ForeignKey("company.name"), info={"label": "производитель"})
    man = relationship(Company, foreign_keys=[man_name])
    category = Column(String, info={"label": "категория"})
    discount = Column(Float, default=0, info={"label": "скидка"})
    quantity = Column(Integer, info={"label": "количество"})
    description = Column(String, info={"label": "описание"})
    photo = Column(String, nullable=True, info={"label": "Фото", "type": "image"})

    @property
    def fixed_price(self):
        return round(self.price * (1 - self.discount / 100), 2)

    @property
    def valid_photo(self):
        if self.photo and os.path.exists(self.photo):
            return self.photo
        return str(ROOT / 'import/picture.png')


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    role = Column(String)
    fio = Column(String, info={"display": True, "label": "ФИО"})
    login = Column(String, unique=True)
    password = Column(String)


class Address(Base):
    __tablename__ = "address"
    id = Column(Integer, primary_key=True)
    description = Column(String)


class OrderItem(Base):
    __tablename__ = "order_item"
    id = Column(Integer, primary_key=True)
    order_articul = Column(Integer, ForeignKey("order.articul"), info={"label": "Товары", "display": True})
    product_articul = Column(String, ForeignKey("product.articul"))
    quantity = Column(Integer)
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product")

    __table_args__ = (UniqueConstraint("order_articul", "product_articul"),)


class Order(Base):
    __tablename__ = "order"
    articul = Column(Integer, primary_key=True, info={"label": "артикул"})
    created_at = Column(DateTime, nullable=True, info={"label": "дата создания"})
    deliver_at = Column(DateTime, nullable=True, info={"label": "дата доставки"})
    address_id = Column(Integer, ForeignKey("address.id"), info={"label": "адрес", "mode": "create"})
    user_id = Column(Integer, ForeignKey("user.id"), info={"label": "пользователь"})
    address = relationship("Address")
    user = relationship("User")
    code = Column(Integer, info={"label": "код", "range": (0, 999)})
    status = Column(String, info={"label": "статус", "choices": [("Новый", "Новый"), ("Старый", "Старый")]})

    order_items = relationship(
        OrderItem,
        back_populates="order",
        cascade="all, delete",
        info={
            "label": "состав заказа",
            "mode": "create",
            "columns": ["product_articul", "quantity"]
        }
    )


def main():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with Session() as session:
        product_data = get_data("import/Tovar.xlsx")
        companies_names = {row[4] for row in product_data} | {row[5] for row in product_data}
        save_data(session, Company, [[name] for name in companies_names])

        for row in product_data:
            row[10] = str(ROOT / 'import' / (row[10] or 'picture.png'))
        save_data(session, Product, product_data)

        save_data(session, User, get_data("import/user_import.xlsx"), exclude={"id"})
        save_data(
            session, Address,
            get_data("import/Пункты выдачи_import.xlsx", first_line_pass=False), exclude={"id"}
        )

        order_data = get_data("import/Заказ_import.xlsx")
        order_item_data = [
            [row[0], *row_data]
            for row in order_data
            for row_data in zip(row[1].split(", ")[::2], row[1].split(", ")[1::2])
        ]

        for row in order_data:
            row[2] = row[2] if isinstance(row[2], datetime) else datetime(year=2025, month=3, day=2)
            row[5] = session.query(User).filter_by(fio=row[5]).first().id
            row.pop(1)

        save_data(session, Order, order_data)
        save_data(session, OrderItem, order_item_data, exclude={"id"})
        session.commit()


if __name__ == '__main__':
    main()
