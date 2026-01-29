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


# Создание объектов подключения к БД; В format аргументами передаете данные для подключения:
# имя_пользователя, пароль_пользователя, адрес_бд, порт_бд, имя_бд
engine = create_engine("postgresql+psycopg2://{}:{}@{}:{}/{}".format(
    "postgres", "postgres", "localhost", "5432", "demo"
))
Session = sessionmaker(bind=engine)
ROOT = Path(__file__).parent.resolve()


def get_data(filepath: str) -> List[List[Any]]:
    """
    Вспомогательная функция которая читает данные из xlsx файла,
    проходится с первой по последнюю строку (НЕ С 0-ой, ПОТОМУ ЧТО НУЛЕВАЯ
    СТРОКА ЭТО НАЗВАНИЯ КОЛОНОК) и создает 2-ую матрицу данных,
    где каждая строка этой матрицы представляет соответствующую строку в БД

    :param filepath: относительный путь до загружаемого файла
    :return: Список из списков значений для загрузки в БД
    """
    wb = openpyxl.load_workbook(filepath)
    sheet = wb.active
    return [
        [val.value for val in row]
        for row in list(sheet.iter_rows())[1:]
        if row[0].value
    ]


class Base(DeclarativeBase):
    """
    Абстрактный класс, от которого ОБЯЗАТЕЛЬНО надо наследоваться
    чтобы провести "связь" между реальной таблицей в БД и классом-эквивалентом
    в вашем коде
    """
    __abstract__ = True


class Company(Base):
    __tablename__ = "company"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


class Product(Base):
    __tablename__ = "product"
    articul = Column(String, primary_key=True)
    name = Column(String)
    measure_type = Column(String)
    price = Column(Float)

    """
    Связь FK на примере поставщика. Чтобы сделать связь одной таблице
    с другой (к примеру One2Many) мы создаем соответствующую колонку
    которая будет ссылаться на таблицу в родительской (supplier_id->company.id)
    
    Чтобы потом не городить join-ы и доп select-ы, и спокойно доставать данные
    из связной таблицы мы создаем объект relationship, в которой поместиться
    в нашем случае объект Company со всеми его полями.
    
    К примеру мы сможем вызвать: self.supplier.name (имя компании поставщика)
    
    Вопрос: зачем указывать foreign_keys в relationship если мы и так уже указали 
    FK в supplier_id?
    
    Ответ: если в нашей таблице всего одна FK связь с другой таблицей, то незачем.
    Но у нас 2 связи. supplier_id-company.id и manufacturer_id->company.id. relationship
    в таком случае автоматически не поймет что куда загружать, поэтому ему нужно явно
    указать по какому ключу искать запись. Если бы у нас manufacturer_id ссылался не на Company
    а на новую таблицу (которой у нас нет ввиду ненадобности) Manufacturer то такой
    финт НЕ БЫЛ ошибкой, но был бы БЕСПОЛЕЗНЫМ.
    """

    supplier_id = Column(Integer, ForeignKey("company.id"))
    supplier = relationship(Company, foreign_keys=[supplier_id])

    manufacturer_id = Column(Integer, ForeignKey("company.id"))
    manufacturer = relationship(Company, foreign_keys=[manufacturer_id])
    category = Column(String)
    discount = Column(Float, default=0)
    quantity = Column(Integer)
    description = Column(String)
    photo = Column(String, nullable=True)

    # @property позволяет к методу обращаться как к атрибуту
    # Пример: self.fixed_price
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
    fio = Column(String)
    login = Column(String, unique=True)
    password = Column(String)


class Address(Base):
    __tablename__ = "address"
    id = Column(Integer, primary_key=True)
    description = Column(String)


class OrderItem(Base):
    __tablename__ = "order_item"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("order.id"))
    quantity = Column(Integer)
    articul = Column(String, ForeignKey("product.articul"))
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product")

    # Создание ограничений ключа, в данном случае создание
    # ограничения уникальности на комбинацию 2 полей
    __table_args__ = (UniqueConstraint("order_id", "articul"),)


