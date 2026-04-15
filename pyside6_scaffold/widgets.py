from pyside6_scaffold.registry import SqlToPysideRegistry
from typing import Protocol, Any, Optional, Callable

from PySide6.QtWidgets import (
    QLayout, QComboBox, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton,
    QWidget, QLineEdit, QCheckBox, QScrollArea
)
from sqlalchemy import Column, Integer, Float, Boolean


class PysideWidget(Protocol):

    column: Column

    def data(self) -> Any | None:
        ...

    def layout(self) -> QLayout:
        ...


class PysideSelectable(PysideWidget):
    def __init__(self, func: Callable, column: Column, default: Any = None, session: Any = None):
        self.column = column
        self.func = func
        if options := column.info.get("choices"):
            self.choices = tuple(options)
        else:
            self.choices = session.query(
                self.column.mapper.class_
            ).all()
        self.default = default
        self.widget: Optional[QComboBox] = None

    def data(self):
        if self.widget is not None and self.widget.currentIndex():
            return self.choices[self.widget.currentIndex() - 1]
        return None

    def layout(self):
        layout = QVBoxLayout()
        box = QHBoxLayout()
        self.widget = select = QComboBox()

        box.addWidget(QLabel(self.column.info.get("label")))
        box.addStretch(1)
        box.addWidget(select)
        try:
            df_index = self.choices.index(self.default)
        except ValueError:
            df_index = 0
        select.addItems(["Ничего не выбрано"] + list(map(str, self.choices)))
        select.setCurrentIndex(df_index + 1)

        layout.addLayout(box)
        if hasattr(self, "model"):

            def callback(instance):
                select.addItems(str(instance))
                self.choices += (instance,)

            layout.addWidget(btn := QPushButton("Добавить запись +"))
            btn.clicked.connect(lambda: self.func(select, callback))

        layout.destroyed.connect(lambda: setattr(self, "widget", None))
        return layout


class PysideField(PysideWidget):

    def __init__(self, column: Column, default: Any = None):
        self.column = column
        self.default = default
        self.widget: Optional[QWidget] = None

    def data(self) -> Any | None:
        if self.widget is not None and (string := self.widget.text()):
            if isinstance(self.column.type, Integer):
                return int(string)
            if isinstance(self.column.type, Float):
                return float(string)
            if isinstance(self.column.type, Boolean):
                return bool(string)
            return string
        return None

    def layout(self):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(self.column.info.get("label")))
        layout.addStretch(1)

        self.widget = self.convert()
        layout.addWidget(self.widget)

        layout.destroyed.connect(lambda: setattr(self, "widget", None))
        return layout

    def convert(self, *args, **kwargs):
        local_registry = SqlToPysideRegistry()
        func = local_registry.get(type(self.column.type), lambda *_, **__: QLineEdit())
        return func(self, *args, **kwargs)


class PysideMultipleSelectable(PysideWidget):
    def __init__(self, func: Callable, column: Column, default: list[Any] = None, session: Any = None):
        self.column = column
        self.func = func
        self.choices = session.query(
            self.column.mapper.class_
        ).all()
        self.default = default
        self.scrollable: Optional[QVBoxLayout] = None

    def data(self):
        if not self.scrollable:
            return []
        layouts = [
            self.scrollable.itemAt(i).layout()
            for i in range(self.scrollable.count())
        ]
        return [
            self.choices[i] for i, layout in enumerate(layouts)
            if layout.itemAt(1).widget().isChecked()
        ]

    def add_child(self, child: Any):
        if not self.scrollable:
            return
        box = QHBoxLayout()
        box.addWidget(QLabel(str(child)))
        box.addWidget(wg := QCheckBox())
        wg.setChecked(child in self.default)
        self.scrollable.addLayout(box)

    def layout(self):
        content = QWidget()
        layout, self.scrollable = QHBoxLayout(), QVBoxLayout(content)
        wrapper = QVBoxLayout()

        layout.addWidget(QLabel(self.column.info.get("label")))
        layout.addLayout(wrapper)
        scroll = QScrollArea()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)

        for choice in self.choices:
            self.add_child(choice)

        def callback(instance):
            self.add_child(instance)
            self.choices += (instance,)

        wrapper.addWidget(scroll)
        wrapper.addWidget(btn := QPushButton("Добавить запись +"))
        btn.clicked.connect(lambda: self.func(content, callback))

        layout.destroyed.connect(lambda: setattr(self, "scrollable", None))
        return layout
