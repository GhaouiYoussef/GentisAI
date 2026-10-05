"""Shared, validated provider configuration for demos and generated projects."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from importlib.util import find_spec
import math
from typing import Any
from urllib.parse import urlsplit

from gentis_ai.config import AzureSettings, load_environment, normalize_environment
from gentis_ai import llm as llm_providers
from gentis_ai.llm import BaseLLM, MockLLM


def __getattr__(name: str):
    # Preserve the provider factory patch points without importing every SDK.
    if name in llm_providers._PROVIDERS:
        return getattr(llm_providers, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


PROVIDER_CHOICES = ("mock", "openai", "azure", "gemini", "bedrock")
ProviderFactory = Callable[..., Any]


class ConfigurationError(ValueError):
    """A configuration problem whose message is safe to display to the user."""


def positive_integer(environment: Mapping[str, str], name: str, default: int) -> int:
    try:
        value = int(environment.get(name, str(default)))
    except ValueError:
        raise ConfigurationError(f"{name} must be a positive integer.") from None
    if value < 1:
        raise ConfigurationError(f"{name} must be a positive integer.")
    return value


@dataclass(frozen=True)
class ProviderSettings:
    provider: str
    options: dict[str, Any] = field(repr=False)
    routing_max_tokens: int = 1024

    @classmethod
    def from_environment(
        cls, environment: Mapping[str, str], provider: str | None = None
    ) -> ProviderSettings:
        env = normalize_environment(environment)
        selected = (provider or env.get("GENTIS_PROVIDER") or "mock").strip().lower()
        if selected not in PROVIDER_CHOICES:
            raise ConfigurationError(
                "GENTIS_PROVIDER must be one of: " + ", ".join(PROVIDER_CHOICES) + "."
            )
        budget = positive_integer(env, "GENTIS_MAX_TOKENS", 4096)
        routing_budget = positive_integer(env, "GENTIS_ROUTING_MAX_TOKENS", 1024)
        try:
            timeout = float(env.get("GENTIS_TIMEOUT", "45"))
        except ValueError:
            raise ConfigurationError(
                "GENTIS_TIMEOUT must be a positive number of seconds."
            ) from None
        if not math.isfinite(timeout) or timeout <= 0:
            raise ConfigurationError(
                "GENTIS_TIMEOUT must be a positive number of seconds."
            )

        def required(name: str) -> str:
            value = env.get(name)
            if not value:
                raise ConfigurationError(
                    f"{name} is required for {selected}. Run gentis configure --provider {selected}."
                )
            return value

        options: dict[str, Any] = {}
        if selected == "azure":
            try:
                azure = AzureSettings.from_environment(env)
            except ValueError as exc:
                raise ConfigurationError(str(exc)) from None
            if azure.missing():
                raise ConfigurationError(
                    "Azure configuration is incomplete; missing "
                    + " and ".join(azure.missing())
                    + ". Run gentis configure --provider azure."
                )
            options = {
                **azure.llm_options(),
                "timeout": timeout,
                "max_completion_tokens": budget,
            }
        elif selected == "openai":
            base_url = env.get("OPENAI_BASE_URL") or None
            if base_url:
                try:
                    parts = urlsplit(base_url)
                except ValueError:
                    raise ConfigurationError(
                        "OPENAI_BASE_URL must be a valid HTTP(S) URL."
                    ) from None
                if (
                    parts.scheme not in ("http", "https")
                    or not parts.netloc
                    or parts.username
                    or parts.password
                ):
                    raise ConfigurationError(
                        "OPENAI_BASE_URL must be a plain HTTP(S) URL without embedded credentials."
                    )
            token_parameter = (
                env.get("GENTIS_TOKEN_PARAMETER") or "max_completion_tokens"
            )
            if token_parameter not in {"max_tokens", "max_completion_tokens"}:
                raise ConfigurationError(
                    "GENTIS_TOKEN_PARAMETER must be max_tokens or max_completion_tokens."
                )
            options = {
                "api_key": required("OPENAI_API_KEY"),
                "base_url": base_url,
                "model_name": env.get("OPENAI_MODEL") or "gpt-4o-mini",
                "timeout": timeout,
                "token_parameter": token_parameter,
                token_parameter: budget,
            }
        elif selected == "gemini":
            options = {
                "api_key": required("GOOGLE_API_KEY"),
                "model_name": env.get("GEMINI_MODEL") or "gemini-2.5-flash",
                "timeout": timeout,
                "max_output_tokens": budget,
            }
        elif selected == "bedrock":
            options = {
                "model_name": required("AWS_BEDROCK_MODEL_ID"),
                "region_name": env.get("AWS_REGION") or env.get("AWS_DEFAULT_REGION"),
                "max_tokens": budget,
                "timeout": timeout,
            }
            if not options["region_name"]:
                raise ConfigurationError(
                    "AWS_REGION or AWS_DEFAULT_REGION is required for bedrock."
                )
        return cls(selected, options, routing_budget)

    def check_dependencies(self) -> None:
        module = {
            "openai": "openai",
            "azure": "openai",
            "gemini": "google.genai",
            "bedrock": "boto3",
        }.get(self.provider)
        if module:
            try:
                available = find_spec(module) is not None
            except ModuleNotFoundError:
                available = False
            if not available:
                raise ConfigurationError(
                    f'Install the provider SDK: python -m pip install "gentis-ai[{self.provider}]"'
                )


def build_cloud_llm(
    provider: str,
    environment: Mapping[str, str] | None = None,
    *,
    gemini_factory: ProviderFactory | None = None,
    azure_factory: ProviderFactory | None = None,
    openai_factory: ProviderFactory | None = None,
    bedrock_factory: ProviderFactory | None = None,
) -> tuple[Any, str]:
    settings = ProviderSettings.from_environment(
        load_environment() if environment is None else environment, provider
    )
    factories = {
        "azure": (azure_factory, "AzureOpenAILLM"),
        "openai": (openai_factory, "OpenAICompatibleLLM"),
        "gemini": (gemini_factory, "GeminiLLM"),
        "bedrock": (bedrock_factory, "BedrockLLM"),
    }
    if settings.provider == "mock":
        raise ConfigurationError("Use build_llm for the mock provider.")
    factory, class_name = factories[settings.provider]
    if factory is None:
        factory = globals().get(class_name) or getattr(llm_providers, class_name)
    llm = factory(**settings.options)
    label = {
        "azure": "Azure OpenAI",
        "openai": "OpenAI",
        "gemini": "Gemini",
        "bedrock": "AWS Bedrock",
    }[settings.provider]
    if settings.provider in {"openai", "gemini"}:
        label += f" ({settings.options['model_name']})"
    return llm, label


def build_llm(environment: Mapping[str, str] | None = None) -> BaseLLM:
    """Build an LLM from cwd configuration, or a supplied mapping for tests."""
    env = load_environment() if environment is None else environment
    settings = ProviderSettings.from_environment(env)
    if settings.provider == "mock":
        return MockLLM(
            routing_rules={"help": "support", "buy": "sales"},
            responses={
                "help": "I can help troubleshoot that.",
                "buy": "I can explain plans and pricing.",
            },
            default_response="Offline demo response. Configure a provider for live answers.",
        )
    return build_cloud_llm(settings.provider, env)[0]
