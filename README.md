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

Create a Gemini-backed customer-support project:

```bash
gentis new customer-support-gemini --template gemini-support
cd customer-support-gemini
gentis run
```

Set `GOOGLE_API_KEY` or `GEMINI_API_KEY` in a project `.env` file or the shell before running it.

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
gentis run
gentis eval
gentis bench
```

### Azure Customer Support POC

Create a three-agent customer-support demo in four commands:

```bash
pip install "gentis-ai[azure]"
gentis new customer-support --template azure-support
cd customer-support
gentis run
```

The POC routes each message to Technical, Billing, or Account Support. If the
Azure API key, endpoint, and deployment are not all configured, it clearly
announces the local mock fallback and still runs.

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

## Launch Demos

The demos below use the 0.2.1 source checkout. Install from the repository root
with `python -m pip install -e ".[openai]"` and
`python -m pip install "streamlit>=1.36,<2"` before running them.
The published PyPI release may lag this checkout; installing `gentis-ai` alone
does not install the demo source files.

- `demos/customer_rescue` shows explicit hybrid routing, fictional tool execution, streaming, and session follow-ups.
- `demos/launch_war_room` shows contextual product-expert routing and parallel synthesis.
- Both demos support `GENTIS_PROVIDER=mock|openai|gemini|azure`; mock remains the default.

```bash
python -m streamlit run demos/customer_rescue/app.py
python -m streamlit run demos/launch_war_room/app.py
```

Mock mode uses scripted routes and answers, including follow-ups. It demonstrates
runtime events and stored history; use a real provider to evaluate contextual
understanding. Customer tools use fictional data and fixed demo account references.

## Azure Configuration

Create a `.env` file with one plain-text assignment per line (URLs must not use
Markdown link syntax):

```dotenv
GENTIS_PROVIDER=azure
AzureOpenAIKey=your-real-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5.4-mini
AZURE_OPENAI_API_VERSION=2025-04-01-preview
```

The app reads `.env` from the working directory, then its own directory. The
app-local file overrides working-directory values; shell variables override both.
Restart the app after changing configuration because the demo caches its provider.

`AZURE_OPENAI_API_KEY` also accepts `AzureOpenAIKey`; `AZURE_OPENAI_ENDPOINT`
also accepts `AzureOpenAIEndpoint`. Deployment aliases are
`AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_DEPLOYMENT_NAME`, and `AZURE_OPENAI_MODEL`
(in that order). Canonical names win within one source; shell aliases still
win over file values. A full deployment chat-completions URL is accepted and its
deployment and `api-version` are extracted when not explicitly configured.

With an API version configured, the adapter uses the versioned Azure SDK client.
Without one, it retains the `/openai/v1` API. Azure token budgets use
`max_completion_tokens`, including routing requests.

See `demos/customer_rescue/README.md` for the demo run command.

## Deployment Boundaries

GentisAI is an early-stage orchestration library. Applications own authentication,
tenant authorization, sensitive-data handling, and access to session IDs and tool
outputs. Tool results are included in model context and structured responses.
The framework does not provide healthcare compliance or general PHI sanitization.

`configure_logging()` masks UUIDs, email addresses, and Bearer tokens in formatted
messages and tracebacks. This is limited redaction, not a guarantee that arbitrary
secrets or personal data are removed. Custom log handlers need their own policy.
Tool failures return a generic message, with diagnostics logged internally.

## License

MIT. See `LICENSE`.
