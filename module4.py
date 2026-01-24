from PySide6.QtGui import Qt, QIntValidator
from PySide6.QtWidgets import (
    QFrame,
    QScrollArea,
    QWidget,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QPushButton,
    QMessageBox,
    QLineEdit,
    QComboBox,
    QDateTimeEdit
)
from sqlalchemy.orm import joinedload

from module1 import Session, Order, OrderItem, Product, Address
from module2 import MainWindow
from module3 import BackwardMixin


class OrderWidget(QFrame):
    def __init__(self, order: Order):
        super().__init__()

        self.mainLayout = QHBoxLayout()

        self.info = QVBoxLayout()
        self.info.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.info.addWidget(QLabel(order.articuls))
        self.info.addWidget(QLabel(order.status))
        self.info.addWidget(QLabel(order.address.description))
        self.info.addWidget(QLabel(order.created_at.strftime('%d.%m.%Y %H:%M')))

        self.mainLayout.addLayout(self.info)
        self.mainLayout.addStretch()

        self.mainLayout.addWidget(QLabel(order.deliver_at.strftime('%d.%m.%Y %H:%M')))

        if (user := MainWindow.get_user()) and user.role == "Администратор":
            self.mainLayout.addStretch()
            action_layout = QVBoxLayout()

            action_layout.addWidget(edit_btn := QPushButton("Редактировать"))
            edit_btn.clicked.connect(self.open_edit_order_page(order))
            action_layout.addWidget(delete_btn := QPushButton("Удалить"))
            delete_btn.clicked.connect(self.delete_order(order))

            self.mainLayout.addLayout(action_layout)

        self.setLayout(self.mainLayout)

    def delete_order(self, order: Order):
        def inner():
            with Session() as session:
                session.delete(order)
                session.commit()
            self.setParent(None)
            self.deleteLater()
            QMessageBox.information(self, "Успешно", "Заказ удален из БД")
        return inner

    @staticmethod
    def open_edit_order_page(order: Order):
        def inner():
            current = MainWindow()
            MainWindow.set_window(
                OrderForm("Редактирование заказа", order=order)
            ).show()
            current.hide()
        return inner


class OrderItemWidget(QFrame):
    def __init__(self, order_item: OrderItem = None):
        super().__init__()
        self.order_item = order_item or OrderItem()
        self.mainLayout = QHBoxLayout()
        self.articul = QLineEdit(self.order_item.articul)
        self.articul.setPlaceholderText("Введите артикул товара")
        self.quantity = QLineEdit(order_item and str(self.order_item.quantity))
        self.quantity.setPlaceholderText("Введите кол-во на складе")
        self.quantity.setValidator(QIntValidator())

        self.mainLayout.addWidget(self.articul)
        self.mainLayout.addWidget(self.quantity)
        self.mainLayout.addWidget(delete_btn := QPushButton("Удалить"))
        delete_btn.clicked.connect(self.delete)

        self.setLayout(self.mainLayout)

    def delete(self):
        self.setParent(None)
        self.deleteLater()


class OrderForm(BackwardMixin):
    def __init__(self, *args, order: Order = None):
        super().__init__(*args)
        self.order = order or Order()
        self.form = QVBoxLayout()

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scrollContent = QWidget()
        self.scroll.setWidget(self.scrollContent)

        self.order_items = QVBoxLayout(self.scrollContent)
        for order_item in self.order.order_items:
            self.order_items.addWidget(OrderItemWidget(order_item))

        self.form.addWidget(self.scroll)
        self.form.addWidget(add_btn := QPushButton("Добавить товар"))
        add_btn.clicked.connect(self.add_order_item_widget)

        self.status_list = QComboBox()
        self.status_list.addItems(c := ["Завершен", "Новый"])
        self.status_list.setCurrentIndex(
            self.order.status in c and c.index(self.order.status)
        )
        self.form.addWidget(self.status_list)

        self.address = QLineEdit(order and order.address.description)
        self.address.setPlaceholderText("Введите описание")
        self.form.addWidget(self.address)

        self.created_at = QDateTimeEdit(order and order.created_at)
        self.created_at.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.form.addWidget(self.created_at)

        self.deliver_at = QDateTimeEdit(order and order.deliver_at)
        self.deliver_at.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.form.addWidget(self.deliver_at)

        self.form.addWidget(btn := QPushButton("Сохранить"))
        btn.clicked.connect(self.save)

        self.layout.addLayout(self.form)

    def add_order_item_widget(self):
        self.order_items.addWidget(OrderItemWidget())

    @property
    def order_items_data(self):
        order_item_widgets = filter(lambda t: bool(t), [
            self.order_items.itemAt(i).widget()
            for i in range(self.order_items.count())
        ])
        arts, qs = zip(*[
            (c.articul.text(), c.quantity.text())
            for c in order_item_widgets
        ])
        if len(set(arts)) != len(arts):
            QMessageBox.critical(
                self, "Ошибка", "Артикулы товаров не должны повторятся"
            )
            return None

        if '' in arts or '' in qs:
            QMessageBox.critical(
                self, "Ошибка",
                "Заполните все артикулы и кол-ва на складе, либо удалите поле"
            )
            return None

        with Session() as session:
            if not all([session.query(Product).filter_by(articul=a).first() for a in arts]):
                QMessageBox.critical(
                    self, "Ошибка", "Вы ввели артикулы не существующих товаров"
                )
                return None

        return [OrderItem(articul=a, quantity=int(q)) for a, q in zip(arts, qs)]

    def save(self):
        if not (order_item_data := self.order_items_data):
            return

        self.order.order_items = order_item_data
        self.order.status = self.status_list.currentText()

        ru_names = ["дату доставки", "дату создания", "адрес"]
        null_columns = [
            "  " + ru
            for ru, attr in zip(ru_names, ["deliver_at", "created_at", "address"])
            if not getattr(self, attr).text()
        ]
        if null_columns:
            return QMessageBox.critical(
                self, "Ошибка", "Вы не ввели:\n" + '\n'.join(null_columns)
            )
        self.order.deliver_at = self.deliver_at.dateTime()
        self.order.created_at = self.created_at.dateTime()

        prev_address = self.order.address and self.order.address.description
        if prev_address != (g := self.address.text()):
            self.order.address = Address(description=g)

        with Session() as session:
            session.merge(self.order)
            session.commit()
            session.query(OrderItem).filter_by(
                order_id=None
            ).delete()
            session.commit()
        QMessageBox.information(self, "Успешно", "Данные о заказе сохранены в БД")


class OrderWindow(BackwardMixin):
    def refresh(self):
        order_content = QWidget(self)
        order_layout = QVBoxLayout(order_content)

        with Session() as session:
            orders = session.query(Order).options(
                joinedload(Order.order_items).joinedload(OrderItem.product),
                joinedload(Order.address)
            ).all()
            for order in orders:
                order_layout.addWidget(OrderWidget(order))

        self.scroll.setWidget(order_content)

    def show(self):
        self.refresh()
        super().show()

    def __init__(self, *args):
        super().__init__(*args)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.layout.addWidget(self.scroll)

        if (user := MainWindow.get_user()) and user.role == "Администратор":
            self.layout.addWidget(btn := QPushButton("Создать новый заказ"))
            btn.clicked.connect(self.open_create_form)

    def open_create_form(self):
        MainWindow.set_window(
            OrderForm("Создание заказ")
        ).show()
        self.hide()
