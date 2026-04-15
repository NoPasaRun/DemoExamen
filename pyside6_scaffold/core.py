from enum import Enum
from typing import Protocol

from PySide6.QtWidgets import QWidget, QMessageBox
from sqlalchemy import Table
from sqlalchemy.orm import registry


class Message(Enum):
    INFORMATION = 0
    WARNING = 1
    CRITICAL = 2
    QUESTION = 3

    def call(self, title: str, message: str, *args, parent: QWidget = None):
        reply = getattr(QMessageBox, self.name.lower())(parent, title, message, *args)
        return reply


class Model(Protocol):
    registry: registry
    verbose_name: str
    exclude_columns: set[str]
    __table__: Table