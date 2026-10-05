from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path
import runpy
import sys
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from gentis_ai.demo import DEMO_CHOICES, export_demo
from gentis_ai.providers import ConfigurationError


@pytest.mark.parametrize("name", DEMO_CHOICES)
def test_export_contains_editable_project_and_offline_check(name, tmp_path, monkeypatch):
    project = export_demo(name, tmp_path / name)
    expected = {
        "app.py", "demo_app/__init__.py", "demo_app/gentis_setup.py",
        "demo_app/telemetry.py", "demo_app/getting_started.py", "README.md",
        "requirements.txt", ".gitignore", ".env.example", "gentis.json",
        "tests/test_demo.py",
    }
    if name == "customer-rescue":
        expected.add("demo_app/tools.py")
        expected.add("demo_app/mock.py")
    assert {file.relative_to(project).as_posix() for file in project.rglob("*") if file.is_file()} == expected
    assert json.loads((project / "gentis.json").read_text()) == {
        "template": name, "entrypoint": "app.py", "runtime": "streamlit",
    }
    assert "!.env.example" in (project / ".gitignore").read_text()
    for source in project.rglob("*.py"):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        assert not any(
            isinstance(node, ast.ImportFrom) and (node.module or "").startswith("gentis_ai.demos")
            for node in ast.walk(tree)
        ), f"{source.name} must import its local demo code"

    monkeypatch.syspath_prepend(str(project))
    monkeypatch.chdir(tmp_path)
    with patch.dict(sys.modules):
        checks = runpy.run_path(str(project / "tests/test_demo.py"))
        checks["test_local_flow_routes_and_streams_offline"]()


def test_export_does_not_load_local_configuration(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Export must not read local configuration")

    monkeypatch.setattr("gentis_ai.demo.load_environment", forbidden)
    monkeypatch.setattr("gentis_ai.onboarding.load_environment", forbidden)
    monkeypatch.setenv("OPENAI_API_KEY", "private-user-key")
    project = export_demo("customer-rescue", tmp_path / "demo")
    for source in project.rglob("*"):
        if source.is_file():
            assert "private-user-key" not in source.read_text(encoding="utf-8")


@pytest.mark.parametrize("existing_directory", [False, True])
def test_export_refuses_existing_content(tmp_path, existing_directory):
    destination = tmp_path / "demo"
    if existing_directory:
        destination.mkdir()
        existing = destination / "app.py"
    else:
        existing = destination
    existing.write_text("my work", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="never overwritten"):
        export_demo("customer-rescue", destination)
    assert existing.read_text() == "my work"
    if existing_directory:
        assert list(destination.iterdir()) == [existing]


def test_export_accepts_empty_directory(tmp_path):
    assert export_demo("launch-war-room", tmp_path) == tmp_path
    assert (tmp_path / "app.py").is_file()


def test_export_rejects_unknown_demo_before_creating_destination(tmp_path):
    destination = tmp_path / "demo"
    with pytest.raises(ConfigurationError, match="Unknown demo"):
        export_demo("missing", destination)
    assert not destination.exists()


def test_export_runs_edited_local_tools(tmp_path, monkeypatch):
    project = export_demo("customer-rescue", tmp_path / "demo")
    tools = project / "demo_app/tools.py"
    tools.write_text(
        tools.read_text().replace('"status": "review eligible"', '"status": "local edit"'),
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(project))
    monkeypatch.setattr("gentis_ai.config.load_environment", lambda: {"GENTIS_PROVIDER": "mock"})
    with patch.dict(sys.modules):
        setup = importlib.import_module("demo_app.gentis_setup")
        assert Path(setup.__file__).parent == project / "demo_app"
        flow, _ = setup.build_flow("mock")
        result = flow.process_turn("Check invoice INV-2048.", session_id="edited")
        assert result.structured["tools"][0]["output"]["status"] == "local edit"


@pytest.mark.parametrize("name,button", [
    ("customer-rescue", "Customer rescue"), ("launch-war-room", "Launch hooks"),
])
def test_exported_ui_uses_local_flow_and_has_build_commands(name, button, tmp_path, monkeypatch):
    project = export_demo(name, tmp_path / name)
    monkeypatch.chdir(project)
    monkeypatch.syspath_prepend(str(project))
    monkeypatch.setattr("gentis_ai.config.load_environment", lambda: {"GENTIS_PROVIDER": "mock"})
    with patch.dict(sys.modules):
        app = AppTest.from_file(str(project / "app.py"), default_timeout=20).run()
        assert not app.exception
        next(item for item in app.button if item.label == button).click().run()
        assert not app.exception
        assert not app.error
        assert any("ms measured" in item.value for item in app.caption)
        assert any(f"gentis demo {name} --export" in item.value for item in app.code)
        assert any("gentis add tool lookup_invoice --agent billing" in item.value for item in app.code)
