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
