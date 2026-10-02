# GentisAI

GentisAI is a small Python package for building multi-expert AI agent POCs with a simple mental model:

`Expert + Router + Flow`

It is designed for interactive chat, support, sales, copilots, and other workflows where routing should be explicit, fast, and easy to test. GentisAI keeps low orchestration overhead by avoiding hidden manager loops, while still leaving an optional bridge to LangGraph for durable workflows.

## Try The Demo First

Python 3.10+ is required. No repository clone or API key is needed:

```bash
python -m pip install --upgrade "gentis-ai[demo]>=0.2.2"
gentis demo
```

The browser opens the **Customer Rescue Command Center**. Click **Customer rescue**, then **Session follow-up** to see expert routing, fictional tools, streaming, and conversation history. Mock mode uses scripted answers; connect a provider to evaluate real language understanding. Stop the server with `Ctrl+C`.

Try the second bundled demo:

```bash
gentis demo launch-war-room
```

Already installed `gentis-ai`? Install the `demo` extra with the command above. If `gentis` is not on your PATH, use `python -m gentis_ai demo`. For a busy port, use `gentis demo --port 8502`.

These commands require the 0.2.2 release built from this source. Until it is published, an older PyPI version will not include them. Maintainers can test the built wheel using the instructions under Development.

### Make A Demo Your Own

Copy the complete demo into an editable local project:

```bash
gentis demo customer-rescue --export my-rescue-demo
cd my-rescue-demo
gentis run
```

Use `launch-war-room` to export the other demo. Each export includes the Streamlit app, local agent setup, tools where used, telemetry, tests, requirements, a README, and `.env.example`. Edit `app.py` for the interface and `demo_app/` for the behavior; the exported app imports your local copies. The destination must be new or empty. `gentis run` opens the exported demo in Streamlit; `--port 8502` and `--headless` are available.

## Connect Your Provider

Run these commands from the folder where you want to keep your configuration. Choose one provider:

| Provider | Install | Configure |
| --- | --- | --- |
| Azure OpenAI | `python -m pip install "gentis-ai[demo,azure]>=0.2.2"` | `gentis configure --provider azure` |
| OpenAI / compatible API | `python -m pip install "gentis-ai[demo,openai]>=0.2.2"` | `gentis configure --provider openai` |
| Google Gemini | `python -m pip install "gentis-ai[demo,gemini]>=0.2.2"` | `gentis configure --provider gemini` |
| AWS Bedrock | `python -m pip install "gentis-ai[demo,bedrock]>=0.2.2"` | `gentis configure --provider bedrock` |

The setup command prompts for the required values, hides API keys as you type, validates settings, and creates a new `.env` in the current directory. It also provides a secret-free `.env.example`. If `.env` already exists, setup preserves it, skips the prompts, and still creates the example if missing. Existing examples are preserved too. With `--output settings.txt`, the example is `settings.txt.example`. Then run:

```bash
gentis doctor
gentis demo
```

`doctor` checks local configuration and SDK installation without spending API credits. It cannot verify credentials, model access, network connectivity, or quotas. The first live message uses your provider account.

For Azure, enter the deployment name from your Azure resource. Use a plain endpoint URL such as `https://your-resource.openai.azure.com/`. Leave the API version blank for the v1 API, or supply the version required by your deployment. For Bedrock, configure credentials using the AWS SDK credential chain (for example, `aws configure` or an authenticated `AWS_PROFILE`); enter a region and a Converse-compatible model or inference-profile ID available to your account.

Prefer editing configuration yourself? Create `.env` in the directory where you run the CLI. For example:

```dotenv
GENTIS_PROVIDER=azure
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
```

Keep `.env` out of version control. Shell variables override file values; `gentis demo --provider mock` overrides provider selection for that launch. Restart the demo after changes. Files inside the installed package are never needed for configuration.

Token limits and timeouts have defaults, so you do not need SDK parameter names to get started:

| Setting | Default | Purpose |
| --- | --- | --- |
| `GENTIS_MAX_TOKENS` | `4096` | Per-response generation budget |
| `GENTIS_ROUTING_MAX_TOKENS` | `1024` | Router generation budget |
| `GENTIS_TIMEOUT` | `45` | Request timeout in seconds; SDK retries can add time |

