from PySide6.QtCore import QDate
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
from module2 import Global, msg
from module3 import BackwardMixin


class OrderWidget(QFrame):
    def __init__(self, order: Order):
        super().__init__()

        main = QHBoxLayout(self)

        main.addLayout(info := QVBoxLayout())
        info.setAlignment(Qt.AlignmentFlag.AlignLeft)

        info.addWidget(QLabel(f"Артикул: {order.articul}"))
        info.addWidget(QLabel(f"Статус: {order.status}"))
        info.addWidget(QLabel(f"Адрес: {order.address.description}"))
        info.addWidget(QLabel(f"Дата создания: {order.created_at.strftime('%d.%m.%Y %H:%M')}"))

        main.addStretch()
        main.addLayout(other := QHBoxLayout())
        other.addWidget(QLabel(f"Дата доставки: {order.deliver_at.strftime('%d.%m.%Y %H:%M')}"))

        if Global.user.role == "Администратор":
            other.addLayout(buttons := QVBoxLayout())
            buttons.addWidget(edit_btn := QPushButton("Редактировать"))
            edit_btn.clicked.connect(self.open_edit_order_page(order))
            buttons.addWidget(delete_btn := QPushButton("Удалить"))
            delete_btn.clicked.connect(self.delete_order(order))

    def delete_order(self, order: Order):
        def inner():
            with Session() as session:
                session.delete(order)
                session.commit()
            self.setParent(None)
            self.deleteLater()
            msg(self, "Заказ удален из БД", "Успешно")
        return inner

    @staticmethod
    def open_edit_order_page(order: Order):
        def inner():
            current = Global.window
            Global.window = OrderForm("Редактирование заказа", order=order)
            Global.window.show()
            current.hide()
        return inner


class OrderItemWidget(QFrame):
    def __init__(self, order_item: OrderItem = None):
        super().__init__()
        self.order_item = order_item or OrderItem()
        main = QHBoxLayout(self)

        self.product_articul = QLineEdit(self.order_item.product_articul)
        self.product_articul.setPlaceholderText("Введите артикул товара")

        self.quantity = QLineEdit(order_item and str(self.order_item.quantity))
        self.quantity.setPlaceholderText("Введите кол-во на складе")
        self.quantity.setValidator(QIntValidator(bottom=0))

        main.addWidget(self.product_articul)
        main.addWidget(self.quantity)
        main.addWidget(delete_btn := QPushButton("Удалить"))
        delete_btn.clicked.connect(self.delete)

    def delete(self):
        self.setParent(None)
        self.deleteLater()


class OrderForm(BackwardMixin):
    def __init__(self, *args, order: Order = None):
        super().__init__(*args)
        self.order = order or Order()
        self.body.addLayout(form := QVBoxLayout())
        self.base_columns = Order.get_fields({"articul"})

        form.addWidget(scroll := QScrollArea())
        scroll.setWidgetResizable(True)
        scroll.setWidget(scroll_content := QWidget())

        self.order_items = QVBoxLayout(scroll_content)
        for order_item in self.order.order_items:
            self.order_items.addWidget(OrderItemWidget(order_item))

        form.addWidget(add_btn := QPushButton("Добавить товар"))
        add_btn.clicked.connect(lambda: self.order_items.addWidget(OrderItemWidget()))

        self.status_list = QComboBox()
        self.status_list.addItems(c := ["Завершен", "Новый"])
        self.status_list.setCurrentIndex(
            self.order.status in c and c.index(self.order.status)
        )
        form.addWidget(self.status_list)

        self.address = QLineEdit(order and order.address.description)
        self.address.setPlaceholderText("Введите адрес")
        form.addWidget(self.address)

        self.code = QLineEdit(order and str(order.code))
        self.code.setPlaceholderText("Введите код получения")
        self.code.setValidator(QIntValidator(bottom=0))
        form.addWidget(self.code)

        self.created_at = QDateTimeEdit(order and order.created_at)
        self.created_at.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.created_at.setMinimumDate(QDate.currentDate())
        form.addWidget(self.created_at)

        self.deliver_at = QDateTimeEdit(order and order.deliver_at)
        self.deliver_at.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.deliver_at.setMinimumDate(QDate.currentDate())
        form.addWidget(self.deliver_at)

        form.addWidget(btn := QPushButton("Сохранить"))
        btn.clicked.connect(self.save)

    @property
    def order_items_data(self):
        if not self.order_items.count():
            msg(
                self, "Заказ должен состоять как минимум из одного товара", "Ошибка"
            )
            return None

        order_item_widgets = filter(lambda t: bool(t), [
            self.order_items.itemAt(i).widget()
            for i in range(self.order_items.count())
        ])
        arts, qs = zip(*[
            (c.product_articul.text(), c.quantity.text())
            for c in order_item_widgets
        ])
        if len(set(arts)) != len(arts):
            msg(
                self, "Артикулы товаров не должны повторятся", "Ошибка"
            )
            return None

        if '' in arts or '' in qs:
            msg(
                self,
                "Заполните все артикулы и кол-ва на складе, либо удалите поле",
                "Ошибка"
            )
            return None
        with Session() as session:
            if not all([session.query(Product).filter_by(articul=a).first() for a in arts]):
                msg(
                    self, "Вы ввели артикулы не существующих товаров", "Ошибка"
                )
                return None

        return [OrderItem(product_articul=a, quantity=int(q)) for a, q in zip(arts, qs)]

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

    def get_data(self, session):
        created_at = self.created_at.dateTime().toPython()
        deliver_at = self.deliver_at.dateTime().toPython()

        if deliver_at < created_at:
            msg(
                self,
                "Даты доставки не может быть раньше даты создания заказа",
                "Ошибка"
            )
            return None

        address = self.order.address
        if address.description != (g := self.address.text()):
            address = session.query(Address).filter_by(description=g).first()
            if not address:
                session.add(address := Address(description=g))
            session.flush()
        return {
            "created_at": created_at,
            "deliver_at": deliver_at,
            "user_id": Global.user.id,
            "address_id": address.id,
            "code": self.code.text(),
            "status": self.status_list.currentText()
        }

    def null_check(self, data):
        null_columns = [
            "  " + label
            for label, attr in self.base_columns
            if not data[attr]
        ]
        if null_columns:
            msg(
                self, "Вы не ввели:\n" + '\n'.join(null_columns), "Ошибка"
            )
            return False
        return True

    def save(self):
        if not self.ask() or not (order_item_data := self.order_items_data):
            return None

        with Session() as session:
            data = self.get_data(session)
            if not data or not self.null_check(data):
                return session.rollback()

            for attr, value in data.items():
                setattr(self.order, attr, value)
            self.order.order_items = order_item_data
            session.merge(self.order)
            session.flush()
            session.query(OrderItem).filter_by(order_articul=None).delete()
            session.commit()
        return QMessageBox.information(self, "Успешно", "Данные о заказе сохранены в БД")


class OrderWindow(BackwardMixin):
    def refresh(self):
        order_content = QWidget()
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
        self.body.addWidget(self.scroll)

        if Global.user.role == "Администратор":
            self.body.addWidget(btn := QPushButton("Создать новый заказ"))
            btn.clicked.connect(self.open_create_form)

    def open_create_form(self):
        Global.window = OrderForm("Создание заказ")
        Global.window.show()
        self.hide()
