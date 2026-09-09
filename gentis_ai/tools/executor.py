from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Any

from pydantic import BaseModel

from gentis_ai.core.errors import ToolExecutionError

from .registry import ToolRegistry

logger = logging.getLogger(__name__)

class ToolResult(BaseModel):
    name: str
    ok: bool
    output: Any = None
    error: str | None = None
    approval_required: bool = False


class ToolExecutor:
    def __init__(
        self,
        registry: ToolRegistry,
        max_tool_calls: int = 4,
        timeout_seconds: float = 10.0,
        approval_policy: dict[str, str] | None = None,
    ):
        self.registry = registry
        self.max_tool_calls = max_tool_calls
        self.timeout_seconds = timeout_seconds
        self.approval_policy = approval_policy or {}
        self._calls_this_turn = 0

    def reset_turn(self) -> None:
        self._calls_this_turn = 0

    def execute(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        if self._calls_this_turn >= self.max_tool_calls:
            raise ToolExecutionError("Maximum tool calls per turn exceeded.")

        self._calls_this_turn += 1
        if self.approval_policy.get(name) == "always":
            return ToolResult(name=name, ok=False, approval_required=True)

        try:
            spec = self.registry.get(name)
        except KeyError as exc:
            raise ToolExecutionError(f"Unknown tool: {name}") from exc

        if spec.function is None:
            raise ToolExecutionError(f"Tool has no callable function: {name}")

        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(spec.function, **arguments)
        try:
            output = future.result(timeout=self.timeout_seconds)
            return ToolResult(name=name, ok=True, output=output)
        except TimeoutError:
            future.cancel()
            return ToolResult(name=name, ok=False, error="Tool timed out.")
        except Exception:
            logger.exception("Tool execution failed: %s", name)
            return ToolResult(name=name, ok=False, error="Tool execution failed.")
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
