from typing import Callable, Any, Optional

from PySide6.QtCore import QLocale, QDateTime
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import QWidget, QLineEdit, QDateTimeEdit, QCheckBox
from sqlalchemy import Float, Integer, DateTime, String, Boolean


DEFAULT_DATETIME_FORMAT = "dd.MM.yyyy HH:mm"


class SqlToPysideRegistry:

    __instance: Optional['SqlToPysideRegistry'] = None

    def __new__(cls):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        if not hasattr(self, f"_{self.__class__.__name__}__converters"):
            self.__converters: dict[Any, Callable] = dict()

    def get(self, type_: Any, default: Callable = None):
        return self.__converters.get(type_, default)

    def register(self, type_: Any):
        def outer(func: Callable) -> Callable:
            def inner(*args, **kwargs) -> QWidget:
                return func(*args, **kwargs)
            self.__converters[type_] = func
            return inner
        return outer

    @staticmethod
    def get_range(field: 'PysideField'):
        return dict(zip(
            ["bottom", "top"], field.column.info.get("range", [])
        ))


type_registry = SqlToPysideRegistry()


@type_registry.register(Float)
def as_float(field: 'PysideField') -> QWidget:
    widget = QLineEdit(field.default and str(field.default))
    widget.setValidator(validator := QDoubleValidator(
        **(type_registry.get_range(field)),
        **{"decimals": field.column.info.get("decimals", 0)}
    ))
    validator.setLocale(QLocale("C"))
    widget.setPlaceholderText("Введите число с плавающей точкой")
    return widget


@type_registry.register(Integer)
def as_integer(field: 'PysideField') -> QWidget:
    widget = QLineEdit(field.default and str(field.default))
    widget.setValidator(QIntValidator(**(type_registry.get_range(field))))
    widget.setPlaceholderText("Введите число")
    return widget


@type_registry.register(DateTime)
def as_datetime(field: 'PysideField') -> QWidget:
    widget = QDateTimeEdit()
    if df := field.default:
        widget.setDateTime(QDateTime(df))
    format_ = field.column.info.get("format", DEFAULT_DATETIME_FORMAT)
    widget.setDisplayFormat(format_)
    return widget


@type_registry.register(String)
def as_string(field: 'PysideField') -> QWidget:
    widget = QLineEdit(field.default)
    widget.setPlaceholderText("Введите текст")
    return widget


@type_registry.register(Boolean)
def as_boolean(field: 'PysideField') -> QWidget:
    widget = QCheckBox()
    widget.setChecked(bool(field.default))
    return widget
