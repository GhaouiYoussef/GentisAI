import os
from typing import Any, Dict, Optional

from .openai_compatible import OpenAICompatibleLLM


class AzureOpenAILLM(OpenAICompatibleLLM):
    """
    LLM adapter for Azure OpenAI deployments.

    The model_name must be the Azure deployment name, not the underlying model
    family. Set it directly or use AZURE_OPENAI_DEPLOYMENT / AZURE_OPENAI_MODEL.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        client: Any = None,
        client_kwargs: Optional[Dict[str, Any]] = None,
        **default_params: Any,
    ):
        resolved_model = (
            model_name
            or os.getenv("AZURE_OPENAI_DEPLOYMENT")
            or os.getenv("AZURE_OPENAI_MODEL")
        )
        if not resolved_model:
            raise ValueError(
                "Azure OpenAI deployment is required. Provide model_name or set "
                "AZURE_OPENAI_DEPLOYMENT."
            )

        resolved_base_url = (
            base_url
            or os.getenv("AZURE_OPENAI_BASE_URL")
            or self._base_url_from_endpoint(
                azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
            )
        )
        if client is None and not resolved_base_url:
            raise ValueError(
                "Azure OpenAI endpoint is required. Provide azure_endpoint/base_url "
                "or set AZURE_OPENAI_ENDPOINT."
            )

        resolved_api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        if client is None and not resolved_api_key:
            raise ValueError(
                "Azure OpenAI API key is required. Provide api_key or set "
                "AZURE_OPENAI_API_KEY."
            )

        super().__init__(
            api_key=resolved_api_key,
            base_url=resolved_base_url,
            model_name=resolved_model,
            client=client,
            client_kwargs=client_kwargs,
            **default_params,
        )

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