OpenAI and Azure use `max_completion_tokens`; Gemini uses `max_output_tokens`; Bedrock uses `maxTokens`. Router calls use the same translation. No temperature is forced. For a third-party OpenAI-compatible endpoint that requires the older parameter, set `GENTIS_TOKEN_PARAMETER=max_tokens`. This override applies only to the OpenAI-compatible provider. Reasoning tokens share the OpenAI/Azure completion budget; increase the relevant budget if a response or routing result is cut off. See the [OpenAI parameter reference](https://developers.openai.com/api/reference/python/resources/chat/subresources/completions/methods/create).

## Build Your Own Agent

Create a project with separate agents, tools, prompts, and a Streamlit chat app:

```bash
gentis init my-agent
cd my-agent
gentis add agent billing --description "Handles invoices and refunds"
gentis add tool lookup_invoice --agent billing
gentis run --ui
```

Already in your project folder? Run `gentis init` there. Existing configuration and unrelated files are preserved; conflicting source files are reported before generation. `gentis new my-agent --template streamlit` creates the same starter in a new or empty directory. These new scaffolding and export commands require a build containing this change.

```text
my-agent/
  agents/             Agent definitions, one Python file per agent
  tools/              Tool functions, one Python file per tool
  prompts/            Editable system prompts
  project.py          Shared build_flow() for terminal and web apps
  app.py              Terminal chat
  streamlit_app.py    Streamlit chat with a separate session per browser
  gentis.json         Registered agents, tools, and app entrypoints
  .env.example        Configuration placeholders, safe to share
```

Both add commands register the new component automatically. Edit the generated prompt and tool function, then restart the app to load changes. Starter tools accept `query: str` and run before the selected agent answers, supplying read-only context. Their placeholder output makes unfinished implementations clear. The starter runs offline with mock responses; connect a provider to route natural language by agent descriptions. Use `gentis run` for terminal chat.

To connect your existing Streamlit app, import `build_flow` from the generated `project.py`, keep the flow in `st.session_state`, and call `flow.process_turn(message, session_id=...)` with a unique session ID for each user. `streamlit_app.py` provides a working example. Set the `ui` field in `gentis.json` to your app's relative path to launch it with `gentis run --ui`.

To enable a real provider, install its extra and run `gentis configure --provider azure` (or `openai`, `gemini`, `bedrock`) **inside the project**, followed by `gentis doctor`. The same configuration powers demos and starters. For the original single-file terminal starter, use `gentis new my-agent --template support`. The add commands apply to modular projects created with `init` or the `streamlit` template; exported demos keep their original demo layout for direct editing.

## Core Install

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

For a provider-specific Gemini customer-support template:

```bash
python -m pip install "gentis-ai[gemini]"
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
gentis demo
gentis demo customer-rescue --export my-rescue-demo
gentis configure --provider azure
gentis doctor
gentis init support-agent
cd support-agent
gentis add agent billing --description "Handles invoices and refunds"
gentis add tool lookup_invoice --agent billing
gentis run --ui
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
python -m pip install -e ".[dev]"
python -m pytest tests demos
python -m build
python scripts/check_wheel.py dist/gentis_ai-0.2.2-py3-none-any.whl
```

The wheel check creates a temporary virtual environment, reuses installed test dependencies, installs the built wheel, and exercises both demos and a generated agent outside the checkout. To try it manually, install `dist/gentis_ai-0.2.2-py3-none-any.whl[demo]` into a clean virtual environment, change to a directory outside the checkout, and run `gentis demo --provider mock`.

## Launch Demos

- [Customer Rescue](demos/customer_rescue/README.md): hybrid routing, fictional tools, streaming, and session follow-ups. Run `gentis demo`.
- [Launch War Room](demos/launch_war_room/README.md): contextual product experts and parallel synthesis. Run `gentis demo launch-war-room`.

Both use `GENTIS_PROVIDER=mock|openai|azure|gemini|bedrock`. Mock is the default. Customer tools use fictional data and fixed demo account references.

When upgrading from the source-only demos, put your configuration in the directory where you launch `gentis demo`. App-local configuration beside the old demo scripts is no longer loaded.

Azure accepts `AzureOpenAIKey`, `AzureOpenAIEndpoint`, `AZURE_OPENAI_DEPLOYMENT_NAME`, and `AZURE_OPENAI_MODEL` as aliases. Canonical names win within one source; shell aliases still override file values. A full deployment chat-completions URL is accepted, with deployment and API version extracted when not explicitly set. `GEMINI_API_KEY` is an alias for `GOOGLE_API_KEY`.

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
