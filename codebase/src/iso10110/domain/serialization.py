from __future__ import annotations

import json
from dataclasses import asdict, fields, is_dataclass
from typing import Any

from .model import SpecV2


def spec_to_dict(spec: SpecV2) -> dict[str, Any]:
    return asdict(spec)


def spec_to_pretty_json(spec: SpecV2) -> str:
    return json.dumps(spec_to_dict(spec), indent=2, ensure_ascii=False)


def get_attr_path(obj: Any, path: str) -> Any:
    current = obj
    for part in path.split("."):
        current = getattr(current, part)
    return current


def set_attr_path(obj: Any, path: str, value: Any) -> None:
    parts = path.split(".")
    current = obj
    for part in parts[:-1]:
        current = getattr(current, part)
    setattr(current, parts[-1], value)


def dataclass_clone(instance: Any) -> Any:
    if not is_dataclass(instance):
        raise TypeError("dataclass_clone expects a dataclass instance")

    values: dict[str, Any] = {}
    for field in fields(instance):
        value = getattr(instance, field.name)
        if is_dataclass(value):
            values[field.name] = dataclass_clone(value)
        else:
            values[field.name] = value
    return type(instance)(**values)
