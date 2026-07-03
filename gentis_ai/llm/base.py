from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generator, Union

from pydantic import BaseModel, ConfigDict, Field

from ..types import Message


class ProviderCapabilities(BaseModel):
    supports_streaming: bool = False
    supports_tools: bool = False
    supports_structured_output: bool = False
    supports_token_counting: bool = False


class ProviderResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    text: str
    usage: dict[str, int] = Field(default_factory=lambda: {"total": 0})
    raw_response: Any = None
    tool_calls: list[Any] = Field(default_factory=list)
    finish_reason: str | None = None

class BaseLLM(ABC):
    """
    Abstract Base Class for LLM providers.
    """
    capabilities = ProviderCapabilities()
    
    @abstractmethod
    def generate(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        tools: list[Any] | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        """
        Generates a response from the LLM.
        
        Args:
            messages: The conversation history.
            system_prompt: Optional system instruction.
            tools: Optional list of tools/functions.
            stream: Whether to stream the response.
            **kwargs: Additional model-specific parameters (e.g., temperature).
            
        Returns:
            The string response content, or a generator if stream=True.
        """
        pass

    def generate_response(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        tools: list[Any] | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> ProviderResponse:
        raw = self.generate(
            messages=messages,
            system_prompt=system_prompt,
            tools=tools,
            stream=stream,
            **kwargs,
        )
        if isinstance(raw, str):
            text = raw
        else:
            text = "".join(str(chunk) for chunk in raw)
        return ProviderResponse(
            text=text,
            usage=self.get_token_usage(),
            raw_response=raw,
        )

    @abstractmethod
    def get_token_usage(self) -> dict[str, int]:
        """
        Returns the token usage of the last call.
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Counts the number of tokens in the given text.
        """
        pass
