# LangGraph Bridge

GentisAI does not require LangGraph. Use LangGraph when you need durable graph execution, checkpointing, or composition with existing graph nodes.

Install:

```bash
pip install "gentis-ai[langgraph]"
```

Use:

```python
from gentis_ai.adapters.langgraph import to_langgraph

graph = to_langgraph(flow)
result = graph.invoke({"input": "hello", "session_id": "user-1"})
```

The bridge compiles one GentisAI turn into a LangGraph node. Pure GentisAI examples stay smaller and avoid importing LangGraph.
