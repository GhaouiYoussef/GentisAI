from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


EventType = Literal[
    "route_started",
    "route_finished",
    "expert_started",
    "token",
    "tool_call",
    "tool_result",
    "final",
    "error",
]


class FlowEvent(BaseModel):
    type: EventType
    content: str = ""
    agent_name: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
