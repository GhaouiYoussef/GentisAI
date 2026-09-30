from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from gentis_ai.cli import main
from gentis_ai.demo import launch_demo
from gentis_ai.onboarding import configure, doctor
from gentis_ai.providers import ConfigurationError, ProviderSettings, build_cloud_llm
from gentis_ai.scaffolding import create_project
from gentis_ai.llm import OpenAICompatibleLLM
from gentis_ai.types import Message
from tests.test_demo_providers import FakeProvider


@pytest.fixture(autouse=True)
def isolated_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def test_demo_launches_packaged_app_with_current_interpreter(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "gentis_ai.demo.load_environment", lambda: {"GENTIS_PROVIDER": "azure"}
    )
    monkeypatch.setattr("gentis_ai.demo.find_spec", lambda _: object())
    monkeypatch.setattr(
        "gentis_ai.demo.subprocess.run",
        lambda args, **kwargs: (
            calls.append((args, kwargs)) or SimpleNamespace(returncode=7)
        ),
    )
    assert (
        launch_demo("launch-war-room", provider="mock", port=8765, headless=True) == 7
    )
    command, options = calls[0]
    assert command[:4] == [sys.executable, "-m", "streamlit", "run"]
    assert Path(command[4]).is_file()
    assert "gentis_ai" in Path(command[4]).parts
    assert "--server.address=127.0.0.1" in command
    assert "--server.port=8765" in command
    assert options["env"]["GENTIS_PROVIDER"] == "mock"
    assert options["check"] is False


def test_missing_demo_extra_has_install_guidance(monkeypatch):
    monkeypatch.setattr("gentis_ai.demo.find_spec", lambda _: None)
    with pytest.raises(ConfigurationError, match=r"gentis-ai\[demo\]"):
        launch_demo()


@pytest.mark.parametrize("port", [0, -1, 65536])
def test_invalid_port_is_rejected(port):
    with pytest.raises(ConfigurationError, match="Port must"):
        launch_demo(port=port)


def test_invalid_provider_prevents_server_launch(monkeypatch):
    monkeypatch.setattr(
        "gentis_ai.demo.load_environment", lambda: {"GENTIS_PROVIDER": "azure"}
    )
    monkeypatch.setattr("gentis_ai.demo.find_spec", lambda _: object())
    monkeypatch.setattr(
        "gentis_ai.demo.subprocess.run", lambda *a, **kw: pytest.fail("must not start")
    )
    with pytest.raises(ConfigurationError, match="missing"):
        launch_demo()


