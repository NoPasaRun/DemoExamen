from typing import Optional, Callable

from PySide6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QFrame,
    QVBoxLayout,
    QLineEdit,
    QComboBox
)
from sqlalchemy import func, or_

from module1 import Company, Session, Product


class MainWindow:

    __instance: QMainWindow = None

    def __new__(cls) -> Optional[QMainWindow]:
        return cls.__instance

    @classmethod
    def set(cls, window: QMainWindow = None):
        cls.__instance = window


class BackwardMixin(QMainWindow):

    header = None

    def __init__(self):
        super().__init__()
        current = MainWindow()
        if current is not None and self.header is not None:
            self.header.addWidget(btn := QPushButton('назад'))
            btn.clicked.connect(self.backwards)
        self.__prev, _ = current, MainWindow.set(self)

    def backwards(self):
        if self.__prev is None:
            return
        self.__prev.show()
        MainWindow.set(self.__prev)
        super().hide()


class FilterProductWidget(QFrame):
    def __init__(self, callback: Callable):
        super().__init__()
        self.layout = QVBoxLayout()
        refresh = lambda *_: callback(self.filters, self.order_by)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск")
        self.search.textEdited.connect(refresh)
        self.layout.addWidget(self.search)

        self.list = QComboBox()
        with Session() as session:
            suppliers = session.query(Company).all()
            self.mapper = {i: val.id for i, val in enumerate(suppliers, 1)}
            self.list.addItems(["Все поставщики", *[val.name for val in suppliers]])
        self.list.currentIndexChanged.connect(refresh)
        self.layout.addWidget(self.list)

        self.sorting = QComboBox()
        self.mapper2 = {1: False, 2: True}
        self.sorting.addItems(
            ['Нет сортировки по кол-ву на складе', 'По убыванию', 'По возрастанию']
        )
        self.sorting.currentIndexChanged.connect(refresh)
        self.layout.addWidget(self.sorting)
        self.setLayout(self.layout)

    @property
    def order_by(self):
        is_asc = self.mapper2.get(self.sorting.currentIndex())
        return (Product.quantity if is_asc else Product.quantity.desc(),)

    @property
    def filters(self):
        f = []
        if q := self.search.text().lower():
            exp = func.lower(Product.articul).like(q + "%")
            for attr in ["name", "category", "description"]:
                exp = or_(
                    exp,
                    func.lower(getattr(Product, attr)).like(q + "%")
                )
            f.append(exp)
        if supplier_id := self.mapper.get(self.list.currentIndex()):
            f.append(Product.supplier_id == supplier_id)
        return tuple(f)
