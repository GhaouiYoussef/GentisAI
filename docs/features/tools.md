# Tools

GentisAI provides reusable tool primitives.

```python
from gentis_ai.tools import ToolExecutor, ToolRegistry

def get_weather(city: str) -> str:
    return "Sunny"

registry = ToolRegistry()
registry.register(get_weather)

executor = ToolExecutor(
    registry,
    max_tool_calls=4,
    timeout_seconds=10,
    approval_policy={"delete_file": "always"},
)

result = executor.execute("get_weather", {"city": "Paris"})
```

Tool errors return safe `ToolResult` objects. Unknown tools and max-call violations raise `ToolExecutionError`.
