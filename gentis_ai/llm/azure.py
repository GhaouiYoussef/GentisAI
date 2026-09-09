from collections.abc import Mapping
from collections.abc import Generator
from typing import Any, Dict, Optional

from gentis_ai.config import AzureSettings, load_environment, normalize_environment
from gentis_ai.core.types import Message

from .openai_compatible import OpenAICompatibleLLM


class AzureOpenAILLM(OpenAICompatibleLLM):
    """Azure deployments using the versioned Azure API or the unversioned v1 API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        client: Any = None,
        client_kwargs: Optional[Dict[str, Any]] = None,
        api_version: Optional[str] = None,
        environment: Mapping[str, str] | None = None,
        **default_params: Any,
    ):
        env = normalize_environment(load_environment() if environment is None else environment)
        for key, value in {
            "AZURE_OPENAI_API_KEY": api_key,
            "AZURE_OPENAI_ENDPOINT": azure_endpoint,
            "AZURE_OPENAI_BASE_URL": base_url,
            "AZURE_OPENAI_DEPLOYMENT": model_name,
            "AZURE_OPENAI_API_VERSION": api_version,
        }.items():
            if value is not None:
                env[key] = value
        settings = AzureSettings.from_environment(env)
        if not settings.deployment:
            raise ValueError("Azure OpenAI deployment is required. Provide model_name or set AZURE_OPENAI_DEPLOYMENT_NAME.")
        if client is None and settings.missing():
            raise ValueError("Azure OpenAI configuration is incomplete; missing " + " and ".join(settings.missing()) + ".")
        if client is None and settings.api_version:
            from openai import AzureOpenAI

            kwargs = (client_kwargs or {}).copy()
            for option in ("timeout", "max_retries"):
                if option in default_params:
                    kwargs.setdefault(option, default_params.pop(option))
            if settings.base_url:
                kwargs["base_url"] = settings.base_url
            else:
                kwargs["azure_endpoint"] = settings.endpoint
            client = AzureOpenAI(api_key=settings.api_key, api_version=settings.api_version, **kwargs)

        if "max_tokens" in default_params:
            default_params.setdefault("max_completion_tokens", default_params.pop("max_tokens"))

        super().__init__(
            api_key=settings.api_key,
            base_url=settings.base_url or self._base_url_from_endpoint(settings.endpoint),
            model_name=settings.deployment,
            client=client,
            client_kwargs=client_kwargs,
            **default_params,
        )

    def generate(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        tools: list[Any] | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> str | Generator[str, None, None]:
        params = self.default_params.copy()
        if "max_tokens" in kwargs or "max_completion_tokens" in kwargs:
            params.pop("max_tokens", None)
            params.pop("max_completion_tokens", None)
        params.update(kwargs)
        if "max_tokens" in params:
            params.setdefault("max_completion_tokens", params.pop("max_tokens"))
        if stream:
            params.setdefault("stream_options", {"include_usage": True})
        return super().generate(messages, system_prompt, tools, stream, **params)

    @staticmethod
    def _base_url_from_endpoint(endpoint: Optional[str]) -> Optional[str]:
        if not endpoint:
            return None
        normalized = endpoint.rstrip("/")
        if normalized.endswith("/openai/v1"):
            return normalized
        if normalized.endswith("/openai"):
            return f"{normalized}/v1"
        return f"{normalized}/openai/v1"
