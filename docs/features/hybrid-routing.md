# Hybrid Routing

Hybrid routing lets the router select multiple experts for one request.

```python
router = Router(experts=[math, history, coding], llm=llm, enable_hybrid=True)
```

`Router.classify()` returns:

```python
RoutingDecision(
    experts=["history", "coding"],
    mode="hybrid",
    confidence=0.92,
)
```

`Flow` asks each selected expert for a response, then uses the default expert to synthesize one final answer. Set `parallel_execution=True` to consult selected experts concurrently.

```python
flow = Flow(router=router, llm=llm, parallel_execution=True)
```

`stream_turn()` emits `expert_started` for each consulted expert and streams
the default expert's final synthesis as `token` events. Intermediate expert
responses remain internal to the synthesis step.

To force one expert:

```python
router = Router(experts=[support, sales], llm=llm, enable_hybrid=False)
```
