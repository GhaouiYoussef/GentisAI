import time
import unittest

from gentis_ai.tools import ToolExecutor, ToolRegistry, ToolSpec
from gentis_ai.core.errors import ToolExecutionError


def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


def explode() -> str:
    raise RuntimeError("boom")


def wait() -> str:
    time.sleep(0.2)
    return "done"


class TestTools(unittest.TestCase):
    def test_tool_spec_from_function(self):
        spec = ToolSpec.from_function(add)
        self.assertEqual(spec.name, "add")
        self.assertEqual(spec.parameters["properties"]["a"]["type"], "integer")
        self.assertIn("a", spec.parameters["required"])

    def test_execute_valid_tool(self):
        registry = ToolRegistry()
        registry.register(add)
        executor = ToolExecutor(registry)
        result = executor.execute("add", {"a": 2, "b": 3})
        self.assertTrue(result.ok)
        self.assertEqual(result.output, 5)

    def test_invalid_tool_name_raises(self):
        executor = ToolExecutor(ToolRegistry())
        with self.assertRaises(ToolExecutionError):
            executor.execute("missing", {})

    def test_tool_exception_returns_safe_result(self):
        registry = ToolRegistry()
        registry.register(explode)
        result = ToolExecutor(registry).execute("explode", {})
        self.assertFalse(result.ok)
        self.assertEqual(result.error, "boom")

    def test_tool_timeout_returns_safe_result(self):
        registry = ToolRegistry()
        registry.register(wait)
        result = ToolExecutor(registry, timeout_seconds=0.01).execute("wait", {})
        self.assertFalse(result.ok)
        self.assertEqual(result.error, "Tool timed out.")

    def test_approval_required(self):
        registry = ToolRegistry()
        registry.register(add)
        result = ToolExecutor(
            registry,
            approval_policy={"add": "always"},
        ).execute("add", {"a": 1, "b": 1})
        self.assertTrue(result.approval_required)


if __name__ == "__main__":
    unittest.main()
