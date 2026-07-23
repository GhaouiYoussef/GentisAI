# Getting Started

## Installation

GentisAI supports Python 3.10+.

```bash
pip install gentis-ai
```

The minimal install includes only core routing, sessions, tools, and `pydantic`.

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
never prints configured values and does not load `.env` files.

Try these prompts:

```text
I was charged twice this month.
The dashboard crashes when I upload a file.
I cannot sign in to my account.
Can you explain the next step?
```

The first three demonstrate each route. The final prompt demonstrates the
stable CLI session.
