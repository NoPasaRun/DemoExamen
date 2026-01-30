import os
from typing import Callable

from PySide6.QtCore import QLocale
from PySide6.QtGui import QDoubleValidator, QIntValidator, QPixmap, Qt
from PySide6.QtWidgets import (
    QPushButton,
    QFrame,
    QVBoxLayout,
    QLineEdit,
    QComboBox, QWidget, QFileDialog, QLabel, QMessageBox
)
from sqlalchemy import func, or_
from module1 import Company, Session, Product, ROOT, OrderItem
from module2 import MainWindow, BaseWindow


class BackwardMixin(BaseWindow):
    """
    Класс, который реализует логику перехода на предыдущую страницу.
    ВНИМАНИЕ. При переходе назад, страница не создается заново, а достается из памяти,
    в таком состоянии, в котором мы ее покинули
    """

    def __init__(self, *args):
        super().__init__(*args)
        current = MainWindow()
        # Если текущая страница не None, то мы можем вернуться
        if current is not None:
            self.header.addWidget(btn := QPushButton('назад'))
            btn.clicked.connect(self.backwards)
        # Теперь предыдущая, это текущая, а текущая, это созданная тут страница
        self.__prev, _ = current, MainWindow.set_window(self)

    def backwards(self):
        # При переходя назад предыдущая становится текущей
        if self.__prev is None:
            return
        self.__prev.show()
        MainWindow.set_window(self.__prev)
        self.hide()


class FilterProductWidget(QFrame):
    """
    Класс с фильтрами
    """

    def __init__(self, callback: Callable):
        super().__init__()
        self.layout = QVBoxLayout()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск")
        self.search.textEdited.connect(self.refresh(callback))
        self.layout.addWidget(self.search)

        """
        Список компаний, которые могут быть поставщиками. ВНИМАНИЕ, не рекомендуется просто использовать
        название поставщика для фильтрации. Зачем вам морочиться с join-ами? Проще фильтровать по id
        поставщика, по которому у нас и настроена связь. Но id не информативно, поэтому пользователю
        мы выводим список названий компаний, а уже при создании фильтров мы мэтчим индекс выбранного
        поставщика с его реальным id.
        
        ВНИМАНИЕ currentIndex и supplier.id НЕ СОВПАДАЮТ. currentIndex это id в списке интерфейса, а supplier.id
        это id из БД. Для этого нам нужен словарь, чтобы сопоставить одно с другим
        """
        self.list = QComboBox()
        with Session() as session:
            suppliers = session.query(Company).all()

            # Отчет идет с одного, потому что первый элемент это "Все поставщики" у которого нет id
            # те его значение None
            self.mapper = {i: val.id for i, val in enumerate(suppliers, 1)}
            self.list.addItems(["Все поставщики", *[val.name for val in suppliers]])
        self.list.currentIndexChanged.connect(self.refresh(callback))
        self.layout.addWidget(self.list)

        self.sorting = QComboBox()
        # Первый индекс - это False (.desc()), второй - True (.asc())
        self.mapper2 = {1: False, 2: True}
        self.sorting.addItems(
            ['Нет сортировки по кол-ву на складе', 'По убыванию', 'По возрастанию']
        )
        self.sorting.currentIndexChanged.connect(self.refresh(callback))
        self.layout.addWidget(self.sorting)
        self.setLayout(self.layout)

    def refresh(self, f: Callable):
        def inner():
            return f(self.filters, self.order_by)

        return inner

    @property
    def order_by(self):
        is_asc = self.mapper2.get(self.sorting.currentIndex())
        # Если первый индекс то по убыванию, если второй - по возрастанию, главное не запутайтесь
        return (Product.quantity if is_asc else Product.quantity.desc(),)

    @property
    def filters(self):
        f = []
        if q := self.search.text().lower():
            exp = func.lower(Product.articul).like(f"%{q}%")
            """
            Нам нужен поиск либо по имени, либо по категории, либо по описанию.
            тк or_ принимает всего два аргумента, то мы последовательно строим
            выражение из предыдущего or_ и нового выражения
            """
            for attr in ["name", "category", "description"]:
                exp = or_(
                    exp,
                    # Приводим функцией поле в бд к нижнему регистру и проверяем, что оно совпадает
                    # с паттерном % + q + %, где % это 0..N символов спереди и сзади
                    func.lower(getattr(Product, attr)).like(f"%{q}%")
                )
            """
            ИЗМЕНЕНИЕ: добавляем возможность фильтрации по имени компании производителя
            """
            exp = or_(exp, func.lower(Company.name).like(f"%{q}%"))
            f.append(exp)
        if supplier_id := self.mapper.get(self.list.currentIndex()):
            # если get не нашел индекс, значит значение None и условие не сработает,
            # фильтр не добавиться в список. индекс не найден, если выбрано "Все поставщики"
            f.append(Product.supplier_id == supplier_id)
        return tuple(f)


