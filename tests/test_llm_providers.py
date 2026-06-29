import unittest
from types import SimpleNamespace

from gentis_ai import AzureOpenAILLM, BedrockLLM, OpenAICompatibleLLM, VLLMLLM
from gentis_ai.types import Message


class FakeOpenAICompletions:
    def __init__(self):
        self.last_request = None

    def create(self, **kwargs):
        self.last_request = kwargs
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="openai-compatible response")
                )
            ],
            usage=SimpleNamespace(
                prompt_tokens=7,
                completion_tokens=3,
                total_tokens=10,
            ),
        )


class FakeOpenAIClient:
    def __init__(self):
        self.completions = FakeOpenAICompletions()
        self.chat = SimpleNamespace(completions=self.completions)


class FakeBedrockClient:
    def __init__(self):
        self.last_request = None

    def converse(self, **kwargs):
        self.last_request = kwargs
        return {
            "output": {
                "message": {
                    "content": [
                        {"text": "bedrock response"},
                    ]
                }
            },
            "usage": {
                "inputTokens": 11,
                "outputTokens": 5,
                "totalTokens": 16,
            },
        }


class TestOpenAIProviderAdapters(unittest.TestCase):
    def test_openai_compatible_formats_messages_and_usage(self):
        client = FakeOpenAIClient()
        llm = OpenAICompatibleLLM(
            client=client,
            model_name="test-model",
            temperature=0.2,
        )

        response = llm.generate(
            messages=[
                Message(role="user", content="hello"),
                Message(role="model", content="hi"),
            ],
            system_prompt="be brief",
            tools=[{"type": "function", "function": {"name": "lookup"}}],
            max_tokens=20,
        )

        self.assertEqual(response, "openai-compatible response")
        self.assertEqual(client.completions.last_request["model"], "test-model")
        self.assertEqual(
            client.completions.last_request["messages"],
            [
                {"role": "system", "content": "be brief"},
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "hi"},
            ],
        )
        self.assertEqual(client.completions.last_request["temperature"], 0.2)
        self.assertEqual(client.completions.last_request["max_tokens"], 20)
        self.assertIn("tools", client.completions.last_request)
        self.assertEqual(llm.get_token_usage()["total"], 10)

    def test_azure_uses_deployment_name_and_normalizes_endpoint(self):
        client = FakeOpenAIClient()
        llm = AzureOpenAILLM(
            client=client,
            azure_endpoint="https://example.openai.azure.com/",
            api_key="ignored-with-client",
            model_name="my-deployment",
        )

        response = llm.generate([Message(role="user", content="hello")])

        self.assertEqual(response, "openai-compatible response")
        self.assertEqual(client.completions.last_request["model"], "my-deployment")
        self.assertEqual(
            AzureOpenAILLM._base_url_from_endpoint(
                "https://example.openai.azure.com/"
            ),
            "https://example.openai.azure.com/openai/v1",
        )

    def test_vllm_preserves_local_openai_compatible_defaults(self):
        llm = VLLMLLM(client=FakeOpenAIClient())

        self.assertEqual(llm.model_name, "facebook/opt-125m")


class TestBedrockAdapter(unittest.TestCase):
    def test_bedrock_converse_request_and_usage(self):
        client = FakeBedrockClient()
        llm = BedrockLLM(
            client=client,
            model_name="us.amazon.nova-lite-v1:0",
            temperature=0.3,
        )

        response = llm.generate(
            messages=[
                Message(role="system", content="system from history"),
                Message(role="user", content="hello"),
                Message(role="model", content="hi"),
            ],
            system_prompt="be brief",
            max_tokens=64,
            top_p=0.9,
        )

        self.assertEqual(response, "bedrock response")
        self.assertEqual(client.last_request["modelId"], "us.amazon.nova-lite-v1:0")
        self.assertEqual(
            client.last_request["system"],
            [
                {"text": "be brief"},
                {"text": "system from history"},
            ],
        )
        self.assertEqual(
            client.last_request["messages"],
            [
                {"role": "user", "content": [{"text": "hello"}]},
                {"role": "assistant", "content": [{"text": "hi"}]},
            ],
        )
        self.assertEqual(
            client.last_request["inferenceConfig"],
            {"temperature": 0.3, "maxTokens": 64, "topP": 0.9},
        )
        self.assertEqual(llm.get_token_usage()["total"], 16)


if __name__ == "__main__":
    unittest.main()
