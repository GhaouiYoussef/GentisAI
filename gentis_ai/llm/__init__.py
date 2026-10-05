from importlib import import_module

from .base import BaseLLM, ProviderCapabilities, ProviderResponse
from .mock import MockLLM

_PROVIDERS = {
    "AzureOpenAILLM": "azure",
    "BedrockLLM": "bedrock",
    "GeminiLLM": "gemini",
    "OpenAICompatibleLLM": "openai_compatible",
    "VLLMLLM": "vllm",
    "OllamaLLM": "ollama",
}


def __getattr__(name: str):
    if name not in _PROVIDERS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(f".{_PROVIDERS[name]}", __name__), name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))

__all__ = [
    "BaseLLM",
    "ProviderCapabilities",
    "ProviderResponse",
    "AzureOpenAILLM",
    "BedrockLLM",
    "GeminiLLM",
    "OpenAICompatibleLLM",
    "VLLMLLM",
    "OllamaLLM",
    "MockLLM",
]
