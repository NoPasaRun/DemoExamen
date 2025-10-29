from enum import StrEnum

from PySide6.QtCore import QUrl

from settings import app_settings


class WindowEnum(StrEnum):
    auth = "index.html"

    @property
    def url(self) -> QUrl:
        abs_url = app_settings.root / f'assets/templates/{self.value}'
        url = QUrl.fromLocalFile(abs_url)

        return url

