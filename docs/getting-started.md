# Getting Started

## Run The Demo

Use Python 3.10+ and GentisAI 0.2.31 or newer. No clone or API key is required:

```bash
python -m pip install --upgrade "gentis-ai[demo]>=0.2.31"
gentis demo
```

Click **Customer rescue**, then **Session follow-up**. For the launch planning demo, run `gentis demo launch-war-room`. Mock mode uses scripted answers. Use `python -m gentis_ai demo` if the console command is not on PATH.

To import a demo's full editable folder structure, use:

```bash
gentis demo customer-rescue --export my-demo
cd my-demo
gentis run
```

Use `launch-war-room` for the other demo. The exported project includes `app.py`, local `demo_app/` helpers and tools, tests, requirements, a README, and `.env.example`. Your app uses these local files, so edits change the running demo. Export requires a new or empty destination. `gentis run --port 8502 --headless` changes the port and disables automatic browser opening. Export and modular scaffolding require a build containing these commands.

## Connect A Provider

Choose the matching extra and provider name: `azure`, `openai`, `gemini`, or `bedrock`. For example:

```bash
python -m pip install "gentis-ai[demo,azure]>=0.2.31"
gentis configure --provider azure
gentis doctor
gentis demo
```

Setup prompts for settings and creates a new working-directory `.env` plus a secret-free `.env.example`. If `.env` exists, setup preserves it, skips prompts, and supplies the example if missing. Existing examples are never overwritten. A custom `--output settings.txt` gets `settings.txt.example`. API keys are hidden while typing. Shell values override file values. Restart after changing configuration. `doctor` checks settings and SDKs locally; it does not validate account access or send an API request.

Azure needs a key, resource endpoint, and deployment name. API version is optional for v1. OpenAI needs a key; model and compatible base URL are optional. Gemini needs a Google API key. Bedrock needs a region and model/inference-profile ID plus credentials configured through the standard AWS SDK chain.

Budgets default to `GENTIS_MAX_TOKENS=4096` and `GENTIS_ROUTING_MAX_TOKENS=1024`; `GENTIS_TIMEOUT=45` sets the request timeout in seconds. Provider-specific token names are translated, including router calls. For older OpenAI-compatible APIs, set `GENTIS_TOKEN_PARAMETER=max_tokens`. Reasoning models may need a larger completion budget. Keep `.env` out of version control.

## Build An Agent

```bash
gentis init my-agent
cd my-agent
gentis add agent billing --description "Handles invoices and refunds"
gentis add tool lookup_invoice --agent billing
gentis run --ui
```

Use `gentis init` without a directory to scaffold in the current folder. It keeps existing configuration and unrelated files; source conflicts stop generation before anything is written. `gentis new my-agent --template streamlit` generates the same starter in a new or empty directory.

| File or folder | What you customize |
| --- | --- |
| `agents/` | One agent definition per Python file |
| `prompts/` | Each agent's system prompt |
| `tools/` | Read-only context functions, accepting `query: str` |
| `gentis.json` | Agent and tool registration, terminal and UI entrypoints |
| `project.py` | Shared `build_flow()` for your apps |
| `streamlit_app.py` | Chat UI with independent browser sessions |
| `app.py` | Terminal chat |

The add commands create files and update registration automatically. Edit the new prompt and tool implementation, then restart the app. Attached tools run for the selected agent before it generates an answer; implement read-only context retrieval in these functions. Mock mode provides an offline smoke test. Configure a real provider inside the project for natural-language routing by agent description. `gentis run` starts terminal chat, while `gentis run --ui` launches Streamlit. Install `gentis-ai[demo]` if Streamlit is missing.

To use an existing Streamlit application, import `build_flow` from `project.py`. Store it in `st.session_state` and call `flow.process_turn(message, session_id=...)` with a unique ID for each user. The generated `streamlit_app.py` is a complete example; set `gentis.json`'s `ui` field to your own relative app path when ready.

The original single-file starter remains available as `gentis new my-agent --template support`. Add commands require the modular `init`/`streamlit` structure. Exported demos retain their demo-specific setup and tools for direct editing. The minimal library-only install remains `python -m pip install gentis-ai`.

## Offline Quickstart

```python
from gentis_ai import Expert, Flow, Router
from gentis_ai.llm import MockLLM

llm = MockLLM(
    routing_rules={"help": "support", "buy": "sales"},
    responses={
        "help": "I can help troubleshoot that.",
        "buy": "I can help with pricing.",
    },
)

support = Expert(name="support", description="Handles technical support.")
sales = Expert(name="sales", description="Handles sales and pricing.")

router = Router(experts=[support, sales], llm=llm)
flow = Flow(router=router, llm=llm)

response = flow.process_turn("I need help with login.", session_id="user-1")
print(response.agent_name)
print(response.content)
```

## Cloud Providers

Install the extra for the provider you want.

```bash
pip install "gentis-ai[openai]"
```

```python
from gentis_ai.llm import OpenAICompatibleLLM

llm = OpenAICompatibleLLM(
    model_name="gpt-4o-mini",
    api_key="...",
    base_url="https://api.openai.com/v1",
)
```

Other adapters:

- `GeminiLLM`: `pip install "gentis-ai[gemini]"`
- `AzureOpenAILLM`: `pip install "gentis-ai[azure]"`
- `BedrockLLM`: `pip install "gentis-ai[bedrock]"`
- `OllamaLLM`: `pip install "gentis-ai[ollama]"`
- `VLLMLLM`: `pip install "gentis-ai[vllm]"`

See `examples/cloud_providers_example.py`.

## Sessions

Always pass a `session_id` in production:

```python
flow.process_turn("hello", session_id="customer-123")
```

For durable local storage:

```python
from gentis_ai import SQLiteSessionStore

flow = Flow(router=router, llm=llm, session_store=SQLiteSessionStore("gentis.db"))
```

## Azure Customer Support POC

```bash
pip install "gentis-ai[azure]"
gentis new customer-support --template azure-support
cd customer-support
gentis run
```

The generated project contains three agents:

- `technical_support` for errors, outages, uploads, and troubleshooting.
- `billing_support` for invoices, charges, refunds, and payments.
- `account_support` for login, access, profile, and fallback questions.

The router performs one compact semantic classification with a 96-token output
budget, hybrid routing disabled, and only the selected agent invoked. The CLI
prints the actual time between `route_started` and `route_finished`; it does not
claim a fixed latency.

Run immediately without credentials to use the announced local mock. To use
Azure OpenAI, set:

```text
AZURE_OPENAI_API_KEY
AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_BASE_URL
AZURE_OPENAI_DEPLOYMENT or AZURE_OPENAI_MODEL
```

The deployment variable must identify an Azure deployment. The application
never prints configured values and loads the working-directory `.env` with shell values taking precedence.

Try these prompts:

```text
I was charged twice this month.
The dashboard crashes when I upload a file.
I cannot sign in to my account.
Can you explain the next step?
```

The first three demonstrate each route. The final prompt demonstrates the
stable CLI session.
