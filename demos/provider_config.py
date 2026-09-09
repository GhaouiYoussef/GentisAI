from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from gentis_ai.config import AzureSettings, load_environment
from gentis_ai.llm import AzureOpenAILLM, GeminiLLM, OpenAICompatibleLLM


ProviderFactory = Callable[..., Any]


def build_cloud_llm(
    provider: str,
    environment: Mapping[str, str] | None = None,
    *,
    gemini_factory: ProviderFactory = GeminiLLM,
    azure_factory: ProviderFactory | None = None,
    openai_factory: ProviderFactory = OpenAICompatibleLLM,
) -> tuple[Any, str]:
    environment = load_environment() if environment is None else environment

    if provider == "gemini":
        key = environment.get("GOOGLE_API_KEY") or environment.get("GEMINI_API_KEY")
        if not key:
            raise RuntimeError(
                "GOOGLE_API_KEY or GEMINI_API_KEY is required when "
                "GENTIS_PROVIDER=gemini"
            )
        model = environment.get("GEMINI_MODEL", "gemini-2.5-flash")
        return (
            gemini_factory(api_key=key, model_name=model),
            f"Gemini ({model})",
        )

    if provider == "azure":
        settings = AzureSettings.from_environment(environment)
        missing = settings.missing()
        if missing:
            raise RuntimeError(
                "Azure OpenAI configuration is incomplete when "
                f"GENTIS_PROVIDER=azure; missing {' and '.join(missing)}."
            )
        return (
            (azure_factory or AzureOpenAILLM)(
                **settings.llm_options(),
                timeout=45.0,
                max_completion_tokens=900,
            ),
            "Azure OpenAI",
        )

    if provider == "openai":
        key = environment.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError(
                "OPENAI_API_KEY is required when GENTIS_PROVIDER=openai"
            )
        model = environment.get("OPENAI_MODEL", "gpt-4o-mini")
        return (
            openai_factory(
                api_key=key,
                base_url=environment.get("OPENAI_BASE_URL") or None,
                model_name=model,
                timeout=45.0,
                max_tokens=900,
            ),
            f"OpenAI ({model})",
        )

    raise RuntimeError(
        "GENTIS_PROVIDER must be 'mock', 'openai', 'gemini', or 'azure'."
    )
