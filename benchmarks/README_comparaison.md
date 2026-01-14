# ✅ **GentisAI vs. CrewAI Comparison Benchmark**

This project contains a real-world benchmark comparing **GentisAI** against **CrewAI** using the Google Gemini API.

## Setup

1. **Environment:**

```bash
# Windows
python -m venv comparison/venv
.\comparison\venv\Scripts\activate
pip install -r comparison/requirements.txt
pip install -e .
```

2. **Configuration:**
   Ensure your `.env` file has a valid `GOOGLE_API_KEY`.

```env
GOOGLE_API_KEY=your_api_key_here
```

## Running the Benchmark

```bash
python comparison/benchmark.py
```

## Benchmark Scenario

A 3-turn realistic conversational workflow:

1. User reports a login issue
2. User asks about upgrading their plan
3. User requests pricing for Enterprise (10 users)

Each framework handles all 3 conversational turns end-to-end.

---

# **Comparison Results (Actual – Gemini 2.5 Flash )**

*Results from a live run on Dec 9, 2025.*

| Feature                | **GentisAI** | **CrewAI** |
| ---------------------- | ----------------- | ---------- |
| **Total Turn Latency** | **12,614 ms**     | 29,995 ms  |
| **Total Tokens**       | **3,077**         | 18,521     |
| **Turns**              | 3                 | 3          |

## 📊 **Averages per Turn**

| Metric                 | GentisAI | CrewAI   |
| ---------------------- | ------------- | -------- |
| **Avg Latency / Turn** | **4,204 ms**  | 9,998 ms |
| **Avg Tokens / Turn**  | **1,025**     | 6,173    |

## **Summary**

* **GentisAI is ~2.4× faster** per turn
* **CrewAI uses ~6× more tokens** per turn
* GentisAI produces concise expert responses
* CrewAI produces extremely long, verbose responses, causing higher latency and cost

---

# **Analysis: Why This Happens**

## **GentisAI (Efficient, Expert-Driven)**

GentisAI uses a **Router-first architecture**:

* The router selects the right expert before generation
* No extra orchestration tokens
* Experts produce **short, targeted** messages
* Predictable per-turn latency
* Designed for **chat, customer support, troubleshooting, sales flows, and real-time apps**

This architecture minimizes unnecessary LLM reasoning steps, resulting in **lower latency and fewer tokens**.

---

## **CrewAI (Verbose, Manager Reasoning Loop)**

CrewAI uses a **Manager-Agent orchestration pattern**:

* The Manager consumes tokens to “think” about the task
* This reasoning step happens **every turn**
* The LLM generates long, marketing-style, padded responses
* Higher tokens → higher latency → higher cost

CrewAI excels at **background autonomous workflows**, but it is less suitable for real-time conversational systems where speed and cost matter.

---
# **Conclusion & Use Case Recommendations**

Across all metrics—**latency, token efficiency, cost, and conversational responsiveness**—**GentisAI consistently outperforms CrewAI** for interactive chat use cases.

Both frameworks have strengths, but they shine in **different categories**.

---

## **When to Choose GentisAI**

🚀 **Real-Time User Interaction**

* **Customer Support Assistants**
  Users expect responses in under 5 seconds. GentisAI’ low per-turn latency makes it ideal.

* **Sales & Lead Qualification**
  Fast, concise expert-driven answers help guide the user without overwhelming them.

* **SaaS AI Copilots**
  When the AI needs to quickly shift between tasks (“update billing”, “explain this feature”, etc.).

* **High-Volume Applications**
  With **6× fewer tokens per turn**, operating costs scale much better.

🟢 Best for:
**Chatbots, product copilots, support agents, guided sales flows, and multi-expert conversational systems.**

---

## **When to Choose CrewAI**

🤖 **Background Autonomous Tasks**

* **Deep Research & Long-Form Analysis**
  When latency does not matter and the agent can take minutes to think, read documents, and produce reports.

* **Complex Multi-Step Planning**
  Tasks where an LLM “manager” decomposes a vague instruction into many steps
  (e.g., *“Plan a full 30-day marketing campaign for my ecommerce store.”*).

* **Heavy Orchestration Workflows**
  When multiple sub-agents must collaborate with a lot of internal reasoning.

🟡 Best for:
**Offline workflows, research agents, planning agents, batch processing, and long-sequence tasks.**

---

# ⭐ Final Thought

GentisAI is designed for **fast, predictable, expert-driven conversations**, while CrewAI focuses on **autonomous procedural reasoning**.
This benchmark helps clarify which tool to choose depending on whether your workload is **interactive** or **autonomous**.