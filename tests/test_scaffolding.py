from __future__ import annotations

import importlib.util
import io
from pathlib import Path
from types import ModuleType

import pytest

from gentis_ai.llm import AzureOpenAILLM, MockLLM
from gentis_ai.scaffolding import TEMPLATE_CHOICES, create_project


AZURE_FILES = {
    "app.py",
    "test_app.py",
    "README.md",
    "requirements.txt",
    ".env.example",
    "gentis.json",
    "Dockerfile",
}


def load_generated_app(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("generated_support_app", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_template_choices_are_stable():
    assert TEMPLATE_CHOICES == ("basic", "azure-support")


def test_basic_template_keeps_existing_files(tmp_path: Path):
    root = create_project(str(tmp_path / "basic"))

    assert {path.name for path in root.iterdir()} == {
        "app.py",
        "test_app.py",
        ".env.example",
        "Dockerfile",
    }
    assert (root / ".env.example").read_text(encoding="utf-8") == (
        "GOOGLE_API_KEY=\n"
    )


def test_azure_support_template_generates_complete_project(tmp_path: Path):
    root = create_project(
        str(tmp_path / "customer-support"),
        template="azure-support",
    )

    assert {path.name for path in root.iterdir()} == AZURE_FILES
    assert '"template": "azure-support"' in (
        root / "gentis.json"
    ).read_text(encoding="utf-8")
    compile((root / "app.py").read_text(encoding="utf-8"), "app.py", "exec")
    compile(
        (root / "test_app.py").read_text(encoding="utf-8"),
        "test_app.py",
        "exec",
    )


def test_missing_azure_config_uses_mock_and_names_missing_categories(
    tmp_path: Path,
):
    root = create_project(
        str(tmp_path / "customer-support"),
        template="azure-support",
    )
    app = load_generated_app(root / "app.py")
    messages = []

    llm, provider = app.build_llm({}, output=messages.append)

    assert isinstance(llm, MockLLM)
    assert provider == "local mock"
    assert messages == [
        "[GentisAI] Azure OpenAI is not fully configured; "
        "using the local mock provider.",
        "[GentisAI] Missing: API key, endpoint, deployment.",
    ]


def test_partial_config_never_prints_environment_values(tmp_path: Path):
    root = create_project(
        str(tmp_path / "customer-support"),
        template="azure-support",
    )
    app = load_generated_app(root / "app.py")
    messages = []
    environment = {
        "AZURE_OPENAI_API_KEY": "top-secret-key",
        "AZURE_OPENAI_ENDPOINT": "https://private.example",
    }

    llm, provider = app.build_llm(environment, output=messages.append)

    rendered = "\n".join(messages)
    assert isinstance(llm, MockLLM)
    assert provider == "local mock"
    assert "deployment" in rendered
    assert "top-secret-key" not in rendered
    assert "https://private.example" not in rendered


def test_complete_config_selects_azure_without_printing_values(tmp_path: Path):
    root = create_project(
        str(tmp_path / "customer-support"),
        template="azure-support",
    )
    app = load_generated_app(root / "app.py")
    messages = []
    environment = {
        "AZURE_OPENAI_API_KEY": "top-secret-key",
        "AZURE_OPENAI_ENDPOINT": "https://private.example",
        "AZURE_OPENAI_DEPLOYMENT": "private-deployment",
    }

    llm, provider = app.build_llm(
        environment,
        azure_client=object(),
        output=messages.append,
    )

    rendered = "\n".join(messages)
    assert isinstance(llm, AzureOpenAILLM)
    assert provider == "Azure OpenAI"
    assert rendered == "[GentisAI] Provider: Azure OpenAI."
    assert "top-secret-key" not in rendered
    assert "https://private.example" not in rendered
    assert "private-deployment" not in rendered


def test_complete_config_accepts_base_url_and_model_aliases(tmp_path: Path):
    root = create_project(
        str(tmp_path / "customer-support"),
        template="azure-support",
    )
    app = load_generated_app(root / "app.py")

    llm, provider = app.build_llm(
        {
            "AZURE_OPENAI_API_KEY": "key",
            "AZURE_OPENAI_BASE_URL": "https://example/openai/v1",
            "AZURE_OPENAI_MODEL": "deployment-alias",
        },
        azure_client=object(),
        output=lambda _: None,
    )

    assert isinstance(llm, AzureOpenAILLM)
    assert provider == "Azure OpenAI"


def test_complete_invalid_azure_config_does_not_fall_back(
    tmp_path: Path,
    monkeypatch,
):
    root = create_project(
        str(tmp_path / "customer-support"),
        template="azure-support",
    )
    app = load_generated_app(root / "app.py")
    messages = []

    def fail_azure(**kwargs):
        raise ValueError("invalid Azure setup")

    monkeypatch.setattr(app, "AzureOpenAILLM", fail_azure)
    environment = {
        "AZURE_OPENAI_API_KEY": "key",
        "AZURE_OPENAI_ENDPOINT": "https://example",
        "AZURE_OPENAI_DEPLOYMENT": "deployment",
    }

    with pytest.raises(ValueError, match="invalid Azure setup"):
        app.build_llm(environment, output=messages.append)

    assert messages == []


def test_generated_flow_has_exactly_three_single_route_agents(tmp_path: Path):
    root = create_project(
        str(tmp_path / "customer-support"),
        template="azure-support",
    )
    app = load_generated_app(root / "app.py")
    llm, _ = app.build_llm({}, output=lambda _: None)

    flow = app.build_flow(llm)

    assert set(flow.router.experts) == {
        "technical_support",
        "billing_support",
        "account_support",
    }
    assert flow.router.default_expert.name == "account_support"
    assert flow.router.enable_hybrid is False
    assert flow.router.routing_max_tokens == 96


def test_mock_routes_each_support_domain_and_keeps_follow_up(tmp_path: Path):
    root = create_project(
        str(tmp_path / "customer-support"),
        template="azure-support",
    )
    app = load_generated_app(root / "app.py")
    llm, _ = app.build_llm({}, output=lambda _: None)
    flow = app.build_flow(llm)

    billing = flow.process_turn(
        "I was charged twice this month.",
        session_id="billing-session",
    )
    technical = flow.process_turn(
        "The dashboard crashes when I upload a file.",
        session_id="technical-session",
    )
    account = flow.process_turn(
        "I cannot sign in to my account.",
        session_id="account-session",
    )
    follow_up = flow.process_turn(
        "Can you explain the next step?",
        session_id="billing-session",
    )

    assert billing.agent_name == "billing_support"
    assert technical.agent_name == "technical_support"
    assert account.agent_name == "account_support"
    assert follow_up.agent_name == "billing_support"


def test_route_latency_is_measured_from_events(tmp_path: Path):
    root = create_project(
        str(tmp_path / "customer-support"),
        template="azure-support",
    )
    app = load_generated_app(root / "app.py")
    llm, _ = app.build_llm({}, output=lambda _: None)
    flow = app.build_flow(llm)
    stream = io.StringIO()
    ticks = iter([10.0, 10.184])

    content = app.stream_support_turn(
        flow,
        "I was charged twice this month.",
        stream=stream,
        clock=lambda: next(ticks),
    )

    rendered = stream.getvalue()
    assert "[route] billing_support selected in 184 ms" in rendered
    assert "[agent] billing_support" in rendered
    assert content
