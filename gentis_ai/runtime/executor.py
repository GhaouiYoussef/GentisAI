from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def collect_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Iterable):
        return "".join(str(chunk) for chunk in value)
    return str(value)
