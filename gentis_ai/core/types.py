from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


MessageRole = Literal["system", "user", "assistant", "tool"]


class Expert(BaseModel):
    """A persona or domain specialist available to the router."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str = ""
    system_prompt: str | None = None
    model_name: str | None = None
    tools: list[Any] = Field(default_factory=list)

    @model_validator(mode="after")
    def _default_system_prompt(self) -> "Expert":
        if self.system_prompt:
            return self

        description = self.description or "Handle user requests in your domain."
        self.system_prompt = f"You are {self.name}. {description}"
        return self


class Message(BaseModel):
    """Provider-neutral message format used inside GentisAI."""

    role: MessageRole
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("role", mode="before")
    @classmethod
    def _normalize_legacy_roles(cls, value: Any) -> Any:
        if value == "model":
            return "assistant"
        return value


class TurnResponse(BaseModel):
    """The result of a single conversation turn."""

    content: str
    agent_name: str
    switched_context: bool
    token_usage: dict[str, int] = Field(default_factory=lambda: {"total": 0})
    session_id: str | None = None
    structured: dict[str, Any] = Field(default_factory=dict)
