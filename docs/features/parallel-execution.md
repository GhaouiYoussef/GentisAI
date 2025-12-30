# Parallel Execution

To improve performance during **Hybrid Routing**, expert queries can be executed in parallel. This significantly reduces latency when consulting multiple experts, as you don't have to wait for one to finish before starting the next.

## Usage

Initialize the `Flow` with `parallel_execution=True`.

```python
flow = Flow(router=router, llm=llm, parallel_execution=True)
```

## Mechanism

This feature uses Python's `concurrent.futures.ThreadPoolExecutor` to run expert queries concurrently.

*   **Sequential (Default)**: Expert A runs -> Expert A finishes -> Expert B runs -> Expert B finishes -> Synthesis.
*   **Parallel**: Expert A and Expert B run at the same time -> Both finish -> Synthesis.

## Performance Impact

The effectiveness of parallel execution depends heavily on your LLM provider:

### ☁️ Cloud APIs (Gemini, OpenAI, Anthropic)
**High Impact.** Since these services handle concurrency on their end, sending multiple requests at once results in a near-linear speedup.
*   *Example:* 2 experts taking 3s each.
    *   Sequential: ~6s
    *   Parallel: ~3.5s

### 💻 Local LLMs (Ollama, LocalAI)
**Variable Impact.**
*   **Single GPU/Model**: If you are running a single instance of Ollama, it often queues requests sequentially or splits compute resources, meaning parallel requests may not complete faster than sequential ones.
*   **Configuration**: You can try increasing `OLLAMA_NUM_PARALLEL` in your Ollama server settings, but inference is still bound by your hardware's total compute capacity.

!!! tip "Recommendation"
    Use `parallel_execution=True` primarily when using **Cloud APIs** or if you have a robust local setup capable of true concurrent inference.
