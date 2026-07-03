from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .spec import ToolSpec


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolSpec] = {}

    def register(self, tool: ToolSpec | Callable[..., Any]) -> ToolSpec:
        spec = tool if isinstance(tool, ToolSpec) else ToolSpec.from_function(tool)
        self._tools[spec.name] = spec
        return spec

    def get(self, name: str) -> ToolSpec:
        return self._tools[name]

    def list(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def to_openai_tools(self) -> list[dict[str, Any]]:
        return [tool.to_openai_tool() for tool in self._tools.values()]
