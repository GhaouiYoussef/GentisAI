
<div align="center">
    <picture>
      <source media="(prefers-color-scheme: light)" srcset=".github/images/GentisAI-B-banner-r.svg">
      <source media="(prefers-color-scheme: dark)" srcset=".github/images/GentisAI-B-banner-r.svg">
      <img alt="GentisAI-B-banner-r" src=".github/images/GentisAI-B-banner-r.svg" width="80%">
    </picture>
</div>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" />
  <img src="https://img.shields.io/badge/python-3.11%2B-blue" />
  <img src="https://img.shields.io/badge/status-beta-orange" />
</p>

<h3 align="center"><i>The lightweight framework for real-time AI agents.</i></h3>

<p align="center">
  Build multi-expert systems with precise routing, zero overhead, and
  <b>6× less token usage than major competitors</b>.
</p>


---

# Why GentisAI?

Traditional agent frameworks (LangChain, CrewAI, AutoGen…) are created for **complex, autonomous, long-running tasks**.
They introduce:

* Heavy orchestration layers
* Hidden “manager” reasoning loops
* Massive prompts
* Slow response times
* High token usage

**GentisAI is built for a different purpose:**

👉 **Create fast, deterministic, conversational AI agents that feel real-time.**

---

## 🔥 The Gentis Advantage

### ⚡ **6× More Efficient**

Our architecture uses **~83% fewer tokens per turn** than CrewAI in benchmarks.

### 🎯 **Precise Expert Routing**

A tiny, dedicated router sends each message to the correct expert
— fast, deterministic, and with no “agent arguing with itself.”

### 🪶 **Minimalist API**

Experts are simple Python classes.
Router is a single object.
Flow is one line.

### 🔍 **Fully Transparent**

No black-box loops.
You control the routing logic, prompts, and state.

### 🛠️ **Production-Ready Structure**

Clean separation of concerns:

* Experts
* Router
* Flow
* Memory
* LLM Adapters

---

# 📊 Benchmark Highlights
### Multi-Context Vs Multi-Agents

GentisAI was compared against a leading framework in a **real 3-turn conversational scenario** requiring expert handoffs.

**Model:** Gemini 2.5 Flash (Dec 2025)

| Metric               | **GentisAI** | **CrewAI** | Difference           |
| -------------------- | ----------------- | ---------- | -------------------- |
| **Total Latency**    | **12.6 s**        | 30.0 s     | **2.4× Faster**      |
| **Total Tokens**     | **3,077**         | 18,521     | **~6× Fewer Tokens** |
| **Avg Latency/Turn** | **4.2 s**         | 10.0 s     | —                    |
| **Avg Tokens/Turn**  | **1,025**         | 6,173      | **~83% Cheaper**     |

> **Why the difference?**
> CrewAI generates **~15,000 extra "manager" tokens** per session to decide which expert should answer.
> GentisAI routes instantly—no wasted reasoning loops.

** **You can reproduce this benchmark by checking the** `benchmarks/` **folder.**

---

## 📈 Benchmark Visualization (Bar Plot)



<img width="1200" height="500" label="Benchmark Comparison" alt="Figure_Comp_MA_MC" src="https://github.com/user-attachments/assets/19f85fbf-7faf-47c1-842a-6588d2b347b4" />


*The image will display latency and token usage differences between GentisAI and CrewAI.*

---

# 💡 Philosophy: Pragmatic Routing & Naming

The name *GentisAI* is inspired by the Latin root $\mathbf{agentis}$ (the genitive form of $\mathbf{agens}$), which means “of the agent” or “the one doing.”

### **Simple things should be simple. Complex things should stay possible.**

We achieve this latency and efficiency trade-off by focusing on three core principles:

### ✔ **Context-Aware Routing**

A tiny LLM classification call over a **recent sliding window**, not the entire history.

### ✔ **No Hidden Reasoning Loops**

Experts respond immediately.
An Orchestrator expert is used only as a fallback.

### ✔ **Sliding-Window Optimization**

Keeps token cost low while preserving high conversational accuracy.

**The result:**

This foundation reflects our core belief: that high-performance AI systems must be built by focusing on the precise actions of the agent—optimizing every step to ensure **speed**, **efficiency (low cost)**, and **deterministic routing**.

---

# 🛠️ How It Works

```mermaid
flowchart TD
    %% Define Styles
    classDef userStyle fill:#e6f7ff,stroke:#007acc,stroke-width:2px;
    classDef flowStyle fill:#fffbe6,stroke:#f7b731,stroke-width:2px;
    classDef memoryStyle fill:#fde0dc,stroke:#ba1a1a,stroke-width:2px;
    classDef expertStyle fill:#e5ffe5,stroke:#36b37e,stroke-width:2px;
    classDef routerStyle fill:#ebedfa,stroke:#7057c6,stroke-width:2px;
    classDef llmStyle fill:#f0f5ff,stroke:#2a62ff,stroke-width:2px;
    classDef orchStyle fill:#fff6e9,stroke:#e67e22,stroke-width:2px;

    %% Main Nodes with Improved Shapes
    User@{ shape: stadium, label: "User" }
    Flow@{ shape: rect, label: "Flow Engine" }
    Memory@{ shape: cyl, label: "Session State" }

    %% Subgraph for GentisAI Core
    subgraph "GentisAI Core"
        Router@{ shape: diamond, label: "Router" }
        ExpertA@{ shape: rect, label: "Expert: Sales" }
        ExpertB@{ shape: rect, label: "Expert: Support" }
        Orch@{ shape: rect, label: "Orchestrator" }
        LLM@{ shape: rect, label: "LLM Adapter" }
    end

    %% Flows
    User -->|Message| Flow
    Flow -->|1. Classify Intent| Router

    Router -->|Sales| ExpertA
    Router -->|Support| ExpertB
    Router -->|Fallback| Orch

    ExpertA --> LLM
    ExpertB --> LLM
    Orch --> LLM
    LLM -->|2. Generated Reply| Flow
    Flow -->|3. Update| Memory
    Flow -->|Return| User

    %% Style the nodes
    class User userStyle;
    class Flow flowStyle;
    class Memory memoryStyle;
    class ExpertA,ExpertB expertStyle;
    class Router routerStyle;
    class Orch orchStyle;
    class LLM llmStyle;
```

