from typing import List, Any, Dict, Optional
from ..types import Message
from .base import BaseLLM
import os

try:
    import ollama
except ImportError:
    ollama = None

class OllamaLLM(BaseLLM):
    def __init__(self, model_name: str = "llama3", host: Optional[str] = None):
        """
        Initialize the Ollama LLM.
        
        Args:
            model_name: The name of the model to use (e.g., "llama3", "mistral").
            host: Optional host URL (e.g., "http://localhost:11434"). 
                  If not provided, uses the OLLAMA_HOST env var or default.
        """
        if not ollama:
            raise ImportError("ollama package is required for OllamaLLM. Install it with `pip install ollama`.")
        
        self.model_name = model_name.strip()
        self.client = ollama.Client(host=host) if host else ollama.Client()
        self._last_usage = {"total": 0}

    def generate(self, messages: List[Message], system_prompt: str = None, tools: List[Any] = None, **kwargs) -> str:
        ollama_messages = []
        
        if system_prompt:
            ollama_messages.append({"role": "system", "content": system_prompt})

        for msg in messages:
            ollama_messages.append({"role": msg.role, "content": msg.content})

        # Handle tools if provided
        api_kwargs = kwargs.copy()
        tool_map = {}
        if tools:
            api_kwargs["tools"] = tools
            # Create a mapping of function names to callables
            for t in tools:
                if callable(t):
                    tool_map[t.__name__] = t

        try:
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
