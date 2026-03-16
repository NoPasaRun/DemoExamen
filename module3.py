import os
from functools import reduce
from typing import Callable, Optional

from PySide6.QtCore import QLocale
from PySide6.QtGui import QDoubleValidator, QIntValidator, QPixmap, Qt
from PySide6.QtWidgets import (
    QPushButton,
    QFrame,
    QVBoxLayout,
    QLineEdit,
    QComboBox,
    QWidget,
    QFileDialog,
    QLabel, QMessageBox
)
from sqlalchemy import func, or_
from module1 import Company, Session, Product, ROOT, OrderItem
from module2 import Global, BaseWindow, msg


class BackwardMixin(BaseWindow):

    def __init__(self, *args):
        super().__init__(*args)
        current = Global.window
        if current is not None:
            self.header.insertWidget(0, btn := QPushButton('назад'))
            btn.clicked.connect(self.backwards)
        self.__prev, Global.window = current, self

    def backwards(self):
        if self.__prev is None:
            return
        self.__prev.show()
        Global.window = self.__prev
        self.hide()


class FilterProductWidget(QFrame):

    def __init__(self, callback: Callable):
        super().__init__()
        form = QVBoxLayout(self)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск")
        self.search.textEdited.connect(self.refresh(callback))
        form.addWidget(self.search)

        self.list = QComboBox()
        with Session() as session:
            suppliers = session.query(Company).all()
            self.list.addItems(["Все поставщики", *[val.name for val in suppliers]])
        self.list.currentTextChanged.connect(self.refresh(callback))
        form.addWidget(self.list)

        self.sorting = QComboBox()
        self.sorting.addItems(
            ['Нет сортировки по кол-ву на складе', 'По убыванию', 'По возрастанию']
        )
        self.sorting.currentTextChanged.connect(self.refresh(callback))
        form.addWidget(self.sorting)

    def refresh(self, f: Callable):
        def inner():
            return f(self.filters, self.order_by)
        return inner

    @property
    def order_by(self):
        if self.sorting.currentIndex() == 2:
            return (Product.quantity,)
        elif self.sorting.currentIndex() == 1:
            return (Product.quantity.desc(),)
        return tuple()

    @property
    def filters(self):
        f = []
        if q := self.search.text().lower():
            f.append(reduce(
                lambda exp, attr: or_(exp, func.lower(getattr(Product, attr)).like(f"%{q}%")),
                ["name", "category", "description", "man_name"],
                func.lower(Product.articul).like(f"%{q}%")
            ))
        if self.list.currentIndex():
            f.append(Product.supplier_name == self.list.currentText())
        return tuple(f)