class ImageUploader(QWidget):
    """
    Класс для загрузки фото
    """

    def __init__(self, filepath: str):
        super().__init__()
        layout = QVBoxLayout(self)
        self.load: QPixmap = None

        self.image_label = QLabel()
        self.image_label.setFixedSize(150, 150)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: 1px dashed gray;")
        self.set_pixmap(QPixmap(filepath))
        layout.addWidget(self.image_label)

        self.upload_btn = QPushButton("Выбрать фото")
        self.upload_btn.clicked.connect(self.load_image)
        layout.addWidget(self.upload_btn)

    def set_pixmap(self, pixmap: QPixmap):
        """
        Здесь устанавливаем превью на label
        :param pixmap:
        :return:
        """
        self.image_label.setPixmap(pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

    def load_image(self):
        # Вся магия в этом диалоговом окне, которое позволяет открыть проводник
        new_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение",
            "", "Images (*.png *.jpg *.jpeg)"
        )

        if new_path:
            pixmap = QPixmap(new_path)
            # Проверка на размер файла. 300x200 оч мало, даже фото в примере больше, поэтому я добавил два нуля
            if pixmap.width() * pixmap.height() > 6_000_000:
                return QMessageBox.critical(
                    self,
                    "Ошибка",
                    "Изображение должно быть не больше формата 300x200"
                )
            self.load = pixmap
            self.set_pixmap(self.load)


def delete_product(product: Product):
    """
    Функция не привязана к окну редактирования, но тк она упоминается в 3-ем модуле, я ее и закинул сюда
    :param product:
    :return:
    """
    prev_filepath = product.photo
    with Session() as session:
        if session.query(OrderItem).filter_by(articul=product.articul).first():
            # Ну тут как будто очевидно. Если есть заказ товара а нашим артикулом
            # то есть и заказ в котором товар 'учавствует'. По ТЗ не удаляем.
            QMessageBox.critical(
                None, "Ошибка", "Нельзя удалить товар, если он в заказе"
            )
            return False
        session.delete(product)
        session.commit()
    # Чистим фото если оно не None и существует
    if prev_filepath is not None and os.path.exists(prev_filepath):
        os.remove(prev_filepath)
    QMessageBox.information(None, "Успешно", "Товар удален из БД")
    return True


