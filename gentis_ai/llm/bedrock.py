import os
from typing import Any, Dict, Generator, List, Optional, Union

from ..types import Message
from .base import BaseLLM, ProviderCapabilities

try:
    import boto3
except ImportError:
    boto3 = None


class BedrockLLM(BaseLLM):
    """
    LLM adapter for AWS Bedrock Runtime Converse API.

    Use model_name for the Bedrock model ID. AWS credentials and region follow
    the standard boto3 provider chain unless supplied explicitly.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        region_name: Optional[str] = None,
        client: Any = None,
        client_kwargs: Optional[Dict[str, Any]] = None,
        **default_params: Any,
    ):
        if client is None and not boto3:
            raise ImportError(
                "boto3 is required for BedrockLLM. Install with "
                "`pip install gentis-ai[bedrock]`."
            )

        self.model_name = model_name or os.getenv("AWS_BEDROCK_MODEL_ID")
        if not self.model_name:
            raise ValueError(
                "AWS Bedrock model ID is required. Provide model_name or set "
                "AWS_BEDROCK_MODEL_ID."
            )

        self.default_params = default_params
        self._last_usage = {"total": 0}

        if client is not None:
            self.client = client
            return

        kwargs = client_kwargs.copy() if client_kwargs else {}
        resolved_region = region_name or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
        if resolved_region:
            kwargs["region_name"] = resolved_region

        self.client = boto3.client("bedrock-runtime", **kwargs)

    def generate(
        self,
        messages: List[Message],
        system_prompt: str = None,
        tools: List[Any] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        request = self._build_request(messages, system_prompt, tools, kwargs)

        if stream:
            response = self.client.converse_stream(**request)
            return self._stream_response(response)

        response = self.client.converse(**request)
        self._update_usage(response.get("usage"))
        return self._extract_text(response)

    def get_token_usage(self) -> Dict[str, int]:
        return self._last_usage

    def count_tokens(self, text: str) -> int:
        return len(text) // 4

    def _build_request(
        self,
        messages: List[Message],
        system_prompt: Optional[str],
        tools: Optional[List[Any]],
        kwargs: Dict[str, Any],
    ) -> Dict[str, Any]:
        request: Dict[str, Any] = {
            "modelId": self.model_name,
            "messages": [],
        }

        system_messages = []
        if system_prompt:
            system_messages.append({"text": system_prompt})

        for message in messages:
            if message.role == "system":
                system_messages.append({"text": message.content})
                continue

            request["messages"].append(
                {
                    "role": self._normalize_role(message.role),
                    "content": [{"text": message.content}],
                }
            )

        if system_messages:
            request["system"] = system_messages

        api_kwargs = self.default_params.copy()
        api_kwargs.update(kwargs)
        inference_config = self._extract_inference_config(api_kwargs)
        if inference_config:
            request["inferenceConfig"] = inference_config

        request.update(api_kwargs)

        if tools:
            request["toolConfig"] = {"tools": tools}

        return request

    def _extract_inference_config(self, api_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        inference_config = {}
        for key in ("maxTokens", "temperature", "topP", "stopSequences"):
            if key in api_kwargs:
                inference_config[key] = api_kwargs.pop(key)

        aliases = {
            "max_tokens": "maxTokens",
            "top_p": "topP",
            "stop_sequences": "stopSequences",
        }
        for source, target in aliases.items():
            if source in api_kwargs:
                inference_config[target] = api_kwargs.pop(source)

        return inference_config

    def _normalize_role(self, role: str) -> str:
        if role == "model":
            return "assistant"
        if role == "assistant":
            return "assistant"
        return "user"

    def _extract_text(self, response: Dict[str, Any]) -> str:
        message = response.get("output", {}).get("message", {})
        parts = message.get("content", [])
        return "".join(part.get("text", "") for part in parts)

    def _stream_response(self, response: Dict[str, Any]) -> Generator[str, None, None]:
        full_text = ""
        for event in response.get("stream", []):
            if "contentBlockDelta" in event:
                text = event["contentBlockDelta"].get("delta", {}).get("text", "")
                if text:
                    full_text += text
                    yield text
            elif "metadata" in event:
                self._update_usage(event["metadata"].get("usage"))

        if self._last_usage.get("total", 0) == 0 and full_text:
            self._last_usage["total"] = self.count_tokens(full_text)

    def _update_usage(self, usage: Optional[Dict[str, int]]) -> None:
        if not usage:
            return

        input_tokens = usage.get("inputTokens", 0)
        output_tokens = usage.get("outputTokens", 0)
        total_tokens = usage.get("totalTokens", input_tokens + output_tokens)

        self._last_usage = {
            "prompt_tokens": input_tokens,
            "completion_tokens": output_tokens,
            "total": total_tokens,
        }
    capabilities = ProviderCapabilities(
        supports_streaming=True,
        supports_tools=True,
        supports_structured_output=False,
        supports_token_counting=True,
    )
