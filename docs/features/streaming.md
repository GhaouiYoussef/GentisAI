# Streaming Support

The framework supports streaming responses from LLMs (Ollama and Gemini), allowing for real-time feedback in your applications.

## Usage

To enable streaming, pass `stream=True` to the `flow.process_turn()` method.

```python
response = flow.process_turn(user_input, user_id=user_id, stream=True)
```

!!! note
    Currently, enabling streaming will print the chunks directly to `stdout` as they arrive. This provides immediate visual feedback in CLI applications but does not yet return a generator object to the caller.

## Example

```python
# ... setup flow ...

print("Agent is thinking...")
response = flow.process_turn("Tell me a long story", user_id="user1", stream=True)

# The story will be printed to the console character by character.
# The final full response is available in response.content
```
