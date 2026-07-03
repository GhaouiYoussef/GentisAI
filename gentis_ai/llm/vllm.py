from typing import Any

from .openai_compatible import OpenAICompatibleLLM


class VLLMLLM(OpenAICompatibleLLM):
    def __init__(
        self,
        api_key: str = "EMPTY",
        base_url: str = "http://localhost:8000/v1",
        model_name: str = "facebook/opt-125m",
        client: Any = None,
        **default_params: Any,
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            client=client,
            **default_params,
        )