class ProductForm(BackwardMixin):
    """
    Форма создания/редактирования товара

    По факту создание и редактирование одна и та же функциональность. Единственное отличие:
    в создании поля пустые, а в редактировании подгружены. Но QLineEdit не ругается на то что мы передаем ей None
    так что по факту мы можем сделать пустой Product() если product = None, а если product не None, то мы передаем
    в поля готовые значения.
    """

    def __init__(self, *args, product: Product = None):
        super().__init__(*args)
        self.form = QVBoxLayout()

        # Один момент. Если мы редактируем, то артикул менять нельязя тк он primary key. Просто не передаем поле
        self.base_columns = (['articul'] if not product else []) + [
            "name", "description", "category", 'measure_type',
            'price', 'discount', 'quantity'
        ]
        # Тут локализация чтобы понять, где какое поле. Используется в сообщении с ошибкой о пустых полях и в заглушке
        # самого поля
        self.ru_columns = (['артикул'] if not product else []) + [
            "название", "описание", 'категорию', 'единицу измерения',
            'цену', 'скидку', 'кол-во на складе',
            'фото', 'производителя', 'поставщика'
        ]
        # Тот самый момент с тем, что у нас product не может быть None. У него либо все поля None (создание),
        # либо поля все имеются (значит редактирование)
        self.product = product or Product()

        # для удобства переменные интерфейса названы так же как и поля продукта
        # setattr устанавливает переменные так же как если бы вы делали self.price = QLineEdit()
        # setattr(self, "price", QLineEdit()) первый параметр объект в который засовываем данные
        # второй - имя атрибута, третий - значение. Редакторы кода не умеют анализировать такое
        # присвоение, да и ### бы с ним. Желтая курсивная линия это норм, забейте, прогайте дальше
        # https://www.w3schools.com/python/ref_func_setattr.asp
        for ru_name, attr in zip(self.ru_columns, self.base_columns):
            product_value = getattr(self.product, attr)
            setattr(
                self, attr, w := QLineEdit(
                    str(product_value) if product_value is not None else None
                )
            )
            w.setPlaceholderText(f"Введите {ru_name}")
            self.form.addWidget(w)

        # Сдесь делаем привентивную валидацию числовых полей, чтобы не писать проверку на валидность
        v1 = QDoubleValidator(top=0.0, bottom=1000000.0, decimals=2)
        # setLocale переводит числа с запятой в числа с точкой
        v1.setLocale(QLocale("C"))
        self.price.setValidator(v1)

        v2 = QDoubleValidator(bottom=0.0, top=100.0, decimals=2)
        v2.setLocale(QLocale("C"))
        self.discount.setValidator(v2)

        self.quantity.setValidator(QIntValidator(bottom=0))

        self.supplierList = QComboBox()
        self.manufacturerList = QComboBox()
        with Session() as session:
            companies = session.query(Company).all()
            self.mapper = {i: val.id for i, val in enumerate(companies, 1)}

            names = ["Не выбрано", *[val.name for val in companies]]
            self.supplierList.addItems(names)
            self.manufacturerList.addItems(names)

        self.supplierList.setCurrentText(
            product and self.product.supplier.name or 'Выберите поставщика'
        )
        self.manufacturerList.setCurrentText(
            product and self.product.manufacturer.name or 'Выберите производителя'
        )
        self.form.addWidget(self.supplierList)
        self.form.addWidget(self.manufacturerList)

        self.photo = ImageUploader(self.product.valid_photo)
        self.form.addWidget(self.photo)

        self.saveBtn = QPushButton("Сохранить")
        self.saveBtn.clicked.connect(self.save)
        self.form.addWidget(self.saveBtn)

        self.layout.addLayout(self.form)

    def save(self):
        """
        Сохраняем товар
        :return:
        """
        # Сначала проверяем, если у нас есть поле articul, значит мы создаем товар. Если мы создаем товар
        # значит нужно проверить что у нас articul не повторяется нигде в БД
        reply = QMessageBox.question(
            self,
            'Подтверждение',
            "Вы уверены, что хотите сохранить данные?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return

        if hasattr(self, 'articul'):
            articul = self.articul.text()
            with Session() as session:
                if session.query(Product).filter_by(articul=articul).first():
                    # Если повторяется, выходим из функции
                    return QMessageBox.information(
                        self, "Ошибка", "Товар с таким артикулом уже имеется"
                    )
        else:
            articul = self.product.articul
        # Наши данные по всем полям. Так как виджеты названы так же как и поля product, то впоследствии
        # очень удобно будет сопоставить их значения.
        data = {
                   # ВНИМАНИЕ getattr(self, col) это не значение поля а QLineEdit!!! А нам нужно значение,
                   # поэтому берем .text()
                   col: getattr(self, col).text()
                   for col in self.base_columns
               } | {
                   # Эти поля не QLineEdit поэтому прописываем их вручную
                   "photo": str(ROOT / 'import' / (articul + '.jpg')) if self.photo.load else self.product.photo,
                   "manufacturer_id": self.mapper.get(self.manufacturerList.currentIndex()),
                   "supplier_id": self.mapper.get(self.supplierList.currentIndex())
               }

        # Пустых полей быть не должно. Проверяем: если они есть, то пишем какие.
        # Для этого используем русские названия полей в сообщении
        null_columns = [
            '  ' + ru for ru, value in zip(self.ru_columns, data.values())
            if not value and ru != 'фото'
        ]
        if null_columns:
            # Если список пустых полей имеет значения, то выходим из функции
            return QMessageBox.critical(
                self, "Ошибка", f"Вы не ввели:\n{'\n'.join(null_columns)}"
            )

        # Сохраняем путь до старого фото
        prev_path = self.product.photo
        # А тут мы значения из полей переносим в поля product. key = col из data
        for key, value in data.items():
            setattr(self.product, key, value)
        with Session() as session:
            # merge умная функция которая либо сохранит новые данные либо по primary key найдет запись
            # и обновит в ней значения
            session.merge(self.product)
            session.commit()

        # Если новое фото загружено, то сохраняем его. Если не загружено, то поле photo будет содержать None
        # Фото
        if self.photo.load:
            # Если старое фото имеется, то мы его удаляем
            if prev_path and os.path.exists(prev_path):
                os.remove(prev_path)
            self.photo.load.save(self.product.photo)
        return QMessageBox.information(self, "Успешно", "Товар сохранен в БД")
