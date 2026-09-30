from typing import List, Any, Dict, Optional, Union, Generator
from ..types import Message
from .base import BaseLLM, ProviderCapabilities
import os
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

class GeminiLLM(BaseLLM):
    capabilities = ProviderCapabilities(
        supports_streaming=True,
        supports_tools=True,
        supports_structured_output=False,
        supports_token_counting=True,
    )

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash-lite", *, timeout: float | None = None, **default_params: Any):
        if not genai:
            raise ImportError(
                "google-genai is required for GeminiLLM. Install with "
                "`pip install gentis-ai[gemini]`."
            )
        #  lets check if its already an env var 
        resolved_api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not resolved_api_key:
            raise ValueError("API key is required. Provide it directly or set GOOGLE_API_KEY in the environment. \nIf you don't have one, create one for free at https://aistudio.google.com/api-keys/")
        client_options = {"api_key": resolved_api_key}
        if timeout is not None:
            client_options["http_options"] = types.HttpOptions(timeout=int(timeout * 1000))
        self.client = genai.Client(**client_options)
        self.model_name = model_name
        self.default_params = default_params.copy()
        self._last_usage = {"total": 0}

    def generate(self, messages: List[Message], system_prompt: str = None, tools: List[Any] = None, stream: bool = False, **kwargs) -> Union[str, Generator[str, None, None]]:
        genai_history = []
        
        # Handle System Prompt
        # Gemini 2.0 Flash often prefers system instructions in the config or as the first part
        # For simplicity in this wrapper, we'll prepend it if provided.
        if system_prompt:
            genai_history.append(types.Content(
                role="user", 
                parts=[types.Part(text=f"System Instruction: {system_prompt}")]
            ))

        # Convert Messages
        for msg in messages:
            role = "model" if msg.role == "assistant" else "user"
            # Handle system messages in history if they exist (though we usually prune them)
            if msg.role == "system":
                continue 
                
            genai_history.append(types.Content(
                role=role,
                parts=[types.Part(text=msg.content)]
            ))

        # Configure Tools
        params = self.default_params.copy()
        if "max_tokens" in kwargs or "max_output_tokens" in kwargs:
            params.pop("max_tokens", None)
            params.pop("max_output_tokens", None)
        params.update(kwargs)
        if "max_tokens" in params:
            params.setdefault("max_output_tokens", params.pop("max_tokens"))
        if tools:
            params.update(tools=tools, automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False))
        tool_config = types.GenerateContentConfig(**params) if params else None

        try:
            # We use chats.create to maintain some semblance of session if needed, 
            # but here we are stateless per call, reconstructing history.
            # Actually, for a pure 'generate' call, models.generate_content is often simpler 
            # if we pass the whole history.
            # However, the chat interface handles history formatting nicely.
            
            # Let's use chats.create with the history (minus the last message if we were doing a chat loop, 
            # but here 'messages' includes the latest user message? 
            # Usually 'generate' takes history + new_message. 
            # Let's assume 'messages' contains the full conversation including the latest user prompt.
            
            if not messages:
                return ""

            # Split history and last message
            history_content = genai_history[:-1]
            last_message_content = genai_history[-1].parts[0].text

            chat = self.client.chats.create(
                model=self.model_name,
                history=history_content,
                config=tool_config
            )
            
            if stream and not tools:
                response_stream = chat.send_message_stream(last_message_content)
                def generator():
                    full_text = ""
                    for chunk in response_stream:
                        text = chunk.text
                        full_text += text
                        yield text
                    # check if its valid argument to access usage_metadata
                    if hasattr(response_stream, 'usage_metadata') and response_stream.usage_metadata:
                        self._last_usage["total"] = response_stream.usage_metadata.total_token_count
                        # if response_stream.usage_metadata:
                        #     self._last_usage["total"] = response_stream.usage_metadata.total_token_count
                return generator()

            response = chat.send_message(last_message_content)
            
            if response.usage_metadata:
                self._last_usage["total"] = response.usage_metadata.total_token_count
                
            return getattr(response, "text", "") or ""

        except Exception as e:
            raise e

    def get_token_usage(self) -> Dict[str, int]:
        return self._last_usage

    def count_tokens(self, text: str) -> int:
        try:
            resp = self.client.models.count_tokens(
                model=self.model_name,
                contents=types.Content(parts=[types.Part(text=text)])
            )
            return resp.total_tokens
        except Exception:
            return len(text) // 4 # Fallback
