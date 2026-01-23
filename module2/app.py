import sys

from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap, Qt
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
from module2 import MainWindow
from module3 import (
    FilterProductWidget,
    BackwardMixin,
    ProductForm,
    delete_product
)


# ВНИМАНИЕ! В Layout можно поместить и виджет и layout. Виджету можно назначить layout но нельзя указать виджет.
# Со ScrollArea странная тема. Оно вроде как layout, но в него нельзя поместить N виджетов, ТОЛЬКО ОДИН. Поэтому мы
# делаем схему ScrollArea->Widget->Layout->Список_наших_QProductWidget

# НЕ ОТОБРАЖАТЬ ВИДЖЕТЫ. Вызывать show() СТРОГО на окнах. В BaseWindow, уже стоит центральный виджет, так что
# не нужно его создавать в наследниках BaseWindow (BackwardMixin тоже наследник BaseWindow). Хотите добавить доп
# разметку в окно, дергайте self.layout.addLayout или self.layout.addWidget. sekf.layout - это тело страницы BaseWindow
# а self.header - шапка. Чтобы добавить контент в шапку, дергать те же методы что и у self.layout


class AuthWindow(BackwardMixin):

    """
    Окно авторизации
    """

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

    # Делаем функцию закрытия окна авторизации, где либо устанавливаем глобального пользователя None (Guest Mode)
    # либо не None. Устанавливаем новое окно и закрываем текущее
    def close(self, user: User = None):
        MainWindow.set_user(user)
        # ВНИМАНИЕ! Такой nested синтаксис валиден. Тк set_window возвращает объект окна, который мы и передали,
        # то можно после set_window(...) дергать show

        """
        new_window = ProductsWindow()
        MainWindow.set_window(new_window) # метод возвращает то что мы передали те new_window
        new_window.show()
        
        Так тоже верно, но долго.
        """
        MainWindow.set_window(
            ProductsWindow()
        ).show()
        self.hide()

    # Автологин чтобы постоянно не париться со входом. После завершения экзамена удалите к черту.
    def autologin(self):
        self.loginInput.setText("94d5ous@gmail.com")
        self.passwordInput.setText("uzWC67")
        self.auth()

    # Авторизация
    def auth(self):
        login = self.loginInput.text()
        password = self.passwordInput.text()

        with Session() as session:
            # Поиск по логину и паролю. Если найден - круто, нет - выходим из функции и кидаем message box
            user = session.query(User).filter_by(login=login, password=password).first()
            if not user:
                return QMessageBox.critical(
                    self,
                    "Ошибка",
                    "Логин иои пароль не верный!"
                )
            self.close(user)


class QProductWidget(QFrame):
    """
    Отдельный виджет для разгрузки страницы со списком товаров

    Вопрос: почему QFrame а не QWidget.
    Ответ: QWidget не поддерживает собственную стилизацию те background-color: red на QWidget не будет работать
    (background-color применится только к потомкам), QFrame же норм стилизуется
    """

    def __init__(self, product: Product):
        super().__init__()
        self.mainLayout = QHBoxLayout()

        # QPixmap умная фигня которая загружает картинку по пути. Более того, если пути не существует
        # Ошибки не будет (предупреждение не ошибка). Но нам по ТЗ нельзя чтобы была пустая картинка,
        # поэтому метод/property у product возвращает путь, только если он существует, иначе - заглушку
        image = QPixmap(product.valid_photo)
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

        # Экономим 5-6 строчек кода)
        for label in [
            self.nameLabel, self.descriptionLabel, self.manufacturerLabel,
            self.supplierLabel, self.priceLabel, self.measureLabel, self.quantityLabel
        ]:
            self.layout.addWidget(label)
        self.mainLayout.addLayout(self.layout)

        # ВНИМАНИЕ! addStretch добавляет flexible пространство между блоками те, если будет 1 stretch, то он займет
        # ширина_экрана - ширина_всех_элементов, 2 stretch займут каждый по (ширина_экрана - ширина_всех_элементов) / 2,
        # Таким образом можно ставить блоки равноудалено друг от друга
        self.mainLayout.addStretch()

        if product.discount:
            self.discountLabel = QLabel(f"Действующая скидка: {product.discount}%")
            self.mainLayout.addWidget(self.discountLabel)
            self.mainLayout.addStretch()

        if (user := MainWindow.get_user()) and user.role == "Администратор":
            # Если админ то добавляет кнопки с переходом на страницу редактирования и действием удаления
            # Доп проверку на роль больше нигде не делаем
            self.actionLayout = QVBoxLayout()

            self.deleteBtn = QPushButton("Удалить")
            self.deleteBtn.clicked.connect(self.delete(product))
            self.actionLayout.addWidget(self.deleteBtn)

            self.editBtn = QPushButton("Редактировать")
            self.editBtn.clicked.connect(self.open_edit_form(product))
            self.actionLayout.addWidget(self.editBtn)

            self.mainLayout.addLayout(self.actionLayout)

        self.setLayout(self.mainLayout)
        self.setObjectName("ProductCard")
        if product.discount > 15:
            self.setStyleSheet("""#ProductCard {background:#2E8B57}""")

    def delete(self, product: Product):
        """
        Так как обработчик события вызывается без передачи данных о продукте, то мы используем
        замыкание, чтобы внутрення функция без параметров знала, что удалять. Про замыкания смотреть тут:
        https://metanit.com/python/tutorial/2.19.php

        :param product: удаляемый продукт
        :return: возвращаем функцию-обработчик
        """
        def inner():
            delete_product(product)
            self.setParent(None)
            # В реальном времени удаляем текущий виджет без перерендера страницы
            self.deleteLater()
        return inner

    @staticmethod
    def open_edit_form(product: Product):
        """
        То же самое что и с delete, только открываем страницу редактирования
        :param product:
        :return:
        """
        def inner():
            prevWindow = MainWindow()
            MainWindow.set_window(
                ProductForm("Редактирование товара", product=product)
            ).show()
            prevWindow.hide()
        return inner


