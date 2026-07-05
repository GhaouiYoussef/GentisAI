from __future__ import annotations

import os

from gentis_ai.llm import (
    AzureOpenAILLM,
    BedrockLLM,
    GeminiLLM,
    MockLLM,
    OllamaLLM,
    OpenAICompatibleLLM,
    VLLMLLM,
)

DEFAULT_PROVIDER = 'azure'


def build_llm(provider_name: str = DEFAULT_PROVIDER):
    provider_name = (provider_name or DEFAULT_PROVIDER).lower()

    if provider_name == "azure":
        return AzureOpenAILLM(
            model_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            temperature=0.2,
        )

    if provider_name == "gemini":
        return GeminiLLM(
            api_key=os.getenv("GOOGLE_API_KEY"),
            model_name=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite"),
        )

    if provider_name == "openai":
        return OpenAICompatibleLLM(
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            temperature=0.2,
        )

    if provider_name == "ollama":
        return OllamaLLM(
            model_name=os.getenv("OLLAMA_MODEL", "llama3.1"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
            temperature=0.2,
        )

    if provider_name == "bedrock":
        return BedrockLLM(
            model_name=os.getenv("AWS_BEDROCK_MODEL_ID", "us.amazon.nova-lite-v1:0"),
            region_name=os.getenv("AWS_REGION"),
            temperature=0.2,
            max_tokens=512,
        )

    if provider_name == "vllm":
        return VLLMLLM(
            model_name=os.getenv("VLLM_MODEL", "facebook/opt-125m"),
            base_url=os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1"),
            api_key=os.getenv("VLLM_API_KEY", "EMPTY"),
            temperature=0.2,
        )

    if provider_name == "mock":
        return MockLLM()

    raise ValueError(f"Unsupported provider: {provider_name}")
