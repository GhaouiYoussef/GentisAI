# New Features Documentation

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
