import os
from datetime import datetime
from pathlib import Path
from typing import List, Any

from sqlalchemy import (
    Column, Integer, create_engine,
    String, Float, ForeignKey,
    UniqueConstraint, DateTime, Boolean
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
    def filter(cls, session, **kwargs):
        return session.query(cls).filter_by(**kwargs)


class Company(Base):
    __tablename__ = "company"
    name = Column(String, primary_key=True, info={"label": "название"})

    verbose_name = "компании"

    def __str__(self):
        return self.name


class Product(Base):
    __tablename__ = "product"
    articul = Column(String, primary_key=True, info={"label": "артикул"})
    name = Column(String, info={"label": "название"})
    measure_type = Column(String, info={"label": "единица измерения"})
    price = Column(Float, info={"label": "цена", "range": (0, 1_000_000), "decimals": 2})

    supplier_name = Column(String, ForeignKey("company.name"))
    supplier = relationship(
        Company, foreign_keys=[supplier_name],
        info={"label": "поставщик", "choices": lambda session: Company.filter(session)}
    )

    man_name = Column(String, ForeignKey("company.name"))
    man = relationship(
        Company, foreign_keys=[man_name],
        info={"choices": lambda session: Company.filter(session), "label": "производитель"}
    )
    category = Column(String, info={"label": "категория"})
    discount = Column(Float, default=0, info={"label": "скидка", "range": (0, 100), "decimals": 2})
    quantity = Column(Integer, info={"label": "количество", "range": (0, 1_000_000)})
    description = Column(String, info={"label": "описание"})
    photo = Column(String, nullable=True, info={"label": "фото"})

    verbose_name = "товара"
    exclude_columns = {"supplier_name", "man_name"}

    @property
    def fixed_price(self):
        return round(self.price * (1 - self.discount / 100), 2)

    @property
    def valid_photo(self):
        if self.photo and os.path.exists(self.photo):
            return self.photo
        return str(ROOT / 'import/picture.png')

    def __str__(self):
        return f"{self.name} произведено {self.man_name}"


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    role = Column(String, info={"label": "роль"})
    fio = Column(String, info={"label": "ФИО"})
    login = Column(String, unique=True, info={"label": "логин"})
    password = Column(String, info={"label": "пароль"})
    is_active = Column(Boolean, info={"label": "активен да/нет"}, default=True)

    def __str__(self):
        return self.fio


    verbose_name = "пользователя"
    exclude_columns = {"id"}


class Address(Base):
    __tablename__ = "address"
    id = Column(Integer, primary_key=True)
    description = Column(String, info={"label": "описание"})

    verbose_name = "адреса"
    exclude_columns = {"id"}

    def __str__(self):
        out, desc = [], self.description.split()
        while sum(map(len, out)) < 30 and desc:
            out.append(desc.pop(0))
        return " ".join(out) + ("..." if desc else "")


class OrderItem(Base):
    __tablename__ = "order_item"
    id = Column(Integer, primary_key=True)
    order_articul = Column(Integer, ForeignKey("order.articul"), info={"label": "артикул заказа"})
    product_articul = Column(String, ForeignKey("product.articul"), info={"label": "артикул товара"})
    quantity = Column(Integer, info={"label": "кол-во"})
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product")

    verbose_name = "товар заказа"
    exclude_columns = {"id"}

    __table_args__ = (UniqueConstraint("order_articul", "product_articul"),)

    def __str__(self):
        return f"Товар {self.product}, {self.quantity} {self.product.measure_type}"


class Order(Base):
    __tablename__ = "order"
    articul = Column(Integer, primary_key=True, info={"label": "артикул"})
    created_at = Column(DateTime, nullable=True, info={"label": "дата создания"})
    deliver_at = Column(DateTime, nullable=True, info={"label": "дата доставки"})
    address_id = Column(Integer, ForeignKey("address.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    address = relationship("Address", info={"label": "адрес"})
    user = relationship("User", info={"label": "пользователь"})
    code = Column(Integer, info={"label": "код"})
    status = Column(String, info={"label": "статус", "choices": ("Новый", "Старый")})

    verbose_name = "заказа"
    exclude_columns = {"address_id", "user_id"}

    order_items = relationship(
        OrderItem, back_populates="order",
        cascade="all, delete", info={"label": "товары заказа"}
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
