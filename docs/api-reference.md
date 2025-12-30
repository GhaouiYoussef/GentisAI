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
