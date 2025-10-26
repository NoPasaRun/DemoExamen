import sys

from PySide6.QtWidgets import QApplication, QLineEdit, QWidget, QPushButton, QVBoxLayout
from pydantic import ValidationError

from forms.login import LoginForm
from ui.window import BaseWindow


class LoginWindow(BaseWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.formData = {
            "password": "",
            "username": ""
        }

        self.flex_container = QWidget()
        self.layout = QVBoxLayout(self.flex_container)
        self.flex_container.setProperty("class", "form")

        self.username = QLineEdit()
        self.username.setProperty("class", "field")
        self.username.textEdited.connect(self.handle_edit_username)

        self.password = QLineEdit()
        self.password.setProperty("class", "field")
        self.password.textEdited.connect(self.handle_edit_password)

        self.submit = QPushButton()
        self.submit.setProperty("class", "submit")
        self.submit.clicked.connect(self.auth)

        self.layout.addWidget(self.username, stretch=1)
        self.layout.addWidget(self.password, stretch=1)
        self.layout.addWidget(self.submit, stretch=0.5)
        self.setLayout(self.layout)

    def handle_edit_password(self, text: str):
        index = text.index(sym := text.strip("*"))
        self.formData["password"] = self.formData["password"][0:index] + sym
        self.password.setText("*" * len(text))

    def handle_edit_username(self, text):
        self.formData["username"] = text

    def auth(self):
        try:
            form = LoginForm(**self.formData)
        except ValidationError as e:
            e: ValidationError
            print(e.errors())


def main():
    app = QApplication(sys.argv)
    login_window = LoginWindow("styles/login", expand=True)
    login_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()