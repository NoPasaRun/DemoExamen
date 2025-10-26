from pydantic import BaseModel, field_validator
from typing import Optional, Any

from pydantic._internal import _model_construction


class BaseForm(_model_construction.ModelMetaclass):

    @staticmethod
    def not_null(value: Any):
        if not value:
            raise ValueError("значение не предоставлено")
        return value

    def __new__(cls, name, bases, namespace, *args, **kwargs):
        for field_name, field in namespace.get('__annotations__', {}).items():
            namespace["__annotations__"][field_name] = Optional[field]
            namespace[field_name] = None
            decorated = field_validator(field_name, mode="before")(cls.not_null)
            namespace[f"validate_{field_name}_not_null"] = decorated
        return super().__new__(cls, name, bases, namespace, *args, **kwargs)
