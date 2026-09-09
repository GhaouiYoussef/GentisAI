import json

import httpx
import pytest

from gentis_ai.llm import AzureOpenAILLM
from gentis_ai.types import Message
from gentis_ai.config import AzureSettings, load_environment


def test_azure_full_url_aliases_build_versioned_sdk_request(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AzureOpenAIEndpoint", "https://example.openai.azure.com/openai/deployments/gpt-5.4-mini/chat/completions?api-version=2025-04-01-preview")
    monkeypatch.setenv("AzureOpenAIKey", "test-key")
    for name in ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT", "AZURE_OPENAI_DEPLOYMENT_NAME", "AZURE_OPENAI_MODEL", "AZURE_OPENAI_API_VERSION", "AZURE_OPENAI_BASE_URL"):
        monkeypatch.delenv(name, raising=False)
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={
            "id": "test", "object": "chat.completion", "created": 0,
            "model": "gpt-5.4-mini", "choices": [{"index": 0,
            "message": {"role": "assistant", "content": "Hello"}, "finish_reason": "stop"}],
        })

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        llm = AzureOpenAILLM(client_kwargs={"http_client": client}, max_tokens=900)
        assert llm.generate([Message(role="user", content="Hello")], max_tokens=512) == "Hello"
    request = requests[0]
    assert str(request.url) == "https://example.openai.azure.com/openai/deployments/gpt-5.4-mini/chat/completions?api-version=2025-04-01-preview"
    assert request.headers["api-key"] == "test-key"
    payload = json.loads(request.content)
    assert payload["model"] == "gpt-5.4-mini"
    assert payload["max_completion_tokens"] == 512
    assert "max_tokens" not in payload


def test_demo_accepts_requested_azure_variable_names():
    from demos.provider_config import build_cloud_llm
    from tests.test_demo_providers import FakeProvider

    llm, _ = build_cloud_llm("azure", {
        "AzureOpenAIKey": "test-key",
        "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com/",
        "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-5.4-mini",
        "AZURE_OPENAI_API_VERSION": "2025-04-01-preview",
    }, azure_factory=FakeProvider)
    assert llm.options["api_key"] == "test-key"
    assert llm.options["model_name"] == "gpt-5.4-mini"
    assert llm.options["api_version"] == "2025-04-01-preview"


def test_demo_loads_dotenv_before_selecting_provider(tmp_path, monkeypatch):
    from demos.customer_rescue import gentis_setup
    from tests.test_demo_providers import FakeProvider

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("GENTIS_PROVIDER=azure\nAzureOpenAIKey=test-key\nAZURE_OPENAI_ENDPOINT=https://example.openai.azure.com/\nAZURE_OPENAI_DEPLOYMENT_NAME=gpt-5.4-mini\nAZURE_OPENAI_API_VERSION=2025-04-01-preview\n")
    monkeypatch.delenv("GENTIS_PROVIDER", raising=False)
    monkeypatch.setattr(gentis_setup, "__file__", str(tmp_path / "gentis_setup.py"))
    from demos import provider_config
    monkeypatch.setattr(provider_config, "AzureOpenAILLM", FakeProvider)
    flow, label = gentis_setup.build_flow()
    assert label == "Azure OpenAI"
    assert flow.llm.options["api_key"] == "test-key"


def test_dotenv_precedence_preserves_shell_aliases_and_does_not_mutate_environment(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("AzureOpenAIKey", "shell-key")
    (tmp_path / ".env").write_text("AZURE_OPENAI_API_KEY=file-key\nGENTIS_TEST_SETTING=root\n")
    local = tmp_path / "demo.env"
    local.write_text("GENTIS_TEST_SETTING=local\n")
    import os
    before = dict(os.environ)
    loaded = load_environment(local)
    assert loaded["AZURE_OPENAI_API_KEY"] == "shell-key"
    assert loaded["GENTIS_TEST_SETTING"] == "local"
    assert dict(os.environ) == before


def test_shell_gemini_alias_overrides_file_google_key(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "shell-key")
    (tmp_path / ".env").write_text("GOOGLE_API_KEY=file-key\n")
    assert load_environment()["GOOGLE_API_KEY"] == "shell-key"


@pytest.mark.parametrize("endpoint", [
    "https://example.openai.azure.com",
    "https://example.openai.azure.com/openai/",
    "https://example.openai.azure.com/openai/v1/",
])
def test_azure_normalizes_resource_endpoints(endpoint):
    assert AzureSettings.from_environment({"AZURE_OPENAI_ENDPOINT": endpoint}).endpoint == "https://example.openai.azure.com"


def test_azure_explicit_settings_override_url_values():
    config = AzureSettings.from_environment({
        "AzureOpenAIEndpoint": "https://example.openai.azure.com/openai/deployments/old/chat/completions?api-version=old-version",
        "AZURE_OPENAI_DEPLOYMENT_NAME": "new-deployment",
        "AZURE_OPENAI_API_VERSION": "new-version",
    })
    assert config.deployment == "new-deployment"
    assert config.api_version == "new-version"


def test_azure_v1_request_remains_supported():
    captured = []

    def respond(request):
        captured.append(request)
        return httpx.Response(200, json={"choices": [{"message": {"content": "Hi"}}]})

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        llm = AzureOpenAILLM(environment={}, api_key="key", azure_endpoint="https://example.openai.azure.com/", model_name="deployment", client_kwargs={"http_client": client})
        llm.generate([Message(role="user", content="Hi")])
    assert str(captured[0].url) == "https://example.openai.azure.com/openai/v1/chat/completions"


def test_azure_streaming_uses_versioned_endpoint_and_completion_budget():
    captured = []

    def respond(request):
        captured.append(request)
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text='data: {"choices":[{"delta":{"content":"Hello"},"index":0}]}\n\ndata: {"choices":[],"usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2}}\n\ndata: [DONE]\n\n')

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        llm = AzureOpenAILLM(environment={}, api_key="key", azure_endpoint="https://example.openai.azure.com/", api_version="2025-04-01-preview", model_name="gpt-5.4-mini", max_tokens=900, client_kwargs={"http_client": client})
        assert "".join(llm.generate([Message(role="user", content="Hello")], stream=True)) == "Hello"
    body = json.loads(captured[0].content)
    assert body["stream"] is True
    assert body["stream_options"]["include_usage"] is True
    assert body["max_completion_tokens"] == 900
    assert "max_tokens" not in body
