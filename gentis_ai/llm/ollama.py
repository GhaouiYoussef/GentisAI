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
        # Ollama python client supports tools in chat
        api_kwargs = kwargs.copy()
        if tools:
            api_kwargs["tools"] = tools

        try:
            response = self.client.chat(
                model=self.model_name,
                messages=ollama_messages,
                **api_kwargs
            )
            
            # Ollama response structure:
            # {'model': 'llama3', 'created_at': '...', 'message': {'role': 'assistant', 'content': '...'}, 'done': True, 'total_duration': ..., 'load_duration': ..., 'prompt_eval_count': 12, 'eval_count': 34}
            
            if "eval_count" in response and "prompt_eval_count" in response:
                self._last_usage["total"] = response.get("prompt_eval_count", 0) + response.get("eval_count", 0)
            
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
