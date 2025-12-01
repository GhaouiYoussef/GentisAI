# SwitchboardAI 🔀

**SwitchboardAI** is a lightweight Python library for building multi-persona AI agents. It solves the "State Management" problem in conversational AI by providing a robust mechanism to:

1.  **Route** user intent to the correct "Expert" (Persona).
2.  **Manage** conversation history, ensuring context is preserved during handoffs.
3.  **Optimize** context windows by pruning stale system prompts and hints.

## Features

*   **Dynamic Router:** Hot-swap system prompts based on user intent classification.
*   **Context Pruning:** Automatically sanitizes chat history to save tokens and reduce hallucinations.
*   **Framework Agnostic:** Designed to work with any LLM provider (Google Gemini, OpenAI, Anthropic), though currently optimized for Google GenAI.

## Installation

```bash
pip install switchboard-ai
```

## Quick Start

```python
from switchboard_ai import Agent, Router, ConversationManager

# 1. Define your Agents
orchestrator = Agent(
    name="orchestrator",
    system_prompt="You are a helpful assistant. Route complex queries to experts.",
    description="General queries, greetings, and routing."
)

marketing_expert = Agent(
    name="marketing",
    system_prompt="You are a marketing guru. Focus on growth and SEO.",
    description="Questions about marketing, SEO, and growth."
)

# 2. Initialize Router
router = Router(agents=[orchestrator, marketing_expert], default_agent=orchestrator)

# 3. Manage Conversation
manager = ConversationManager(router=router)

user_input = "How do I improve my SEO?"
response = manager.process_turn(user_id="user_123", message=user_input)

print(f"Agent: {response.agent_name}")
print(f"Reply: {response.content}")
```
