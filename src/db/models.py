import base64
import hashlib
import random
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Integer, Column, ForeignKey, UniqueConstraint, text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from db.connection import engine, create_session
from settings import app_settings
from settings import app_settings


class RoleTypeEnum(StrEnum):
    admin = "админ"
    manager = "менеджер"
    simple = "пользователь"
    guest = "гость"

    @classmethod
    def str_values(cls):
        return ', '.join(f"'{e.name}'" for e in cls)


class User(Base):
    username: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str] = mapped_column()
    orders = relationship("Order", back_populates="user", uselist=True)
    role_type: Mapped[str] = mapped_column(default="simle")

    exclude = {"password_hash", "id", "role_type"}
    extra = {"encrypt_user_id", "role"}

    __table_args__ = (
        CheckConstraint(
            f"role_type in ({RoleTypeEnum.str_values()})"
        ),
    )

    @property
    def role(self):
        return getattr(RoleTypeEnum, self.role_type).value

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


class Category(Base):
    title: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str] = mapped_column()

    products = relationship("Product", back_populates="category", uselist=True)


class MeasureTypeEnum(StrEnum):
    unit = "штука"
    pack = "упаковка"
    container = "партия"

    @classmethod
    def str_values(cls):
        return ', '.join(f"'{e.name}'" for e in cls)


class Product(Base):

    exclude = {"measure_type"}
    extra = {"measure", "category", "corrected_price"}

    order_products = relationship("OrderProduct", back_populates="product", uselist=True)
    price: Mapped[float] = mapped_column()
    quantity: Mapped[int] = mapped_column()
    title: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()
    image_url: Mapped[str] = mapped_column(nullable=True)
    supplier: Mapped[str] = mapped_column()
    producer: Mapped[str] = mapped_column()
    measure_type: Mapped[str] = mapped_column()
    discount: Mapped[float] = mapped_column(default=0)

    category = relationship(Category, back_populates="products")
    category_id: Mapped[int] = Column(Integer, ForeignKey("category.id"))

    @property
    def corrected_price(self):
        if self.discount > 0:
            return round(self.price * (100 - self.discount) / 100, 2)
        return None

    @property
    def measure(self):
        return getattr(MeasureTypeEnum, self.measure_type).value

    __table_args__ = (
        CheckConstraint(
            f"measure_type in ({MeasureTypeEnum.str_values()})"
        ),
    )


class OrderProduct(Base):

    order = relationship("Order", back_populates="order_products")
    product = relationship(Product, back_populates="order_products")

    product_id: Mapped[int] = Column(Integer, ForeignKey("product.id"))
    order_id: Mapped[int] = Column(Integer, ForeignKey("order.id"))
    quantity: Mapped[int] = mapped_column()

    __table_args__ = (
        UniqueConstraint(product_id, order_id),
    )


class Order(Base):

    extra = {"order_products"}

    user = relationship(User, back_populates="orders")
    order_products = relationship(OrderProduct, back_populates="order")
    address: Mapped[str] = mapped_column()
    user_id: Mapped[int] = Column(Integer, ForeignKey("user.id"))


if __name__ == '__main__':
    with engine.connect() as conn:
        for table in Base.metadata.tables:
            conn.execute(text(f"DROP TABLE IF EXISTS \"{table}\" CASCADE"))
        conn.commit()
    Base.metadata.create_all(engine)

    with create_session() as session:
        user = User(username="user", role_type="simple")
        user.set_password("user")
        user.save(session)

        categories = [
            Category(
                title=f"Title {i}",
                description=f"Description {i}"
            )
            for i in range(1, 6)
        ]
        session.add_all(categories)

        products = [
            Product(
                title=f"Title {i}",
                description=f"Description {i}",
                price=random.randint(1000, 10000),
                quantity=random.randint(1, 10),
                supplier=f"Supplier {i}",
                producer=f"Producer {i}",
                measure_type="pack",
                category=random.choice(categories),
                image_url=f"{app_settings.root}/assets/images/image{random.randint(1, 3)}.webp",
                discount=random.choice([None, round(random.uniform(15, 30), random.randint(0, 2))])
            )
            for i in range(1, 11)
        ]
        session.add_all(products)
