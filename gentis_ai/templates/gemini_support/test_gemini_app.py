from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


class FakeGeminiLLM:
    def __init__(self, *, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name


def load_app() -> ModuleType:
    app_path = Path(__file__).with_name("app.py")
    spec = importlib.util.spec_from_file_location("generated_gemini_app", app_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_missing_key_fails_with_setup_guidance():
    app = load_app()

    with pytest.raises(RuntimeError, match="GOOGLE_API_KEY"):
        app.build_llm({}, gemini_factory=FakeGeminiLLM, output=lambda _: None)


@pytest.mark.parametrize("key_name", ["GOOGLE_API_KEY", "GEMINI_API_KEY"])
def test_configured_key_selects_gemini_without_printing_secret(key_name):
    app = load_app()
    messages = []

    llm, provider = app.build_llm(
        {key_name: "test-secret"},
        gemini_factory=FakeGeminiLLM,
        output=messages.append,
    )

    assert isinstance(llm, FakeGeminiLLM)
    assert llm.model_name == "gemini-2.5-flash"
    assert provider == "Gemini (gemini-2.5-flash)"
    assert "test-secret" not in "\n".join(messages)
