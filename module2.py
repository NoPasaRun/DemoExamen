import sys
from typing import Optional

from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap, Qt, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLabel,
    QScrollArea,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QFrame
)
from sqlalchemy.orm import joinedload

from module1 import User, Session, Product
from module3 import BackwardMixin, MainWindow, FilterProductWidget

user: Optional[User] = None


class BaseWindow(BackwardMixin):
    def __init__(self, title: str):
        self.header = QHBoxLayout(header := QWidget())
        super().__init__()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setFixedSize(1280, 720)

        self.layout = QVBoxLayout(central_widget)
        self.top_layout = QHBoxLayout(top_layout := QWidget())

        self.top_layout.addWidget(QLabel(
            f"<h1>{title}</h1>"
        ), alignment=Qt.AlignmentFlag.AlignHCenter)

        self.layout.addWidget(top_layout)
        self.layout.addWidget(header)

        if user is not None:
            self.top_layout.addWidget(QLabel(user.fio))

        self.setWindowTitle(title)
        self.setWindowIcon(QIcon("./import/icon.png"))


class AuthWindow(BaseWindow):
    def __init__(self):
        super().__init__("Войти")
        layout = QVBoxLayout(form := QWidget())

        self.loginInput = QLineEdit()
        self.loginInput.setPlaceholderText("Ввести логин")
        self.passwordInput = QLineEdit()
        self.passwordInput.setPlaceholderText("Ввести пароль")

        self.authBtn = QPushButton("Войти")
        self.guestBtn = QPushButton("Зайти как гость")
        self.authBtn.clicked.connect(self.auth)
        self.guestBtn.clicked.connect(self.close)

        layout.addWidget(self.loginInput)
        layout.addWidget(self.passwordInput)
        layout.addWidget(self.authBtn)
        layout.addWidget(self.guestBtn)

        self.layout.addWidget(form, alignment=Qt.AlignmentFlag.AlignHCenter)

    def close(self):
        MainWindow.set(ProductsWindow())
        MainWindow().show()
        self.hide()

    def auth(self):
        global user

        login = self.loginInput.text()
        password = self.passwordInput.text()

        with Session() as session:
            user = session.query(User).filter_by(login=login, password=password).first()
            if not user:
                return QMessageBox.information(
                    self,
                    "Ошибка",
                    "Логин иои пароль не верный!"
                )
            self.close()


class QProductWidget(QFrame):
    def __init__(self, product: Product):
        super().__init__()
        self.mainLayout = QHBoxLayout()

        image = QPixmap(f"./import/{product.photo or 'picture.png'}")
        self.imageLabel = QLabel()
        self.imageLabel.setPixmap(image.scaled(QSize(100, 100)))
        self.imageLabel.setStyleSheet("width: 100px;")
        self.mainLayout.addWidget(self.imageLabel)
        self.mainLayout.addStretch()

        self.layout = QVBoxLayout()
        self.nameLabel = QLabel(f"{product.category} | {product.name}")
        self.nameLabel.setStyleSheet('font-weight: bold;')
        self.descriptionLabel = QLabel(f"Описание: {product.description}")
        self.manufacturerLabel = QLabel(f"Производитель: {product.manufacturer.name}")
        self.supplierLabel = QLabel(f"Поставщик: {product.supplier.name}")
        if not product.discount:
            self.priceLabel = QLabel(f"Цена: {product.price} руб.")
        else:
            self.priceLabel = QLabel(
                f"Цена: <s style='color: red'>{product.price}</s> "
                f"<span style='color: black'>{product.fixed_price}</span> руб."
            )
        self.measureLabel = QLabel(f"Единица измерения: {product.measure_type}")
        self.quantityLabel = QLabel(f"Количество на складе: {product.quantity}")
        if not product.quantity:
            self.quantityLabel.setStyleSheet('background-color: #4444AA;')
        for label in [
            self.nameLabel, self.descriptionLabel, self.manufacturerLabel,
            self.supplierLabel, self.priceLabel, self.measureLabel, self.quantityLabel
        ]:
            self.layout.addWidget(label)
        self.mainLayout.addLayout(self.layout)
        self.mainLayout.addStretch()

        if product.discount:
            self.discountLabel = QLabel(f"Действующая скидка: {product.discount}%")
            self.mainLayout.addWidget(self.discountLabel)

        self.setLayout(self.mainLayout)
        self.setObjectName("ProductCard")
        if product.discount > 15:
            self.setStyleSheet("""#ProductCard {background:#2E8B57}""")


class ProductsWindow(BaseWindow):

    def refresh(self, filters: tuple = (), order_by: tuple = ()):
        productContent = QWidget()
        scrollLayout = QVBoxLayout(productContent)

        with Session() as session:
            products = session.query(Product).where(
                *filters
            ).options(
                joinedload(Product.manufacturer),
                joinedload(Product.supplier)
            ).order_by(*order_by).all()

        for product in products:
            scrollLayout.addWidget(QProductWidget(product))
        self.scroll.setWidget(productContent)

    def __init__(self):
        super().__init__("Список товаров")

        self.view = QVBoxLayout()

        if user is not None and user.role in ["Менеджер", "Администратор"]:
            self.view.addWidget(FilterProductWidget(self.refresh))

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.logoutBtn = QPushButton("Выйти")
        self.logoutBtn.clicked.connect(self.logout)

        self.view.addWidget(self.scroll)

        self.header.addWidget(self.logoutBtn)
        self.layout.addLayout(self.view)
        self.refresh()

    def logout(self):
        global user
        user, _ = None, MainWindow.set(None)
        MainWindow.set(AuthWindow())
        MainWindow().show()
        self.hide()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow.set(AuthWindow())
    MainWindow().show()
    sys.exit(app.exec())
