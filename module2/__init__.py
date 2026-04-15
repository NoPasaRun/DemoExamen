from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QMainWindow, QMessageBox
)

from module1 import User, ROOT


class Global:
    window: Optional[QMainWindow] = None
    user: Optional[User] = None


class BaseWindow(QMainWindow):

    def __init__(self, title: str):
        super().__init__()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.body = QVBoxLayout(central_widget)
        self.title, self.header = QHBoxLayout(), QHBoxLayout()

        self.title.addWidget(QLabel(
            f"<h1>{title}</h1>"
        ), alignment=Qt.AlignmentFlag.AlignHCenter)

        self.body.addLayout(self.header)
        self.body.addLayout(self.title)

        if Global.user:
            self.header.addStretch()
            self.header.addWidget(QLabel(Global.user.fio))

        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(str(ROOT / "import/Icon.png")))


def msg(parent, text, title="Инфо", crit=False):
    func = QMessageBox.critical if crit else QMessageBox.information
    func(parent, title, text)
