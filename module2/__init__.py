from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QMainWindow
)

from module1 import User, ROOT


class MainWindow:
    """
    Короче, глобальные переменные - это практика говна. Принцип как бы не поменялся,
    но синглтон, это как бы паттерн, а global - антипаттерн, поэтому вот так.

    Тут у нас хранится ОДНО активное окно и ОДИН активный пользователь, чтобы не
    морочиться с синхронизацией между несколькими окнами.
    """
    __instance: QMainWindow = None
    __user: User = None

    def __new__(cls) -> Optional[QMainWindow]:
        return cls.__instance

    @classmethod
    def set_window(cls, window: Optional[QMainWindow]):
        cls.__instance = window
        return cls.__instance

    @classmethod
    def set_user(cls, user: Optional[User]):
        cls.__user = user

    @classmethod
    def get_user(cls):
        return cls.__user


class BaseWindow(QMainWindow):

    """
    Тупое наследование - это плохо, но лучше так, чем copy-paste.

    Тут выносим повторяющиеся виджеты - Заголовок страницы, иконка, шапка
    и ФИО, если пользователь есть в MainWindow
    """

    def __init__(self, title: str):
        super().__init__()
        self.header = QHBoxLayout(header := QWidget())

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

        if user := MainWindow.get_user():
            self.top_layout.addWidget(QLabel(user.fio))

        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(str(ROOT / "import/icon.png")))
