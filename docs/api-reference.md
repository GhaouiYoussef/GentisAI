# API Reference

## Core Classes

### `gentis_ai.session.Flow`

The main entry point for managing a chat session.

```python
class Flow:
    def __init__(self, router: Router, llm: BaseLLM, debug: bool = False, optimize: bool = False, parallel_execution: bool = False):
        ...

    def process_turn(self, message: str, user_id: Optional[str] = None, stream: bool = False) -> TurnResponse:
        ...
```

### `gentis_ai.router.Router`

Handles intent classification and expert selection.

```python
class Router:
    def __init__(self, experts: List[Expert], llm: BaseLLM, default_expert: Optional[Expert] = None, enable_hybrid: bool = True):
        ...

    def classify(self, user_message: str, current_expert_name: str, recent_history: List[str] = None) -> List[str]:
        ...
```

### `gentis_ai.types.Expert`

Defines a persona or domain expert.

```python
class Expert(BaseModel):
    name: str
    description: str
    system_prompt: str
    tools: Optional[List[Any]] = None
```

## LLM Adapters

All adapters implement `BaseLLM.generate`, `BaseLLM.get_token_usage`, and `BaseLLM.count_tokens`.

### `gentis_ai.llm.AzureOpenAILLM`

Uses Azure OpenAI through the OpenAI-compatible chat completions API. `model_name` is the Azure deployment name.

```python
AzureOpenAILLM(
    model_name="my-azure-deployment",
    azure_endpoint="https://my-resource.openai.azure.com",
    api_key="...",
)
```

Environment variables: `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT`.

### `gentis_ai.llm.BedrockLLM`

Uses AWS Bedrock Runtime's Converse API.

```python
BedrockLLM(
    model_name="us.amazon.nova-lite-v1:0",
    region_name="us-east-1",
)
```

Environment variables: `AWS_BEDROCK_MODEL_ID`, `AWS_REGION`, `AWS_DEFAULT_REGION`.

### `gentis_ai.llm.OpenAICompatibleLLM`

Uses any endpoint that supports the OpenAI chat completions API.

```python
OpenAICompatibleLLM(
    model_name="gpt-4o-mini",
    api_key="...",
    base_url="https://api.openai.com/v1",
)
```
