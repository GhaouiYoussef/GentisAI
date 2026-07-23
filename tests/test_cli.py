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
