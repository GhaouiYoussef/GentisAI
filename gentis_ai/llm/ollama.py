from typing import List, Any, Dict, Optional, Union, Generator
from ..types import Message
from .base import BaseLLM
import os

try:
    import ollama
except ImportError:
    ollama = None

class OllamaLLM(BaseLLM):
    def __init__(self, model_name: str = "llama3", host: Optional[str] = None, **kwargs):
        """
        Initialize the Ollama LLM.
        
        Args:
            model_name: The name of the model to use (e.g., "llama3", "mistral").
            host: Optional host URL (e.g., "http://localhost:11434"). 
                  If not provided, uses the OLLAMA_HOST env var or default.
            **kwargs: Additional arguments to pass to the client or store (e.g. temperature).
        """
        if not ollama:
            raise ImportError("ollama package is required for OllamaLLM. Install it with `pip install ollama`.")
        
        self.model_name = model_name.strip()
        self.client = ollama.Client(host=host) if host else ollama.Client()
        self.options = kwargs
        self._last_usage = {"total": 0}

    def generate(self, messages: List[Message], system_prompt: str = None, tools: List[Any] = None, stream: bool = False, **kwargs) -> Union[str, Generator[str, None, None]]:
        ollama_messages = []
        
        if system_prompt:
            ollama_messages.append({"role": "system", "content": system_prompt})

        for msg in messages:
            ollama_messages.append({"role": msg.role, "content": msg.content})

        # Handle tools if provided
        api_kwargs = kwargs.copy()
        # Merge options from init (like temperature)
        if self.options:
            if "options" not in api_kwargs:
                api_kwargs["options"] = {}
            api_kwargs["options"].update(self.options)

        tool_map = {}
        if tools:
            api_kwargs["tools"] = tools
            # Create a mapping of function names to callables
            for t in tools:
                if callable(t):
                    tool_map[t.__name__] = t

        try:
            if stream and not tools: # Streaming not supported with tools yet in this simple implementation
                response_stream = self.client.chat(
                    model=self.model_name,
                    messages=ollama_messages,
                    stream=True,
                    **api_kwargs
                )
                def generator():
                    full_content = ""
                    for chunk in response_stream:
                        content = chunk['message']['content']
                        full_content += content
                        yield content
                    
                    # Update usage after stream completes (if available in last chunk, otherwise estimate)
                    # Ollama stream chunks might not have usage stats until the end
                    self._last_usage["total"] = len(full_content) // 4 # Rough estimate for stream

                return generator()

            response = self.client.chat(
                model=self.model_name,
                messages=ollama_messages,
                **api_kwargs
            )
            
            # Update usage
            if "eval_count" in response and "prompt_eval_count" in response:
                self._last_usage["total"] = response.get("prompt_eval_count", 0) + response.get("eval_count", 0)

            # Check for tool calls
            if response['message'].get('tool_calls'):
                # Add the assistant's message (with tool calls) to history
                ollama_messages.append(response['message'])
                
                # Execute tools
                for tool_call in response['message']['tool_calls']:
                    function_name = tool_call['function']['name']
                    arguments = tool_call['function']['arguments']
                    
                    if function_name in tool_map:
                        function_to_call = tool_map[function_name]
                        try:
                            # Call the function
                            result = function_to_call(**arguments)
                        except Exception as e:
                            result = f"Error executing tool: {e}"
                        
                        # Add result to history
                        ollama_messages.append({
                            'role': 'tool',
                            'content': str(result),
                        })
                    else:
                         ollama_messages.append({
                            'role': 'tool',
                            'content': f"Error: Tool '{function_name}' not found.",
                        })
                
                # Call LLM again with tool results
                response = self.client.chat(
                    model=self.model_name,
                    messages=ollama_messages,
                    **api_kwargs
                )
                
                # Update usage (accumulate)
                if "eval_count" in response:
                     self._last_usage["total"] += response.get("prompt_eval_count", 0) + response.get("eval_count", 0)

            return response['message']['content']

        except Exception as e:
            raise e

    def get_token_usage(self) -> Dict[str, int]:
        return self._last_usage

    def count_tokens(self, text: str) -> int:
        # Ollama doesn't have a direct count_tokens endpoint exposed easily in the client yet,
        # but we can estimate or use a tokenizer if needed.
        # For now, simple estimation.
        return len(text) // 4
