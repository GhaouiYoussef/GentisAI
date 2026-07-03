# Parallel Execution

When a route selects multiple experts, `Flow` can call them concurrently.

```python
flow = Flow(router=router, llm=llm, parallel_execution=True)
```

This helps most when provider calls are remote and independent. Local model servers may still serialize requests depending on their runtime settings.

Parallel execution is only used for hybrid routes. Single-expert turns remain direct.
