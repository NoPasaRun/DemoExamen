import sys

from PySide6.QtWidgets import QApplication

from pyside6_scaffold.forms import open_sub_window
from module1 import Session, User


if __name__ == '__main__':
    app = QApplication(sys.argv)
    with Session() as ses:
        window = open_sub_window(User, None, ses, is_active=True)
    sys.exit(app.exec())
