from typing import Any, Dict, Generator, List, Optional, Union

from ..types import Message
from .base import BaseLLM, ProviderCapabilities

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class OpenAICompatibleLLM(BaseLLM):
    """
    LLM adapter for OpenAI-compatible chat completion APIs.

    This works with OpenAI itself and any server that implements the OpenAI
    Chat Completions API, including vLLM, LiteLLM, and compatible gateways.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: str = "gpt-4o-mini",
        client: Any = None,
        client_kwargs: Optional[Dict[str, Any]] = None,
        **default_params: Any,
    ):
        if client is None and not OpenAI:
            raise ImportError(
                "openai is required for OpenAICompatibleLLM. Install with "
                "`pip install gentis-ai[openai]`."
            )

        self.model_name = model_name
        self.default_params = default_params.copy()
        self._last_usage = {"total": 0}

        if client is not None:
            self.client = client
            return

        kwargs = client_kwargs.copy() if client_kwargs else {}
        if api_key is not None:
            kwargs["api_key"] = api_key
        if base_url is not None:
            kwargs["base_url"] = base_url
        if "timeout" in self.default_params:
            kwargs.setdefault("timeout", self.default_params.pop("timeout"))
        if "max_retries" in self.default_params:
            kwargs.setdefault("max_retries", self.default_params.pop("max_retries"))

        self.client = OpenAI(**kwargs)

    def generate(
        self,
        messages: List[Message],
        system_prompt: str = None,
        tools: List[Any] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        openai_messages = self._format_messages(messages, system_prompt)

        api_kwargs = self.default_params.copy()
        api_kwargs.update(kwargs)
        if tools:
            api_kwargs["tools"] = tools

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=openai_messages,
            stream=stream,
            **api_kwargs,
        )

        if stream:
            return self._stream_response(response)

        usage = getattr(response, "usage", None)
        self._update_usage(usage)

        if not response.choices:
            return ""
        return response.choices[0].message.content or ""

    def get_token_usage(self) -> Dict[str, int]:
        return self._last_usage

    def count_tokens(self, text: str) -> int:
        try:
            import tiktoken

            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            return len(encoding.encode(text))
        except ImportError:
            return len(text) // 4

    def _format_messages(
        self, messages: List[Message], system_prompt: Optional[str]
    ) -> List[Dict[str, str]]:
        formatted = []
        if system_prompt:
            formatted.append({"role": "system", "content": system_prompt})

        for message in messages:
            formatted.append(
                {
                    "role": self._normalize_role(message.role),
                    "content": message.content,
                }
            )
        return formatted

    def _normalize_role(self, role: str) -> str:
        if role == "model":
            return "assistant"
        return role

    def _stream_response(self, response: Any) -> Generator[str, None, None]:
        full_text = ""
        for chunk in response:
            usage = getattr(chunk, "usage", None)
            if usage is not None:
                self._update_usage(usage)

            if not getattr(chunk, "choices", None):
                continue

            delta = chunk.choices[0].delta
            text = getattr(delta, "content", None)
            if text:
                full_text += text
                yield text

        if self._last_usage.get("total", 0) == 0 and full_text:
            self._last_usage["total"] = self.count_tokens(full_text)

    def _update_usage(self, usage: Any) -> None:
        if usage is None:
            return

        prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
        completion_tokens = getattr(usage, "completion_tokens", 0) or 0
        total_tokens = getattr(usage, "total_tokens", None)

        if total_tokens is None:
            total_tokens = prompt_tokens + completion_tokens

        self._last_usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total": total_tokens,
        }
    capabilities = ProviderCapabilities(
        supports_streaming=True,
        supports_tools=True,
        supports_structured_output=True,
        supports_token_counting=False,
    )