class ImageUploader(QWidget):

    def __init__(self, filepath: str):
        super().__init__()
        form = QVBoxLayout(self)
        self.load: Optional[QPixmap] = None

        self.label = QLabel()
        self.label.setFixedSize(150, 150)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("border: 1px dashed gray;")
        self.set_pixmap(QPixmap(filepath))
        form.addWidget(self.label)

        form.addWidget(upload_btn := QPushButton("Выбрать фото"))
        upload_btn.clicked.connect(self.load_image)

    def set_pixmap(self, pixmap: QPixmap):
        self.label.setPixmap(pixmap.scaled(
            self.label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

    def load_image(self):
        new_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение",
            "", "Images (*.png *.jpg *.jpeg)"
        )

        if new_path:
            pixmap = QPixmap(new_path)
            if pixmap.width() * pixmap.height() > 6_000_000:
                return msg(
                    self,"Изображение должно быть не больше формата 300x200",
                    "Ошибка",
                )
            self.load = pixmap
            self.set_pixmap(self.load)
        return None


def delete_product(product: Product):
    prev_filepath = product.photo
    with Session() as session:
        if session.query(OrderItem).filter_by(product_articul=product.articul).first():
            msg(
                None, "Нельзя удалить товар, если он в заказе", "Ошибка"
            )
            return False
        session.delete(product)
        session.commit()
    if prev_filepath is not None and os.path.exists(prev_filepath):
        os.remove(prev_filepath)
    msg(None, "Товар удален из БД", "Успешно")
    return True


class ProductForm(BackwardMixin):

    def __init__(self, *args, product: Product = None):
        super().__init__(*args)
        self.body.addLayout(form := QVBoxLayout())
        self.product = product or Product()
        exclude = {"photo", "supplier_name", "man_name"}
        if product is not None:
            exclude |= {"articul"}
        self.base_columns = Product.get_fields(exclude)

        for label, attr in self.base_columns:
            product_value = getattr(self.product, attr)
            setattr(
                self, attr, w := QLineEdit(
                    str(product_value) if product_value is not None else None
                )
            )
            w.setPlaceholderText(f"Введите {label}")
            form.addWidget(w)

        v1 = QDoubleValidator(top=0.0, bottom=1000000.0, decimals=2)
        v1.setLocale(QLocale("C"))
        getattr(self, "price").setValidator(v1)

        v2 = QDoubleValidator(bottom=0.0, top=100.0, decimals=2)
        v2.setLocale(QLocale("C"))
        getattr(self, "discount").setValidator(v2)
        getattr(self, "quantity").setValidator(QIntValidator(bottom=0))

        self.supplier_list = QComboBox()
        self.man_list = QComboBox()
        with Session() as session:
            companies = session.query(Company).all()
            names = ["Не выбрано", *[val.name for val in companies]]
            self.supplier_list.addItems(names)
            self.man_list.addItems(names)

        self.supplier_list.setCurrentText(
            product and self.product.supplier_name or 'Выберите поставщика'
        )
        self.man_list.setCurrentText(
            product and self.product.man_name or 'Выберите производителя'
        )
        form.addWidget(self.supplier_list)
        form.addWidget(self.man_list)
        self.photo = ImageUploader(self.product.valid_photo)
        form.addWidget(self.photo)

        form.addWidget(save_btn := QPushButton("Сохранить"))
        save_btn.clicked.connect(self.save)

    def ask(self):
        reply = QMessageBox.question(
            self,
            'Подтверждение',
            "Вы уверены, что хотите сохранить данные?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return False
        return True

    @property
    def valid_id(self):
        if hasattr(self, 'articul'):
            art = self.articul.text()
            with Session() as session:
                if session.query(Product).filter_by(articul=art).first():
                    msg(
                        self, "Товар с таким артикулом уже имеется", "Ошибка"
                    )
                    return None
        else:
            art = self.product.articul
        return art

    def get_data(self):
        if not (id_ := self.valid_id):
            msg(
                self, "Введите артикул", "Ошибка"
            )
            return None
        return {
           col: getattr(self, col).text()
           for _, col in self.base_columns
        } | {
           "photo": str(ROOT / 'import' / (id_ + '.jpg')) if self.photo.load else self.product.photo,
           "man_name": self.man_list.currentText() if self.man_list.currentIndex() else None,
           "supplier_name": self.supplier_list.currentText() if self.supplier_list.currentIndex() else None,
        }

    def null_check(self, data: dict):
        other_columns = [("производитель", "man_name"), ("поставщик", "supplier_name")]
        null_columns = [
            '  ' + label for label, attr in self.base_columns + other_columns
            if not data[attr]
        ]
        if null_columns:
            QMessageBox.critical(
                self, "Ошибка", f"Вы не ввели:\n{'\n'.join(null_columns)}"
            )
            return None
        return True

    def save(self):
        if not self.ask() or not (data := self.get_data()):
            return None
        if not self.null_check(data):
            return None

        prev_path = self.product.photo
        for key, value in data.items():
            setattr(self.product, key, value)
        with Session() as session:
            session.merge(self.product)
            session.commit()

        if self.photo.load:
            if prev_path and os.path.exists(prev_path):
                os.remove(prev_path)
            self.photo.load.save(self.product.photo)
        return QMessageBox.information(self, "Успешно", "Товар сохранен в БД")
