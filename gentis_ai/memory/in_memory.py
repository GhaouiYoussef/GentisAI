from __future__ import annotations

import threading
import time

from .base import BaseSessionStore, SessionState


class InMemorySessionStore(BaseSessionStore):
    def __init__(self, ttl_seconds: int | None = None):
        self.ttl_seconds = ttl_seconds
        self._sessions: dict[str, SessionState] = {}
        self._lock = threading.Lock()

    def get(self, session_id: str, default_expert: str) -> SessionState:
        now = time.time()
        with self._lock:
            state = self._sessions.get(session_id)
            if state and state.expires_at is not None and state.expires_at <= now:
                del self._sessions[session_id]
                state = None

            if state is None:
                state = SessionState(
                    session_id=session_id,
                    current_expert=default_expert,
                    created_at=now,
                    updated_at=now,
                    expires_at=self._expires_at(now),
                )
                self._sessions[session_id] = state

            return state.model_copy(deep=True)

    def save(self, state: SessionState) -> None:
        now = time.time()
        state = state.model_copy(deep=True)
        state.updated_at = now
        state.expires_at = self._expires_at(now)
        with self._lock:
            self._sessions[state.session_id] = state

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def clear(self) -> None:
        with self._lock:
            self._sessions.clear()

    def _expires_at(self, now: float) -> float | None:
        if self.ttl_seconds is None:
            return None
        return now + self.ttl_seconds
