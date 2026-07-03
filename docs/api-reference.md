# API Reference

## Core

### `Expert`

```python
Expert(
    name="support",
    description="Handles support requests.",
    system_prompt=None,
    tools=[],
)
```

`system_prompt` is optional. If omitted, GentisAI creates a simple prompt from the expert name and description.

### `Message`

Internal roles are strictly typed:

- `system`
- `user`
- `assistant`
- `tool`

Legacy `model` input is normalized to `assistant` for compatibility.

### `Router`

```python
decision = router.classify("I need pricing help", "orchestrator")
names = router.classify_names("I need pricing help", "orchestrator")
```

`classify()` returns `RoutingDecision`:

```python
class RoutingDecision:
    experts: list[str]
    mode: Literal["single", "hybrid", "fallback"]
    confidence: float
    reason: str
```

### `Flow`

```python
response = flow.process_turn("hello", session_id="user-1")

for event in flow.stream_turn("hello", session_id="user-1"):
    ...

response = await flow.aprocess_turn("hello", session_id="user-1")

async for event in flow.astream_turn("hello", session_id="user-1"):
    ...
```

## Memory

```python
from gentis_ai import InMemorySessionStore, SQLiteSessionStore

memory = InMemorySessionStore(ttl_seconds=3600)
sqlite = SQLiteSessionStore("gentis.db")
```

## Providers

All adapters implement `BaseLLM.generate`, `BaseLLM.generate_response`, `BaseLLM.get_token_usage`, and `BaseLLM.count_tokens`.

```python
from gentis_ai.llm import ProviderResponse
```

`ProviderResponse` includes:

- `text`
- `usage`
- `raw_response`
- `tool_calls`
- `finish_reason`

## Tools

```python
from gentis_ai.tools import ToolExecutor, ToolRegistry, ToolSpec
```

`ToolSpec.from_function(fn)` builds a JSON schema from a Python function signature. `ToolExecutor` supports max calls, timeouts, safe error results, and approval policies.
