from typing import List, Any, Dict, Optional
from ..types import Message
from .base import BaseLLM
import os

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class VLLMLLM(BaseLLM):
    def __init__(self, api_key: str = "EMPTY", base_url: str = "http://localhost:8000/v1", model_name: str = "facebook/opt-125m"):
        if not OpenAI:
            raise ImportError("openai package is required for VLLMLLM")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        self.model_name = model_name
        self._last_usage = {"total": 0}

    def generate(self, messages: List[Message], system_prompt: str = None, tools: List[Any] = None, **kwargs) -> str:
        openai_messages = []
        
        if system_prompt:
            openai_messages.append({"role": "system", "content": system_prompt})

        for msg in messages:
            openai_messages.append({"role": msg.role, "content": msg.content})

        # Handle tools if provided (VLLM support for tools varies, but we pass it if OpenAI compatible)
        # Note: VLLM's tool support might depend on the model and version.
        # We'll pass it if 'tools' is in kwargs or we map it.
        # BaseLLM passes 'tools' as a list. OpenAI expects 'tools' param.
        
        api_kwargs = kwargs.copy()
        if tools:
            api_kwargs["tools"] = tools

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=openai_messages,
                **api_kwargs
            )
            
            if response.usage:
                self._last_usage["total"] = response.usage.total_tokens
                
            return response.choices[0].message.content or ""

        except Exception as e:
            raise e

    def get_token_usage(self) -> Dict[str, int]:
        return self._last_usage

    def count_tokens(self, text: str) -> int:
        # VLLM/OpenAI API doesn't have a standard count_tokens endpoint.
        # We can use a rough estimate or try to use tiktoken if available.
        # For now, we'll return a rough estimate (char count / 4) to avoid heavy dependencies
        # unless the user installs tiktoken.
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo") # Fallback encoding
            return len(encoding.encode(text))
        except ImportError:
            return len(text) // 4
