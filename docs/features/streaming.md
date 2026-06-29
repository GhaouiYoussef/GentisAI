# Streaming

GentisAI streams structured events. Core runtime does not print.

```python
for event in flow.stream_turn("Tell me a story", session_id="user-1"):
    if event.type == "token":
        print(event.content, end="", flush=True)
    elif event.type == "final":
        print()
```

Event types:

- `route_started`
- `route_finished`
- `expert_started`
- `token`
- `tool_call`
- `tool_result`
- `final`
- `error`

Async streaming:

```python
async for event in flow.astream_turn("Tell me a story", session_id="user-1"):
    ...
```
