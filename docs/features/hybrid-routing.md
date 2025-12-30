# Hybrid Routing

Hybrid Routing allows the Router to select **multiple experts** for a single query if the user's intent covers multiple domains. This is useful for complex queries that require interdisciplinary knowledge.

## How it Works

1.  **Detection**: The Router prompt has been updated to output a comma-separated list of experts if multiple domains are detected (e.g., "history, math").
2.  **Execution**: `Flow.process_turn` detects this list.
3.  **Consultation**: The system queries each selected expert individually with the user's message.
4.  **Synthesis**: The default expert (usually the Orchestrator) receives the individual expert opinions and synthesizes a final, cohesive answer.

## Example Scenario

**User Query:** "Explain the historical significance of the Enigma machine and write a Python script to simulate it."

**Router Decision:** `['history', 'coding']`

**Process:**
1.  **History Expert**: Explains the Enigma machine's role in WWII.
2.  **Coding Expert**: Writes a Python script for a substitution cipher.
3.  **Orchestrator**: Combines both outputs into a single response.

## Configuration

Hybrid routing is **enabled by default**. You can disable it if you want to force the router to always pick a single expert (which saves tokens and reduces latency).

```python
# Disable Hybrid Routing (Single Expert Mode)
router = Router(experts=[...], llm=llm, enable_hybrid=False)
```

When `enable_hybrid=False`, the router is strictly instructed to select the **single best expert** for the task.