# 📦 Installation

```bash
pip install gentis-ai
```

---

# ⚡ Quick Start (No API Key Required)

The included **MockLLM** lets you prototype routing instantly, **offline**.

```python
from gentis_ai import Expert, Router, Flow
from gentis_ai.llm import MockLLM

# 1. Define a Mock LLM for testing
llm = MockLLM(
    routing_rules={
        "help": "support_agent",
        "buy": "sales_agent"
    },
    responses={
        "help": "I can certainly help you with your technical issue.",
        "buy": "Great! Let's get you set up with a new plan."
    },
    default_response="I'm not sure how to route that request."
)

# 2. Define your Experts
support = Expert(name="support_agent", description="Handles technical support queries.")
sales   = Expert(name="sales_agent",   description="Handles sales and upgrades.")

# 3. Initialize Router and Flow
router = Router(experts=[support, sales], llm=llm)
flow   = Flow(router=router, llm=llm)

# 4. Run a turn
response = flow.process_turn("I need help with an error.")

print(response.agent_name)  # support_agent
print(response.content)      # I can certainly help you...
```

---

# 🌐 Real LLM Usage (Gemini, etc.)

Switching from mock mode to a real model is just one line:

```python
import os
from gentis_ai.llm import GeminiLLM

llm = GeminiLLM(
    model_name="gemini-2.5-flash-lite",
    api_key=os.getenv("GOOGLE_API_KEY")
)

# Everything else stays the same
```

Azure OpenAI, AWS Bedrock, vLLM, and other OpenAI-compatible endpoints use the same `BaseLLM` contract:

```python
from gentis_ai.llm import AzureOpenAILLM, BedrockLLM, OpenAICompatibleLLM

azure_llm = AzureOpenAILLM(
    model_name="my-azure-deployment",
    azure_endpoint="https://my-resource.openai.azure.com",
    api_key="...",
)

aws_llm = BedrockLLM(
    model_name="us.amazon.nova-lite-v1:0",
    region_name="us-east-1",
)

compatible_llm = OpenAICompatibleLLM(
    model_name="gpt-4o-mini",
    api_key="...",
    base_url="https://api.openai.com/v1",
)
```

Useful environment variables:

* Azure: `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT`
* AWS Bedrock: `AWS_BEDROCK_MODEL_ID`, `AWS_REGION` or `AWS_DEFAULT_REGION`
* OpenAI-compatible: `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`

See `examples/cloud_providers_example.py` for a provider-switching example.

---

# ✨ Advanced Features

## 1. Streaming Support
The framework now supports streaming responses from LLMs (Ollama and Gemini).

### Usage
Pass `stream=True` to `flow.process_turn()`:
```python
response = flow.process_turn(user_input, user_id=user_id, stream=True)
```
**Note:** Currently, this will print the chunks directly to `stdout` as they arrive, providing immediate visual feedback in CLI applications.

## 2. Hybrid Routing
The Router can now select multiple experts for a single query if the intent covers multiple domains (e.g., "History of Math" -> `history` + `math`).

### How it works
1. The Router prompt was updated to output a comma-separated list of experts.
2. `Flow.process_turn` detects if multiple experts are returned.
3. If multiple experts are selected:
   - The system queries each expert individually with the user's message.
   - The responses are collected.
   - The default expert (Orchestrator) synthesizes a final answer based on the expert opinions.

## 3. Parallel Execution
To improve performance during Hybrid Routing, expert queries can be executed in parallel.

### Usage
Initialize `Flow` with `parallel_execution=True`: (for CPU-bound tasks)
```python
flow = Flow(router=router, llm=llm, parallel_execution=True)
```
This uses a `ThreadPoolExecutor` to run expert queries concurrently.

## 4. Ollama Configuration
`OllamaLLM` now accepts additional keyword arguments (like `temperature`) in its constructor:
```python
llm = OllamaLLM(model_name="granite4:micro", temperature=0.7)
```

---

# 📘 Documentation & Examples

* [**Official Documentation**](https://gentisaidocumentation.vercel.app/)
* `examples/simple_example.py` — A basic two-expert system
* `examples/advanced_example.py` — Multi-turn flows and expert handoffs
* `comparison/README_comparison.md` — Full benchmark logs

---

# 🤝 Contributing

We welcome contributions!
Pull requests, issues, and feature ideas are all appreciated.
See **CONTRIBUTING.md**.

---

# 📜 License

MIT License — see `LICENSE`.

---
