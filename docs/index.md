# GentisAI

GentisAI is a lightweight package for multi-expert AI agent routing and state management.

It keeps the core model small:

```text
Expert + Router + Flow
```

Use GentisAI alone for fast interactive POCs. Add provider extras only when you need a real LLM, and add the LangGraph extra only when you need durable graph workflows.

## Why It Exists

Most agent frameworks are optimized for autonomous background work. GentisAI focuses on real-time chat paths where users expect quick, predictable handoffs between known domains.

- Low orchestration overhead
- No hidden manager loop
- Structured routing decisions
- Explicit session IDs
- Offline MockLLM for tests and demos
- Optional provider and LangGraph integrations

## First Run

```python
from gentis_ai import Expert, Flow, Router
from gentis_ai.llm import MockLLM

llm = MockLLM(
    routing_rules={"help": "support"},
    responses={"help": "I can help troubleshoot that."},
)

support = Expert(name="support", description="Handles support.")
router = Router(experts=[support], llm=llm)
flow = Flow(router=router, llm=llm)

print(flow.process_turn("help", session_id="docs").content)
```

## Install

```bash
pip install gentis-ai
```

Provider extras:

```bash
pip install "gentis-ai[gemini]"
pip install "gentis-ai[openai]"
pip install "gentis-ai[ollama]"
pip install "gentis-ai[langgraph]"
```
