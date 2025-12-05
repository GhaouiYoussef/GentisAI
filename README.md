# AgenticMinds

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Status](https://img.shields.io/badge/status-beta-orange)

A lightweight library for multi-persona AI agent routing and state management.

## Why AgenticMinds?

Building multi-agent systems often involves complex frameworks that are hard to debug and heavy to deploy. **AgenticMinds** is designed to be the opposite:
*   **Simple**: Minimal abstraction overhead.
*   **Flexible**: Define experts as simple Python objects.
*   **Transparent**: Full visibility into routing and state.
*   **Lightweight**: Perfect for embedding into existing applications.

## Features (v0.1)

*   **Flow**: Simple conversation management.
*   **Expert**: Define agents with specific personas and tools.
*   **Router**: Basic intent routing between experts.
*   **PNNet**: Tiny interface for memory optimization and context management.
*   **LLM Adapter**: Support for Gemini (and easy to extend).

## Installation

```bash
pip install agenticminds
```

## Quick Start (No API Key Required)

You can test the flow logic immediately using the `MockLLM`.

```python
from agenticminds import Expert, Router, Flow
from agenticminds.llm import MockLLM

# 1. Setup Mock LLM with routing rules
llm = MockLLM(
    responses={"help": "I can help you!", "buy": "Great choice!"},
    routing_rules={"help": "support", "buy": "sales"},
    default_response="Hello! I am a simulated agent."
)

# 2. Define Experts
support = Expert(name="support", description="Technical help", system_prompt="...")
sales = Expert(name="sales", description="Sales help", system_prompt="...")

# 3. Create Flow
router = Router(experts=[support, sales], llm=llm)
flow = Flow(router=router, llm=llm)

# 4. Run
response = flow.process_turn("I need help")
print(f"Agent: {response.agent_name}") # Output: support
print(f"Response: {response.content}")
```

## Real-World Usage

To use with a real LLM (e.g., Gemini), simply switch the adapter:

```python
import os
from agenticminds.llm import GeminiLLM

llm = GeminiLLM(model_name="gemini-2.0-flash", api_key=os.getenv("GOOGLE_API_KEY"))
# ... rest is the same
```

## Advanced Examples

For a complex scenario involving an **Orchestrator** that switches "modes" (personas) based on intent, check out `advanced_example.py` in the repository.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


