from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any, get_origin

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolSpec(BaseModel):
    name: str
    description: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    function: Callable[..., Any] | None = None

    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def from_function(cls, function: Callable[..., Any]) -> "ToolSpec":
        signature = inspect.signature(function)
        properties: dict[str, Any] = {}
        required: list[str] = []

        for name, parameter in signature.parameters.items():
            schema = {"type": _json_type(parameter.annotation)}
            if parameter.default is inspect._empty:
                required.append(name)
            properties[name] = schema

        return cls(
            name=function.__name__,
            description=inspect.getdoc(function) or "",
            parameters={
                "type": "object",
                "properties": properties,
                "required": required,
            },
            function=function,
        )

    def to_openai_tool(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


def _json_type(annotation: Any) -> str:
    if annotation is inspect._empty:
        return "string"

    origin = get_origin(annotation)
    if origin is not None:
        annotation = origin

    mapping = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }
    return mapping.get(annotation, "string")
