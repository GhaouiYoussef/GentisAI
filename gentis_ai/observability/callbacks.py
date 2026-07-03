from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from gentis_ai.core.events import FlowEvent


EventHandler = Callable[[FlowEvent], None]
Hook = Callable[..., None]


@dataclass
class CallbackManager:
    event_handlers: list[EventHandler] = field(default_factory=list)
    hooks: dict[str, list[Hook]] = field(default_factory=dict)

    def add_event_handler(self, handler: EventHandler) -> None:
        self.event_handlers.append(handler)

    def add_hook(self, name: str, hook: Hook) -> None:
        self.hooks.setdefault(name, []).append(hook)

    def on_event(self, event: FlowEvent) -> None:
        for handler in self.event_handlers:
            handler(event)
        self._run_hook(event.type, event=event)

    def on_route(self, decision: Any) -> None:
        self._run_hook("on_route", decision=decision)

    def on_llm_start(self, provider: str | None = None) -> None:
        self._run_hook("on_llm_start", provider=provider)

    def on_llm_end(self, usage: dict[str, int] | None = None) -> None:
        self._run_hook("on_llm_end", usage=usage or {})

    def on_tool_start(self, name: str) -> None:
        self._run_hook("on_tool_start", name=name)

    def on_tool_end(self, name: str, ok: bool) -> None:
        self._run_hook("on_tool_end", name=name, ok=ok)

    def on_expert_started(self, name: str) -> None:
        self._run_hook("on_expert_started", name=name)

    def on_error(self, message: str) -> None:
        self._run_hook("on_error", message=message)

    def _run_hook(self, hook_name: str, **kwargs: Any) -> None:
        for hook in self.hooks.get(hook_name, []):
            hook(**kwargs)
