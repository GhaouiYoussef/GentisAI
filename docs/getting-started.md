# Getting Started

## Installation

GentisAI requires Python 3.11+.

```bash
pip install gentis-ai
```

Or install from source:

```bash
git clone https://github.com/GhaouiYoussef/GentisAI.git
cd GentisAI
pip install -e .
```

## Basic Usage

Here is a simple example of how to set up a router with two experts.

```python
from gentis_ai.session import Flow
from gentis_ai.router import Router
from gentis_ai.types import Expert
from gentis_ai.llm.ollama import OllamaLLM

# 1. Setup LLM
llm = OllamaLLM(model_name="llama3")

# 2. Define Experts
sales_expert = Expert(
    name="sales",
    description="Handles product inquiries and sales.",
    system_prompt="You are a sales assistant. Be persuasive and helpful."
)

support_expert = Expert(
    name="support",
    description="Handles technical issues and bugs.",
    system_prompt="You are a technical support engineer. Be patient and precise."
)

# 3. Initialize Router and Flow
router = Router(experts=[sales_expert, support_expert], llm=llm)
flow = Flow(router=router, llm=llm)

# 4. Chat Loop
response = flow.process_turn("I want to buy a laptop", user_id="user1")
print(f"Agent: {response.agent_name}")
print(f"Response: {response.content}")
```