def test_configure_round_trips_special_characters_without_printing_key(
    tmp_path, monkeypatch, capsys
):
    from dotenv import dotenv_values

    secret = "fake-'key\\with#spaces and ${literal}"
    monkeypatch.setattr("gentis_ai.onboarding.getpass.getpass", lambda _: secret)
    answers = iter(["test-model", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    target = tmp_path / "test-config.txt"
    configure("openai", target)
    values = dotenv_values(target, interpolate=False)
    assert values["OPENAI_API_KEY"] == secret
    assert values["GENTIS_PROVIDER"] == "openai"
    assert values["GENTIS_MAX_TOKENS"] == "4096"
    assert secret not in capsys.readouterr().out


def test_configure_preserves_existing_file(tmp_path):
    target = tmp_path / "settings.txt"
    target.write_text("existing config", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="already exists"):
        configure("mock", target)
    assert target.read_text(encoding="utf-8") == "existing config"


def test_configure_invalid_values_do_not_create_file(tmp_path, monkeypatch):
    monkeypatch.setattr("gentis_ai.onboarding.getpass.getpass", lambda _: "")
    answers = iter(["", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    target = tmp_path / "settings.txt"
    with pytest.raises(ConfigurationError, match="OPENAI_API_KEY"):
        configure("openai", target)
    assert not target.exists()


def test_doctor_is_offline_and_does_not_print_credentials(monkeypatch, capsys):
    monkeypatch.setattr(
        "gentis_ai.onboarding.load_environment",
        lambda: {"GENTIS_PROVIDER": "openai", "OPENAI_API_KEY": "private-key"},
    )
    monkeypatch.setattr("gentis_ai.providers.find_spec", lambda _: object())
    monkeypatch.setattr(
        "gentis_ai.providers.OpenAICompatibleLLM",
        lambda **kw: pytest.fail("must not build client"),
    )
    assert doctor().provider == "openai"
    output = capsys.readouterr().out
    assert "private-key" not in output
    assert "No API request" in output


def test_missing_provider_sdk_has_install_guidance(monkeypatch):
    monkeypatch.setattr("gentis_ai.providers.find_spec", lambda _: None)
    settings = ProviderSettings.from_environment(
        {"GENTIS_PROVIDER": "gemini", "GEMINI_API_KEY": "key"}
    )
    with pytest.raises(ConfigurationError, match=r"gentis-ai\[gemini\]"):
        settings.check_dependencies()


@pytest.mark.parametrize(
    "name,value",
    [
        ("GENTIS_MAX_TOKENS", "0"),
        ("GENTIS_MAX_TOKENS", "1.2"),
        ("GENTIS_ROUTING_MAX_TOKENS", "-1"),
        ("GENTIS_TIMEOUT", "nan"),
        ("GENTIS_TIMEOUT", "inf"),
        ("GENTIS_TIMEOUT", "0"),
    ],
)
def test_invalid_budgets_fail_locally_without_echoing_values(name, value):
    with pytest.raises(ConfigurationError, match=name):
        ProviderSettings.from_environment({name: value})


def test_bedrock_uses_sdk_credentials_and_normalized_budgets():
    llm, label = build_cloud_llm(
        "bedrock",
        {
            "AWS_BEDROCK_MODEL_ID": "test-profile",
            "AWS_REGION": "us-east-1",
            "GENTIS_MAX_TOKENS": "1234",
            "GENTIS_TIMEOUT": "15",
        },
        bedrock_factory=FakeProvider,
    )
    assert label == "AWS Bedrock"
    assert llm.options == {
        "model_name": "test-profile",
        "region_name": "us-east-1",
        "max_tokens": 1234,
        "timeout": 15.0,
    }


@pytest.mark.parametrize("parameter", ["max_completion_tokens", "max_tokens"])
def test_openai_router_budget_overrides_default_with_one_parameter(parameter):
    from tests.test_llm_providers import FakeOpenAIClient

    client = FakeOpenAIClient()
    llm = OpenAICompatibleLLM(
        client=client, token_parameter=parameter, max_completion_tokens=4096
    )
    llm.generate([Message(role="user", content="hello")], max_tokens=1024)
    request = client.completions.last_request
    assert request[parameter] == 1024
    assert ("max_tokens" in request) != ("max_completion_tokens" in request)
    llm.generate([Message(role="user", content="hello")])
    assert client.completions.last_request[parameter] == 4096


@pytest.mark.parametrize(
    "endpoint",
    ["https://[invalid", "[URL](https://example.com)", "https://key@example.com"],
)
def test_malformed_compatible_endpoint_has_safe_actionable_error(endpoint):
    with pytest.raises(ConfigurationError, match="OPENAI_BASE_URL") as error:
        ProviderSettings.from_environment(
            {
                "GENTIS_PROVIDER": "openai",
                "OPENAI_API_KEY": "private",
                "OPENAI_BASE_URL": endpoint,
            }
        )
    assert endpoint not in str(error.value)
    assert "private" not in str(error.value)


def test_gemini_translates_router_budget_and_timeout(monkeypatch):
    from gentis_ai.llm import gemini

    clients, configurations = [], []

    class FakeTypes:
        HttpOptions = staticmethod(lambda **kw: kw)
        Content = staticmethod(lambda **kw: SimpleNamespace(**kw))
        Part = staticmethod(lambda **kw: SimpleNamespace(**kw))
        GenerateContentConfig = staticmethod(lambda **kw: kw)

    def create_chat(**kwargs):
        configurations.append(kwargs["config"])
        return SimpleNamespace(
            send_message=lambda _: SimpleNamespace(text="answer", usage_metadata=None)
        )

    def create_client(**kwargs):
        clients.append(kwargs)
        return SimpleNamespace(chats=SimpleNamespace(create=create_chat))

    monkeypatch.setattr(gemini, "types", FakeTypes)
    monkeypatch.setattr(gemini, "genai", SimpleNamespace(Client=create_client))
    llm = gemini.GeminiLLM(api_key="fake", timeout=45, max_output_tokens=4096)
    llm.generate([Message(role="user", content="hello")], max_tokens=1024)
    assert clients[0]["http_options"]["timeout"] == 45000
    assert configurations[0] == {"max_output_tokens": 1024}


def test_support_project_runs_offline_and_is_editable(tmp_path):
    project = create_project(str(tmp_path / "agent"), template="support")
    assert json.loads((project / "gentis.json").read_text())["entrypoint"] == "app.py"
    spec = importlib.util.spec_from_file_location("new_support", project / "app.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    flow = module.build_flow({"GENTIS_PROVIDER": "mock"})
    response = flow.process_turn("I need help", session_id="test")
    assert response.agent_name == "support"
    assert "help" in response.content


def test_scaffolding_refuses_to_overwrite_project(tmp_path):
    root = tmp_path / "existing"
    root.mkdir()
    (root / "app.py").write_text("my work", encoding="utf-8")
    with pytest.raises(ValueError, match="never overwritten"):
        create_project(str(root), template="support")
    assert (root / "app.py").read_text() == "my work"


def test_cli_returns_server_exit_status(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["gentis", "demo", "--provider", "mock"])
    monkeypatch.setattr("gentis_ai.cli.launch_demo", lambda *a, **kw: 7)
    with pytest.raises(SystemExit) as result:
        main()
    assert result.value.code == 7
