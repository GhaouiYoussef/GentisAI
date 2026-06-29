from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path

from gentis_ai.core.errors import SessionStoreError

from .base import BaseSessionStore, SessionState


class SQLiteSessionStore(BaseSessionStore):
    def __init__(self, path: str | Path, ttl_seconds: int | None = None):
        self.path = Path(path)
        self.ttl_seconds = ttl_seconds
        if self.path.parent != Path("."):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at REAL NOT NULL,
                expires_at REAL
            )
            """
        )
        self._conn.commit()

    def get(self, session_id: str, default_expert: str) -> SessionState:
        now = time.time()
        try:
            with self._lock:
                row = self._conn.execute(
                    "SELECT payload, expires_at FROM sessions WHERE session_id = ?",
                    (session_id,),
                ).fetchone()
                if row is not None:
                    payload, expires_at = row
                    if expires_at is not None and expires_at <= now:
                        self._conn.execute(
                            "DELETE FROM sessions WHERE session_id = ?",
                            (session_id,),
                        )
                        self._conn.commit()
                    else:
                        return SessionState.model_validate_json(payload)

            return SessionState(
                session_id=session_id,
                current_expert=default_expert,
                created_at=now,
                updated_at=now,
                expires_at=self._expires_at(now),
            )
        except sqlite3.Error as exc:
            raise SessionStoreError(f"Could not read session {session_id}") from exc

    def save(self, state: SessionState) -> None:
        now = time.time()
        state = state.model_copy(deep=True)
        state.updated_at = now
        state.expires_at = self._expires_at(now)
        try:
            with self._lock:
                self._conn.execute(
                    """
                    INSERT INTO sessions (session_id, payload, updated_at, expires_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        payload = excluded.payload,
                        updated_at = excluded.updated_at,
                        expires_at = excluded.expires_at
                    """,
                    (
                        state.session_id,
                        state.model_dump_json(),
                        state.updated_at,
                        state.expires_at,
                    ),
                )
                self._conn.commit()
        except sqlite3.Error as exc:
            raise SessionStoreError(f"Could not save session {state.session_id}") from exc

    def delete(self, session_id: str) -> None:
        try:
            with self._lock:
                self._conn.execute(
                    "DELETE FROM sessions WHERE session_id = ?",
                    (session_id,),
                )
                self._conn.commit()
        except sqlite3.Error as exc:
            raise SessionStoreError(f"Could not delete session {session_id}") from exc

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def _expires_at(self, now: float) -> float | None:
        if self.ttl_seconds is None:
            return None
        return now + self.ttl_seconds
