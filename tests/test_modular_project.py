import json
import os
import sys

import pytest
from streamlit.testing.v1 import AppTest

from gentis_ai.project_runtime import build_project_flow
from gentis_ai.scaffolding import add_agent, add_tool, create_project, init_project


def test_generated_project_runs_its_attached_tool_offline(tmp_path):
    root = init_project(tmp_path)
    flow = build_project_flow(root, environment={})
    response = flow.process_turn("Hello", session_id="first")
    assert response.agent_name == "assistant"
    assert response.content
    assert response.structured["tools"][0]["name"] == "get_started"
    assert response.structured["tools"][0]["ok"]


def test_added_agent_uses_edited_prompt_and_executes_only_its_tool(tmp_path):
    root = init_project(tmp_path)
    add_agent("billing", root=root, description="Handles invoices")
    tool = add_tool("lookup_invoice", root=root, agent="billing")
    tool.write_text(
        "def lookup_invoice(query: str):\n    return {'invoice': query, 'source': 'local'}\n"
    )
    (root / "prompts/billing.md").write_text("My customized billing prompt")
    flow = build_project_flow(root, environment={})
    flow.session_store.save(flow.session_store.get("billing-session", "billing"))
    response = flow.process_turn("invoice 42", session_id="billing-session")
    assert response.agent_name == "billing"
    assert (
        flow.router.experts["billing"].system_prompt == "My customized billing prompt"
    )
    assert [item["name"] for item in response.structured["tools"]] == ["lookup_invoice"]
    assert response.structured["tools"][0]["output"] == {
        "invoice": "invoice 42",
        "source": "local",
    }
    other = flow.process_turn("Hello", session_id="separate-session")
    assert other.agent_name == "assistant"


def test_init_preserves_unrelated_files_and_existing_example(tmp_path):
    (tmp_path / "notes.txt").write_text("keep me")
    (tmp_path / ".env.example").write_text("CUSTOM_EXAMPLE=yes\n")
    (tmp_path / ".gitignore").write_text("custom-cache/\n")
    init_project(tmp_path)
    assert (tmp_path / "notes.txt").read_text() == "keep me"
    assert (tmp_path / ".env.example").read_text() == "CUSTOM_EXAMPLE=yes\n"
    ignore = (tmp_path / ".gitignore").read_text()
    assert "custom-cache/" in ignore and "!.env.example" in ignore


def test_init_conflict_does_not_partially_write_project(tmp_path):
    (tmp_path / "streamlit_app.py").write_text("existing app")
    with pytest.raises(ValueError, match="already exists"):
        init_project(tmp_path)
    assert {item.name for item in tmp_path.iterdir()} == {"streamlit_app.py"}


@pytest.mark.parametrize(
    "name", ["../escape", "bad/name", "class", "__init__", "NUL", "1bad"]
)
def test_add_rejects_invalid_names_without_creating_files(tmp_path, name):
    init_project(tmp_path)
    before = (tmp_path / "gentis.json").read_text()
    with pytest.raises(ValueError, match="Use a name"):
        add_agent(name, root=tmp_path)
    assert (tmp_path / "gentis.json").read_text() == before


def test_add_preserves_existing_component_and_rejects_unknown_agent(tmp_path):
    init_project(tmp_path)
    existing = (tmp_path / "agents/assistant.py").read_text()
    with pytest.raises(ValueError, match="already registered"):
        add_agent("assistant", root=tmp_path)
    with pytest.raises(ValueError, match="Unknown agent"):
        add_tool("lookup", root=tmp_path, agent="missing")
    assert (tmp_path / "agents/assistant.py").read_text() == existing
    assert not (tmp_path / "tools/lookup.py").exists()


def test_new_streamlit_template_and_normalized_names(tmp_path):
    root = create_project(str(tmp_path / "project"), template="streamlit")
    path = add_agent("Customer-Care", root=root)
    tool = add_tool("Lookup-Account", root=root, agent="Customer-Care")
    assert path.name == "customer_care.py"
    assert tool.name == "lookup_account.py"
    assert "customer_care" in build_project_flow(root, environment={}).router.experts


def test_runtime_rejects_manifest_path_escape(tmp_path):
    init_project(tmp_path)
    manifest_path = tmp_path / "gentis.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["agents"]["assistant"]["module"] = "../outside.py"
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="inside the project"):
        build_project_flow(tmp_path, environment={})


def test_reload_uses_edited_tool_even_with_unchanged_size_and_timestamp(tmp_path):
    init_project(tmp_path)
    path = tmp_path / "tools/get_started.py"
    path.write_text("def get_started(query: str):\n    return 'before'\n")
    before = path.stat()
    first = build_project_flow(tmp_path, environment={})
    assert first.process_turn("Hi").structured["tools"][0]["output"] == "before"
    path.write_text("def get_started(query: str):\n    return 'edited'\n")
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    reloaded = build_project_flow(tmp_path, environment={})
    assert reloaded.process_turn("Hi").structured["tools"][0]["output"] == "edited"


def test_generated_streamlit_chat_selects_added_agent_and_resets_session(
    tmp_path, monkeypatch
):
    root = init_project(tmp_path)
    add_agent("billing", root=root)
    add_tool("lookup_invoice", root=root, agent="billing")
    monkeypatch.chdir(root)
    monkeypatch.syspath_prepend(str(root))
    monkeypatch.setattr("gentis_ai.project_runtime.load_environment", lambda *a: {})
    prior = sys.modules.pop("project", None)
    try:
        app = AppTest.from_file(
            str(root / "streamlit_app.py"), default_timeout=20
        ).run()
        assert not app.exception
        app.selectbox[0].select("billing").run()
        app.chat_input[0].set_value("Check my invoice").run()
        assert not app.exception
        assert app.session_state["gentis_messages"][-1]["agent"] == "billing"
        assert any("lookup_invoice" in str(item.value) for item in app.json)
        before = app.session_state["gentis_session_id"]
        next(
            button for button in app.button if button.label == "New conversation"
        ).click().run()
        assert app.session_state["gentis_session_id"] != before
        assert app.session_state["gentis_messages"] == []
    finally:
        sys.modules.pop("project", None)
        if prior is not None:
            sys.modules["project"] = prior
