import sys

from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLabel,
    QScrollArea,
    QHBoxLayout,
    QLineEdit,
    QFrame
)
from sqlalchemy.orm import joinedload

from module1 import User, Session, Product, Company
from module2 import Global, msg
from module3 import (
    FilterProductWidget,
    BackwardMixin,
    ProductForm,
    delete_product
)
from module4 import OrderWindow


class AuthWindow(BackwardMixin):

    def __init__(self):
        super().__init__("Войти")
        self.body.addLayout(form := QVBoxLayout())

        self.loginInput = QLineEdit()
        self.loginInput.setPlaceholderText("Ввести логин")
        self.passwordInput = QLineEdit()
        self.passwordInput.setPlaceholderText("Ввести пароль")

        authBtn = QPushButton("Войти")
        guestBtn = QPushButton("Зайти как гость")
        authBtn.clicked.connect(self.auth)
        guestBtn.clicked.connect(lambda: self.pass_(User(fio="", role="Гость")))

        form.addWidget(self.loginInput)
        form.addWidget(self.passwordInput)
        form.addStretch()
        form.addWidget(authBtn)
        form.addWidget(guestBtn)

    def pass_(self, user: User):
        Global.user = user
        Global.window = ProductsWindow()
        Global.window.show()
        self.hide()

    def autologin(self):
        self.loginInput.setText("94d5ous@gmail.com")
        self.passwordInput.setText("uzWC67")
        self.auth()

    # Авторизация
    def auth(self):
        login = self.loginInput.text()
        password = self.passwordInput.text()

        with Session() as session:
            user = session.query(User).filter_by(login=login, password=password).first()
            if not user:
                return msg(self, "Логин иои пароль не верный!", "Ошибка")
            return self.pass_(user)


class QProductWidget(QFrame):

    def __init__(self, product: Product):
        super().__init__()
        self.setLayout(container := QHBoxLayout())

        image = QPixmap(product.valid_photo)
        label = QLabel()
        label.setPixmap(image.scaled(QSize(100, 100)))
        container.addWidget(label)

        info = QVBoxLayout()
        info.addWidget(QLabel(f"<b>{product.category} | {product.name}</b>"))
        info.addWidget(QLabel(f"Описание: {product.description}"))
        info.addWidget(QLabel(f"Производитель: {product.man_name}"))
        info.addWidget(QLabel(f"Поставщик: {product.supplier_name}"))

        if not product.discount:
            info.addWidget(QLabel(f"Цена: {product.price} руб."))
        else:
            info.addWidget(QLabel(
                f"Цена: <s style='color: red'>{product.price}</s> "
                f"<span style='color: black'>{product.fixed_price}</span> руб."
            ))

        info.addWidget(
            q := QLabel(f"Количество на складе: {product.quantity} {product.measure_type}")
        )
        if not product.quantity:
            q.setStyleSheet('background-color: #4444AA;')

        container.addLayout(info)
        container.addStretch()
        if product.discount:
            container.addWidget(QLabel(f"Действующая скидка: {product.discount}%"))

        if Global.user.role == "Администратор":
            container.addStretch()
            container.addLayout(buttons := QVBoxLayout())

            buttons.addWidget(delete_btn := QPushButton("Удалить"))
            delete_btn.clicked.connect(self.delete(product))

            buttons.addWidget(edit_btn := QPushButton("Редактировать"))
            edit_btn.clicked.connect(self.open_edit_form(product))

        self.setObjectName("ProductCard")
        if product.discount > 15:
            self.setStyleSheet("""#ProductCard {background:#2E8B57}""")

    def delete(self, product: Product):
        def inner():
            if delete_product(product):
                self.setParent(None)
                self.deleteLater()
        return inner

    @staticmethod
    def open_edit_form(product: Product):
        def inner():
            prevWindow = Global.window
            Global.window = ProductForm("Редактирование товара", product=product)
            Global.window.show()
            prevWindow.hide()
        return inner


class ProductsWindow(BackwardMixin):

    def refresh(self, filters: tuple = (), order_by: tuple = ()):
        product_content = QWidget()
        scrollLayout = QVBoxLayout(product_content)

        with Session() as session:
            products = session.query(Product).where(
                *filters
            ).join(
                Company, Product.man_name == Company.name
            ).options(
                joinedload(Product.man),
                joinedload(Product.supplier)
            ).order_by(*order_by).all()

        for product in products:
            scrollLayout.addWidget(QProductWidget(product))
        self.scroll.setWidget(product_content)

    def __init__(self):
        super().__init__("Список товаров")

        self.body.addLayout(main := QVBoxLayout())
        if Global.user.role in ["Менеджер", "Администратор"]:
            main.addWidget(FilterProductWidget(self.refresh))
            self.header.insertWidget(0, btn := QPushButton("Заказы"))
            btn.clicked.connect(self.open_order_page)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        main.addWidget(self.scroll)

        self.header.insertWidget(0, logout_btn := QPushButton("Выйти"))
        logout_btn.clicked.connect(self.logout)

        if Global.user.role == "Администратор":
            main.addWidget(create_btn := QPushButton("Создать новый товар"))
            create_btn.clicked.connect(self.open_create_form)

    def open_order_page(self):
        Global.window = OrderWindow("Список заказов")
        Global.window.show()
        self.hide()

    def open_create_form(self):
        Global.window = ProductForm("Создание товара", product=None)
        Global.window.show()
        self.hide()

    def show(self):
        self.refresh()
        super().show()

    def logout(self):
        Global.user, Global.window = None, None
        Global.window = AuthWindow()
        Global.window.show()
        self.hide()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    Global.window = a = AuthWindow()
    Global.window.show()
    a.autologin()
    sys.exit(app.exec())
