from PySide6.QtWidgets import (
    QMessageBox, QLayout, QVBoxLayout,
    QWidget, QMainWindow, QDialog, QPushButton
)

from pyside6_scaffold.core import Message, Model
from pyside6_scaffold.widgets import (
    PysideWidget, PysideField,
    PysideSelectable,
    PysideMultipleSelectable
)
from typing import Any, Iterable, Callable

from sqlalchemy import Table, inspect, Column
from sqlalchemy.orm import Mapper, RelationshipProperty


class PysideForm(PysideWidget):
    def __init__(self, model: 'Model', session: Any = None, **defaults):
        self.exclude_columns = getattr(model, "exclude_columns", set())
        self.verbose_name = getattr(model, "verbose_name", model.__table__.name)

        self._mapper: Mapper = inspect(model)
        self.table: Table = model.__table__
        self.session = session

        self.fields: dict[str, 'PysideWidget'] = dict()
        choice_fields = set(filter(lambda c: c.info.get("choices"), self.columns))

        for col in self.columns - choice_fields:
            self.fields[col.key] = PysideField(col, defaults.get(col.key))

        cls_col_data = [
            [PysideSelectable, self.relations | choice_fields],
            [PysideMultipleSelectable, self.m2m_relations],
        ]

        for cls, columns in cls_col_data:
            for col in columns:
                self.fields[col.key] = cls(
                    lambda parent, callback: open_sub_window(
                        col.mapper.class_, parent, session, callback
                    ),
                    col, defaults.get(col.key), session
                )

    def null_check(self):
        for key, field in self.fields.items():
            if isinstance(field, PysideForm):
                if not field.null_check():
                    return False
            elif not field.column.nullable and field.data() is None:
                Message(1).call(
                    "Некорректное значение",
                    f"Вы ввели неверно: {field.column.info.get("label")}"
                )
                return False
        return True

    def instance(self):
        obj = self._mapper.class_()
        for key, field in self.fields.items():
            if isinstance(field, PysideForm):
                setattr(obj, key, field.instance())
            else:
                setattr(obj, key, field.data())
        return obj

    def save(self) -> bool | Any:
        reply = Message(3).call(
            "Подтверждение", f"Вы уверены что хотите сохранить данные?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return False
        if not self.null_check():
            return False

        self.session.merge(instance := self.instance())
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            Message(2).call("Ошибка", str(e))
        return instance

    def layout(self) -> QLayout:
        layout = QVBoxLayout()
        for field in self.fields.values():
            layout.addLayout(field.layout())
        return layout

    @property
    def columns(self):
        return {
            col for col in self.table.columns.values()
            if col.key not in self.exclude_columns
        }

    @staticmethod
    def get_rel_column(column: Column, relationships: Iterable[RelationshipProperty]) -> RelationshipProperty:
        def wrapper():
            for rel in relationships:
                if column.name in [col.name for col in rel.local_columns]:
                    yield rel
            yield
        return next(wrapper())

    @property
    def relations(self):
        return {
            self.get_rel_column(fk.parent, self._mapper.relationships)
            for fk in self.table.foreign_keys
        }

    @property
    def m2m_relations(self):
        return [
            rel for rel in self._mapper.relationships
            if not any(
                fk.parent.name in [col.name for col in rel.local_columns]
                for fk in self.table.foreign_keys
            )
        ]


def open_sub_window(
    model: Model,
    parent: QWidget = None,
    session: Any = None,
    callback: Callable = lambda *_, **__: ...,
    **kwargs
) -> QMainWindow | QDialog:

    def click():
        if not (instance := form.save()):
            return
        sub_window.close()
        callback(instance)

    body = QVBoxLayout()
    if parent is not None:
        sub_window = QDialog(parent)
        sub_window.setModal(True)
        sub_window.setLayout(body)
    else:
        sub_window, central = QMainWindow(), QWidget()
        sub_window.setCentralWidget(central)
        central.setLayout(body)
    form = PysideForm(model, session, **kwargs)
    body.addLayout(form.layout())
    body.addWidget(btn := QPushButton("сохранить"))

    btn.clicked.connect(click)
    sub_window.show()
    return sub_window