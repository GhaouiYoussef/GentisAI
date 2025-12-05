# AghenticMinds

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Status](https://img.shields.io/badge/status-beta-orange)

A lightweight library for multi-persona AI agent routing and state management.

## Why AghenticMinds?

Building multi-agent systems often involves complex frameworks that are hard to debug and heavy to deploy. **AghenticMinds** is designed to be the opposite:
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

## Story & Motivation

AghenticMinds exists to make multi-agent development *ridiculously fast*.  
Most agent frameworks either (a) force you to architect and wire everything from scratch, or (b) dump a huge, opinionated stack on your desk. AghenticMinds intentionally sits between: a tiny, composable routing + state layer that lets you assemble expert agents in minutes — but also provides the primitives you need to build robust production flows later.

We care about two developer problems:
1. **Speed of iteration** — get a working multi-expert agent in < 5 minutes.  
2. **Reasonable robustness** — sensible routing, context pruning, and performance trade-offs without the heavy lifting of full orchestration stacks.

## Robust routing — design trade-offs (latency vs multi-agent accuracy)

Routing in multi-agent systems is a trade-off between **latency** and **routing accuracy / specialization**. AghenticMinds uses a pragmatic approach that balances both:

- **Context-Aware LLM Routing**: Instead of brittle keyword heuristics, we use a lightweight LLM call to classify intent based on the most recent conversation history. This ensures high accuracy even for complex queries.
- **Orchestrator-Guided Flow**: The Orchestrator acts as an intelligent internal helper, maintaining context and guiding the user to the correct expert only when necessary, preventing jarring context switches.
- **Optimized Context Window**: By routing based on a "sliding window" of recent history rather than the full conversation log, we keep latency low and token costs manageable without sacrificing the ability to understand immediate intent.

This strategy lets you scale agent count while keeping the system responsive and accurate.

## How AghenticMinds differs from existing solutions

- **Not a heavy orchestration platform** (e.g., compared to LangChain/CrewAI): AghenticMinds is intentionally a thin routing + state layer built for speed of development and pragmatic production readiness. It’s not trying to reimplement a whole pipeline ecosystem in v0.x.

- **Smaller surface area than “full agent frameworks”:** We trade off some advanced orchestration primitives early-on for better DX, smaller installs, and faster iteration cycles.

- **Context-Aware Routing:** Many libraries rely on rigid keywords or heavy embedding databases. AghenticMinds uses a lightweight LLM classifier on the recent conversation window, ensuring accurate routing without the operational complexity.

- **Designed for incremental adoption:** Start with simple keyword or persona-based flows; progressively enable embedding routing, tools, and storage as the product matures — you don’t need to rewrite the app to scale.

## How it Works

```mermaid
graph TD
    User([User]) -->|Message| Flow[Flow Engine]
    
    subgraph "AghenticMinds Core"
        Flow -->|1. Check Intent| Router{Router}
        
        Router -->|Match| ExpertA[Expert: Sales]
        Router -->|Match| ExpertB[Expert: Support]
        Router -->|No Match| Orch[Expert: Orchestrator]
        
        ExpertA -->|Context + Tools| LLM[LLM Adapter]
        ExpertB -->|Context + Tools| LLM
        Orch -->|Context + Tools| LLM
    end
    
    LLM -->|Response| Flow
    Flow -->|2. Update State| Memory[(Session State)]
    Flow -->|3. Reply| User
```

## Installation

```bash
pip install aghenticMinds
```

## Quick Start (No API Key Required)

You can test the flow logic immediately using the `MockLLM`.

```python
from aghenticMinds import Expert, Router, Flow
from aghenticMinds.llm import MockLLM

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

To use with a real LLM (e.g., Gemini), simply switch the adapter (check `simple_example.py`):

```python
import os
from aghenticMinds.llm import GeminiLLM

llm = GeminiLLM(model_name="gemini-2.0-flash", api_key=os.getenv("GOOGLE_API_KEY"))
# ... rest is the same
```

## Advanced Examples

For a complex scenario involving an **Orchestrator** that switches "modes" (personas) based on intent, check out `advanced_example.py` in the repository.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


