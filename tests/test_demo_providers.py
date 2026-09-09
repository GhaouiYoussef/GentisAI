from __future__ import annotations

from typing import Any

import pytest

from demos.customer_rescue.gentis_setup import _build_llm as build_rescue_llm
from demos.launch_war_room.gentis_setup import _build_llm as build_war_room_llm


class FakeProvider:
    def __init__(self, **kwargs: Any):
        self.options = kwargs


def build_provider(*args: Any, **kwargs: Any):
    try:
        from demos.provider_config import build_cloud_llm
    except ModuleNotFoundError:
        pytest.fail("The shared demo provider factory is not implemented")
    return build_cloud_llm(*args, **kwargs)


@pytest.mark.parametrize("key_name", ["GOOGLE_API_KEY", "GEMINI_API_KEY"])
def test_gemini_uses_supported_key_alias_without_exposing_it(key_name):
    llm, label = build_provider(
        "gemini",
        {key_name: "gemini-secret"},
        gemini_factory=FakeProvider,
    )

    assert isinstance(llm, FakeProvider)
    assert llm.options == {
        "api_key": "gemini-secret",
        "model_name": "gemini-2.5-flash",
    }
    assert label == "Gemini (gemini-2.5-flash)"
    assert "gemini-secret" not in label


def test_azure_uses_endpoint_and_deployment_without_exposing_them():
    llm, label = build_provider(
        "azure",
        {
            "AZURE_OPENAI_API_KEY": "azure-secret",
            "AZURE_OPENAI_ENDPOINT": "https://private.example",
            "AZURE_OPENAI_DEPLOYMENT": "private-deployment",
        },
        azure_factory=FakeProvider,
    )

    assert isinstance(llm, FakeProvider)
    assert llm.options == {
        "api_key": "azure-secret",
        "azure_endpoint": "https://private.example",
        "base_url": None,
        "model_name": "private-deployment",
        "api_version": None,
        "environment": {},
        "timeout": 45.0,
        "max_completion_tokens": 900,
    }
    assert label == "Azure OpenAI"
    assert "azure-secret" not in label
    assert "private.example" not in label
    assert "private-deployment" not in label


def test_openai_provider_remains_supported():
    llm, label = build_provider(
        "openai",
        {"OPENAI_API_KEY": "openai-secret"},
        openai_factory=FakeProvider,
    )

    assert isinstance(llm, FakeProvider)
    assert llm.options == {
        "api_key": "openai-secret",
        "base_url": None,
        "model_name": "gpt-4o-mini",
        "timeout": 45.0,
        "max_tokens": 900,
    }
    assert label == "OpenAI (gpt-4o-mini)"
    assert "openai-secret" not in label


@pytest.mark.parametrize(
    ("provider", "environment", "missing_name"),
    [
        ("gemini", {}, "GOOGLE_API_KEY"),
        ("openai", {}, "OPENAI_API_KEY"),
        (
            "azure",
            {"AZURE_OPENAI_API_KEY": "key"},
            "endpoint and deployment",
        ),
    ],
)
def test_selected_provider_rejects_incomplete_configuration(
    provider, environment, missing_name
):
    with pytest.raises(RuntimeError, match=missing_name):
        build_provider(provider, environment)


def test_unknown_provider_names_every_supported_option():
    with pytest.raises(
        RuntimeError,
        match="GENTIS_PROVIDER must be 'mock', 'openai', 'gemini', or 'azure'",
    ):
        build_provider("other", {})


@pytest.mark.parametrize("demo_builder", [build_rescue_llm, build_war_room_llm])
@pytest.mark.parametrize(
    ("provider", "environment", "factory_name", "expected_label"),
    [
        (
            "gemini",
            {"GOOGLE_API_KEY": "key"},
            "gemini_factory",
            "Gemini (gemini-2.5-flash)",
        ),
        (
            "azure",
            {
                "AZURE_OPENAI_API_KEY": "key",
                "AZURE_OPENAI_ENDPOINT": "https://example",
                "AZURE_OPENAI_DEPLOYMENT": "deployment",
            },
            "azure_factory",
            "Azure OpenAI",
        ),
    ],
)
def test_each_demo_accepts_gemini_and_azure(
    demo_builder, provider, environment, factory_name, expected_label
):
    llm, label = demo_builder(
        provider,
        environment,
        **{factory_name: FakeProvider},
    )

    assert isinstance(llm, FakeProvider)
    assert label == expected_label
