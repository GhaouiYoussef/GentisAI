# GentisAI

GentisAI is a small Python package for building multi-expert AI agent POCs with a simple mental model:

`Expert + Router + Flow`

It is designed for interactive chat, support, sales, copilots, and other workflows where routing should be explicit, fast, and easy to test. GentisAI keeps low orchestration overhead by avoiding hidden manager loops, while still leaving an optional bridge to LangGraph for durable workflows.

## Install

```bash
pip install gentis-ai
```

The default install only includes the tiny core and `pydantic`. Provider SDKs are optional:

```bash
pip install "gentis-ai[gemini]"
pip install "gentis-ai[openai]"
pip install "gentis-ai[ollama]"
pip install "gentis-ai[langgraph]"
```

## Quick Start

This example runs offline with no API key.

```python
from gentis_ai import Expert, Flow, Router
from gentis_ai.llm import MockLLM

llm = MockLLM(
    routing_rules={
        "help": "support",
        "buy": "sales",
    },
    responses={
        "help": "I can help troubleshoot that issue.",
        "buy": "I can walk you through plans and pricing.",
    },
    default_response="I can route that to the right expert.",
)

support = Expert(name="support", description="Handles technical support.")
sales = Expert(name="sales", description="Handles sales and pricing.")

router = Router(experts=[support, sales], llm=llm)
flow = Flow(router=router, llm=llm)

response = flow.process_turn(
    "I need help with my account.",
    session_id="demo-user",
)

print(response.agent_name)
print(response.content)
```

## Core Concepts

- `Expert`: a persona with a name, description, optional system prompt, and optional tools.
- `Router`: selects one or more experts and returns a validated `RoutingDecision`.
- `Flow`: manages routing, session history, expert execution, streaming events, and responses.
- `SessionStore`: stores state in memory or SQLite.
- `BaseLLM`: provider-neutral interface for mock, Gemini, Ollama, Bedrock, and OpenAI-compatible adapters.

## Structured Routing

`Router.classify()` returns a `RoutingDecision`:

```python
decision = router.classify("I want pricing help", "orchestrator")
print(decision.experts)
print(decision.confidence)
```

Older code can use `router.classify_names(...)` to get a `list[str]`.

For zero-LLM routing, pass deterministic rules:

```python
router = Router(
    experts=[support, sales],
    llm=None,
    rules={"help": "support", "buy": "sales"},
)
```

## Sessions

Use explicit `session_id` values in production so users do not share state:

```python
response = flow.process_turn("hello", session_id="customer-123")
```

SQLite persistence is built in:

```python
from gentis_ai import SQLiteSessionStore

flow = Flow(
    router=router,
    llm=llm,
    session_store=SQLiteSessionStore("gentis.db"),
)
```

Anonymous calls are allowed, but each call receives a fresh anonymous session.

## Streaming

Core runtime does not print. Use `stream_turn()` and decide how your app displays events:

```python
for event in flow.stream_turn("Tell me a story", session_id="demo"):
    if event.type == "token":
        print(event.content, end="", flush=True)
    elif event.type == "final":
        print()
```

Async variants are available:

```python
response = await flow.aprocess_turn("hello", session_id="demo")

async for event in flow.astream_turn("hello", session_id="demo"):
    ...
```

## Providers

All provider adapters implement the same `BaseLLM` contract.

```python
from gentis_ai.llm import OpenAICompatibleLLM

llm = OpenAICompatibleLLM(
    model_name="gpt-4o-mini",
    api_key="...",
    base_url="https://api.openai.com/v1",
)
```

Helpful extras:

- Gemini: `pip install "gentis-ai[gemini]"`
- OpenAI-compatible and Azure: `pip install "gentis-ai[openai]"`
- AWS Bedrock: `pip install "gentis-ai[bedrock]"`
- Ollama: `pip install "gentis-ai[ollama]"`
- LangGraph bridge: `pip install "gentis-ai[langgraph]"`

See `examples/cloud_providers_example.py` for provider selection by environment variable.

## Tools

GentisAI includes reusable tool schema, registry, and executor primitives:

```python
from gentis_ai.tools import ToolExecutor, ToolRegistry

def add(a: int, b: int) -> int:
    return a + b

registry = ToolRegistry()
registry.register(add)

executor = ToolExecutor(registry, approval_policy={"delete_file": "always"})
result = executor.execute("add", {"a": 2, "b": 3})
```

## LangGraph Bridge

GentisAI stays simple by default. Use LangGraph when you need checkpointed, durable, multi-node workflows:

```python
from gentis_ai.adapters.langgraph import to_langgraph

graph = to_langgraph(flow)
```

`import gentis_ai` never imports LangGraph.

## CLI

```bash
gentis new support-agent
gentis new support-agent --azure
gentis new support-agent --google
gentis agent add billing --project support-agent
gentis run
gentis eval
gentis bench
```

`gentis new` now scaffolds a multi-agent project system with a project manifest, provider-specific wiring, editable expert prompts, optional tool placeholders, and an optional fast router scaffold. `gentis agent add` adds a new expert to an existing project and rewrites the router rules so the fast router stays in sync.

The starter includes support and sales prompt examples so users can see the shape of each expert prompt immediately.

## Documentation And Examples

- `docs/getting-started.md`
- `docs/api-reference.md`
- `docs/features/streaming.md`
- `examples/quick_mock_start.py`
- `examples/cloud_providers_example.py`
- `benchmarks/README_comparison.md`

## Development

```bash
pip install -e ".[dev]"
python -m pytest
```

## License

MIT. See `LICENSE`.