class Order(Base):
    __tablename__ = "order"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, nullable=True)
    deliver_at = Column(DateTime, nullable=True)
    address_id = Column(Integer, ForeignKey("address.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    address = relationship("Address")
    user = relationship("User")
    code = Column(Integer)
    status = Column(String)

    order_items = relationship(OrderItem, back_populates="order", cascade="all, delete")

    @property
    def articuls(self):
        return ", ".join(oi.product.articul for oi in self.order_items)


def main():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    data = get_data("import/Tovar.xlsx")

    # Казалось бы, очень страшная строчка, ой все, не буду программистом, буду
    # проституткой. ВНИМАНИЕ. Все просто, следите за руками. set как вы знаете
    # из английского означает множество. А мы и приводим столбец компаний
    # (4 и 5) по индексу соответственно к множеству УНИКАЛЬНЫХ значений
    # ведь нам же не нужны дубликаты в таблице company, верно?

    # Недоумение может составить еще эта запись [row[4] for row in data]
    # Тогда вам следует почитать про list comprehensions. Клянусь это
    # не сложно. Вот ресурс: https://metanit.com/python/tutorial/3.6.php

    # | - это оператор сложения двух множеств, тк у нас нет разделения на таблицы
    # поставщика и производителя (единая таблица Company) и в конце мы все приводим к списку
    companies_names = list(set([row[4] for row in data]) | set([row[5] for row in data]))

    with Session() as session:
        companies = [Company(name=name) for name in companies_names]
        session.bulk_save_objects(companies, return_defaults=True)
        session.commit()

    # Мы создаем вспомогательный словарь, чтобы постоянно не дергать БД в поисках
    # компании для товаров, тк связь у товара с производителем и поставщиком не по
    # имени, а по идентификатору, а в сырых данных таблице у нас нет идентификатора,
    # но зато мы его сгенерировали и в данном словаре соотнесли с именем компании
    companies = {val.name: val.id for val in companies}

    # Из списка товаров словарь делать необязательно тк идентификатор товара это артикул
    # а артикул уже есть в сырах данных xlsx
    with Session() as session:
        products = [
            Product(
                articul=row[0],
                name=row[1],
                measure_type=row[2],
                price=row[3],
                supplier_id=companies[row[4]],
                manufacturer_id=companies[row[5]],
                category=row[6],
                discount=row[7],
                quantity=row[8],
                description=row[9],
                photo=(row[10] and str(ROOT / 'import' / row[10])) or None
            )
            for row in data
        ]
        # Просто сохраняем и все
        session.bulk_save_objects(products)
        session.commit()

    # Создание и маппинг пользователей
    data = get_data("import/user_import.xlsx")
    with Session() as session:
        users = [
            User(
                role=row[0],
                fio=row[1],
                login=row[2],
                password=row[3]
            )
            for row in data
        ]
        session.bulk_save_objects(users, return_defaults=True)
        session.commit()
    users = {val.fio: val.id for val in users}

    # С заказами как и с товарами нам повезло и адреса пунктов выдачи
    # в xlsx с заказами там пронумерованы идентификаторами.
    # Самое главное это при создании адресов присвоить им
    # последовательные идентификаторы от 1 до N
    data = get_data("import/Пункты выдачи_import.xlsx")
    with Session() as session:
        # Функция enumerate возвращает список кортежей по типу:
        # [(j, value1), (j + 1, value2), (j + 2, value3), ..., (j + n, valueN)]
        # Где j - это число стартового индекса. В нашем случае с 1 и до n
        addresses = [Address(id=id_, description=row[0]) for id_, row in enumerate(data, 1)]
        session.bulk_save_objects(addresses, return_defaults=True)
        session.commit()

    # Заготовка данных товаров определенного заказа
    # Тк у нас УЖЕ есть идентификатор заказа, данные мы можем
    # заготовить заранее, НО НЕ СОЗДАВАТЬ. Если мы попробуем
    # создать OrderItem до Order, то у нас вылетит IntegrityError
    # те ошибка целостности данных
    data = get_data("import/Заказ_import.xlsx")
    # Да, это - zip(row[1].split(", ")[::2], row[1].split(", ")[1::2])
    # ужас однозначно, собираюсь ли я его вырезать? Нет, потому что это по своему
    # прекрасно. Но в качестве альтернативы я напишу более подробную версию то как
    # обработать эту строку "Артикул, кол-во, Артикул, кол-во"
    order_items = [
        OrderItem(
            order_id=row[0],
            articul=row_data[0],
            quantity=row_data[1]
        )
        for row in data
        for row_data in zip(row[1].split(", ")[::2], row[1].split(", ")[1::2])
    ]
    """
    Alt version:
    order_items = []
    for row in data:
        art1, quant1, art2, quant2 = row[1].split(', ')
        order_items.append(OrderItem(order_id=row[0], articul=art1, quantity=quant1))
        order_items.append(OrderItem(order_id=row[0], articul=art2, quantity=quant2))
    
    Ну как-то так. split создает из строки список, вырезая переданный делитель.
    Тк у нас во всем столбце по три запятые с пробелом то и элементов получится всегда 4.
    Этот список из четырех элементов мы распаковываем в 4 переменные.
    """

    with Session() as session:
        orders = [
            Order(
                id=row[0],
                # Можете сказать, что это костыль и будете правы. Но нигде в ТЗ не сказано
                # как обрабатывать ущербность данных и я сделал так как счел нужным
                created_at=row[2] if isinstance(row[2], datetime) else datetime(year=2025, month=3, day=2),
                deliver_at=row[3],
                address_id=row[4],
                user_id=users[row[5]],
                code=row[6],
                # Я просто в #### с того насколько это убого. Вот им делать нечего как пробелы
                # перед текстом ставить. Тьфу, ####.
                status=row[7].strip()
            )
            for row in data
        ]
        session.bulk_save_objects(orders)
        # Уже после создания товаров можно и сохранить товары заказов
        session.bulk_save_objects(order_items)
        session.commit()


if __name__ == '__main__':
    main()
