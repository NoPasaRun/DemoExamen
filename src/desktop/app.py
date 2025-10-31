from typing import Dict

from pydantic import ValidationError
from sqlalchemy import or_

from db.models import User, Product
from db.connection import create_session
from desktop.forms import LoginForm, SearchProductForm
from desktop.window import WindowEnum

from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QObject, Slot
from PySide6.QtWebChannel import QWebChannel

import sys

from settings import app_settings


AUTH_USERS: Dict[str, User] = dict()


class Bridge(QObject):

    def __init__(self, view: QWebEngineView):
        super().__init__()
        self.view = view

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

    @Slot(str, result=None)
    def change_page(self, data: str):
        if hasattr(WindowEnum, data):
            self.view.load(getattr(WindowEnum, data).url)

    @Slot(dict, result=dict)
    def get_products(self, data):
        try:
            form, filters = SearchProductForm(**data), list()
            if form.q:
                q = f"%{form.q}%"
                filters.append(
                    or_(
                        or_(Product.title.like(q), Product.supplier.like(q)),
                        Product.producer.like(q)
                    )
                )
            filters.append((Product.price * (100 - Product.discount) / 100).between(form.min_price, form.max_price))
            with create_session() as session:
                products = Product.filter(session, *filters)
                products = [dict(p) for p in products]
        except ValidationError as e:
            errors = e.errors()
        else:
            return {"data": products, "ok": True}
        return {"errors": errors, "ok": False}


def main():
    app = QApplication(sys.argv)
    web_view = QWebEngineView()

    channel = QWebChannel()
    bridge = Bridge(web_view)
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
