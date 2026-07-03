from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from gentis_ai.core.types import Message


class SessionState(BaseModel):
    session_id: str
    current_expert: str
    history: list[Message] = Field(default_factory=list)
    summary: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: float = 0.0
    updated_at: float = 0.0
    expires_at: float | None = None


class BaseSessionStore(ABC):
    @abstractmethod
    def get(self, session_id: str, default_expert: str) -> SessionState:
        """Load an existing session or create an empty one."""

    @abstractmethod
    def save(self, state: SessionState) -> None:
        """Persist session state."""

    @abstractmethod
    def delete(self, session_id: str) -> None:
        """Delete a session if it exists."""
