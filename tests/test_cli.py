from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from gentis_ai.cli import main


def test_new_defaults_to_basic_template(tmp_path: Path, capsys):
    project = tmp_path / "basic"

    with patch.object(sys, "argv", ["gentis", "new", str(project)]):
        main()

    assert (project / "app.py").is_file()
    assert not (project / "gentis.json").exists()
    assert f"Created {project}" in capsys.readouterr().out


def test_new_azure_support_prints_next_steps(tmp_path: Path, capsys):
    project = tmp_path / "customer-support"

    with patch.object(
        sys,
        "argv",
        [
            "gentis",
            "new",
            str(project),
            "--template",
            "azure-support",
        ],
    ):
        main()

    output = capsys.readouterr().out
    assert (project / "gentis.json").is_file()
    assert f"Created {project}" in output
    assert f"cd {project}" in output
    assert "gentis run" in output


def test_new_gemini_support_prints_next_steps(tmp_path: Path, capsys):
    project = tmp_path / "customer-support-gemini"

    with patch.object(
        sys,
        "argv",
        [
            "gentis",
            "new",
            str(project),
            "--template",
            "gemini-support",
        ],
    ):
        main()

    output = capsys.readouterr().out
    assert (project / "gentis.json").is_file()
    assert f"Created {project}" in output
    assert f"cd {project}" in output
    assert "GOOGLE_API_KEY" in output
    assert "gentis run" in output


def test_new_rejects_unknown_template(tmp_path: Path):
    with patch.object(
        sys,
        "argv",
        [
            "gentis",
            "new",
            str(tmp_path / "invalid"),
            "--template",
            "unknown",
        ],
    ):
        with pytest.raises(SystemExit) as error:
            main()

    assert error.value.code == 2


def test_run_executes_manifested_project(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "gentis.json").write_text(
        json.dumps({"entrypoint": "app.py"}),
        encoding="utf-8",
    )
    (tmp_path / "app.py").write_text(
        "print('manifest-project-ran')\n",
        encoding="utf-8",
    )

    with patch.object(sys, "argv", ["gentis", "run"]):
        main()

    assert "manifest-project-ran" in capsys.readouterr().out


def test_run_without_manifest_keeps_builtin_chat(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with (
        patch.object(sys, "argv", ["gentis", "run"]),
        patch("gentis_ai.cli.run_mock_chat") as mock_chat,
    ):
        main()

    mock_chat.assert_called_once_with()


def test_run_reports_safe_project_error(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "gentis.json").write_text("{", encoding="utf-8")

    with patch.object(sys, "argv", ["gentis", "run"]):
        with pytest.raises(SystemExit) as error:
            main()

    assert error.value.code == 1
    assert "manifest is not valid JSON" in capsys.readouterr().err


def test_init_and_add_commands_create_registered_components(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    for command in [
        ["gentis", "init"],
        ["gentis", "add", "agent", "billing", "--description", "Handles invoices"],
        ["gentis", "add", "tool", "lookup_invoice", "--agent", "billing"],
    ]:
        with patch.object(sys, "argv", command):
            main()
    assert (tmp_path / "agents/billing.py").is_file()
    assert (tmp_path / "tools/lookup_invoice.py").is_file()
    manifest = (tmp_path / "gentis.json").read_text()
    assert "billing" in manifest and "lookup_invoice" in manifest
    output = capsys.readouterr().out
    assert "gentis run --ui" in output
    assert "Added agent billing" in output
    assert "Added tool lookup_invoice" in output


def test_demo_export_does_not_launch_server(tmp_path, capsys):
    destination = tmp_path / "editable-demo"
    with (
        patch.object(
            sys,
            "argv",
            ["gentis", "demo", "customer-rescue", "--export", str(destination)],
        ),
        patch("gentis_ai.cli.launch_demo") as launch,
    ):
        main()
    launch.assert_not_called()
    assert (destination / "gentis.json").is_file()
    assert "gentis run" in capsys.readouterr().out


def test_run_ui_passes_launch_options():
    with (
        patch.object(
            sys, "argv", ["gentis", "run", "--ui", "--port", "8765", "--headless"]
        ),
        patch("gentis_ai.cli.run_local_project", return_value=True) as run,
    ):
        main()
    run.assert_called_once_with(ui=True, port=8765, headless=True)


def test_run_ui_failure_preserves_server_status(capsys):
    from gentis_ai.project_runner import ProjectRunError

    with (
        patch.object(sys, "argv", ["gentis", "run", "--ui"]),
        patch(
            "gentis_ai.cli.run_local_project",
            side_effect=ProjectRunError("Server failed", exit_code=7),
        ),
        pytest.raises(SystemExit) as error,
    ):
        main()
    assert error.value.code == 7
    assert "Server failed" in capsys.readouterr().err


def test_configure_existing_file_reports_preservation_and_example(tmp_path, capsys):
    target = tmp_path / "settings.txt"
    target.write_text("keep this config")
    with patch.object(
        sys,
        "argv",
        ["gentis", "configure", "--provider", "mock", "--output", str(target)],
    ):
        main()
    output = capsys.readouterr().out
    assert "Kept existing" in output
    assert "settings.txt.example" in output
    assert "Created" not in output
    assert target.read_text() == "keep this config"
