from __future__ import annotations

from collections.abc import Callable
from typing import TypeAlias

from gentis_ai.routing import RoutingDecision

from .spec import ToolCall


ToolPolicy: TypeAlias = Callable[[str, RoutingDecision], list[ToolCall]]

__all__ = ["ToolPolicy"]
