from .core import (
    GentisAIError,
    ProviderError,
    RoutingError,
    SessionStoreError,
    ToolExecutionError,
)
from .memory import BaseSessionStore, InMemorySessionStore, PNNet, SQLiteSessionStore
from .routing import RoutingDecision
from .tools import ToolCall, ToolExecutor, ToolPolicy, ToolRegistry, ToolSpec
from .types import Expert, Message, TurnResponse
from .router import Router
from .session import Flow
from .llm import (
    BaseLLM,
    MockLLM,
    ProviderCapabilities,
    ProviderResponse,
)


def __getattr__(name: str):
    from . import llm

    if name not in llm._PROVIDERS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(llm, name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))

__all__ = [
    "Expert",
    "Message",
    "TurnResponse",
    "Router",
    "RoutingDecision",
    "Flow",
    "PNNet",
    "BaseSessionStore",
    "InMemorySessionStore",
    "SQLiteSessionStore",
    "ToolSpec",
    "ToolCall",
    "ToolPolicy",
    "ToolRegistry",
    "ToolExecutor",
    "GentisAIError",
    "RoutingError",
    "ProviderError",
    "ToolExecutionError",
    "SessionStoreError",
    "AzureOpenAILLM",
    "BaseLLM",
    "BedrockLLM",
    "GeminiLLM",
    "MockLLM",
    "OllamaLLM",
    "OpenAICompatibleLLM",
    "ProviderCapabilities",
    "ProviderResponse",
    "VLLMLLM",
]