# BackwardMixin это уже 3-ий модуль. Для второго достаточно отнаследовать от BaseWindow
class ProductsWindow(BackwardMixin):

    """
    Страница со списком товаров
    """

    def refresh(self, filters: tuple = (), order_by: tuple = ()):
        """
        Устанавливаем ScrollArea новый виджет с обновленным списком
        :param filters: Список фильтров
        :param order_by: Список сортировки (ну на всякий, по факту там один параметр сортировки, но может быть и больше)
        :return:
        """
        productContent = QWidget()
        scrollLayout = QVBoxLayout(productContent)

        with Session() as session:
            products = session.query(Product).where(
                *filters
            ).options(
                # ВНИМАНИЕ! Чтобы объекты связанные по FK подгрузились, нужно передать их в options, через joinedload
                # Если нужно подгрузить, к примеру у manufacturer поле которое тоже FK (у нас его нет, но предпододим,
                # что есть, к примеру industry_id, industry), то мы бы в options передали
                # joinedload(Product.manufacturer).joinedload(Manufacturer.industry)
                joinedload(Product.manufacturer),
                joinedload(Product.supplier)
            ).order_by(*order_by).all()

        for product in products:
            # В список устанавливаем наш кастомный виджет
            scrollLayout.addWidget(QProductWidget(product))
        self.scroll.setWidget(productContent)

    def __init__(self):
        super().__init__("Список товаров")

        self.view = QVBoxLayout()
        user = MainWindow.get_user()

        if user and user.role in ["Менеджер", "Администратор"]:
            # Если менеджер или админ добавляем виджет фильтров (3-ий модуль)
            self.view.addWidget(FilterProductWidget(self.refresh))

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.logoutBtn = QPushButton("Выйти")
        self.logoutBtn.clicked.connect(self.logout)

        self.view.addWidget(self.scroll)
        if user and user.role == "Администратор":
            self.createBtn = QPushButton("Создать новый товар")
            self.createBtn.clicked.connect(self.open_create_form)
            self.view.addWidget(self.createBtn)

        self.header.addWidget(self.logoutBtn)
        self.layout.addLayout(self.view)

    def open_create_form(self):
        MainWindow.set_window(
            ProductForm("Создание товара", product=None)
        ).show()
        self.hide()

    def show(self):
        # ВНИМАНИЕ! Это не кастомный метод. Это переопределение открытия окна. При каждом новом открытии, перезагружаем
        # список
        self.refresh()
        super().show()

    def logout(self):
        """
        Вопрос: Зачем мы сначала устанавливаем текущее окно None а потом устанавливаем окно Авторизации. Почему
        сразу не назначить новым окном - окно Авторизации.

        Ответ: AuthWindow наследуется от BackwardMixin, которое устанавливает предыдущим окном, текущее окно во время
        инициализации. те если бы текущее окно перед AuthWindow.__init__ не было бы None, то у AuthWindow было бы
        предыдущее окно, куда можно было бы вернуться, а это черева то багами, тк вернуться мы можем, но пользователь
        у нас уже None. Поэтому перед инициализацией AuthWindow текущее окно должно быть None, чтобы мы не могли вернуться
        назад.
        :return:
        """
        MainWindow.set_window(None)
        MainWindow.set_user(None)
        MainWindow.set_window(
            AuthWindow()
        ).show()
        self.hide()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow.set_window(
        a := AuthWindow()
    ).show()
    a.autologin()
    sys.exit(app.exec())
