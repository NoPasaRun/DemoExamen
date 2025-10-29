from typing import Dict

from pydantic import ValidationError

from db.models import User
from desktop.forms import LoginForm
from desktop.window import WindowEnum

from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QObject, Slot
from PySide6.QtWebChannel import QWebChannel

import sys

from settings import app_settings

AUTH_USERS: Dict[str, User] = dict()


class Bridge(QObject):

    def __init__(self):
        super().__init__()

    @Slot(dict, result=dict)
    def auth_request(self, data):
        try:
            form = LoginForm(**data)
            AUTH_USERS[form.user.encrypt_user_id] = form.user
        except ValidationError as e:
            errors = e.errors()
        else:
            return {"data": dict(form.user), "ok": True}
        return {"errors": errors, "ok": False}


def main():
    app = QApplication(sys.argv)

    web_view = QWebEngineView()

    channel = QWebChannel()
    bridge = Bridge()
    channel.registerObject("bridge", bridge)

    web_view.page().setWebChannel(channel)
    web_view.load(WindowEnum.auth.url)

    web_view.show()
    if app_settings.debug:
        dev_tools = QWebEngineView()
        web_view.page().setDevToolsPage(dev_tools.page())
        dev_tools.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
