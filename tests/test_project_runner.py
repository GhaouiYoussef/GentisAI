import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from gentis_ai.project_runner import ProjectRunError, run_local_project


def test_no_manifest_preserves_builtin_runner(tmp_path: Path):
    (tmp_path / "app.py").write_text(
        "raise AssertionError('must not execute')\n",
        encoding="utf-8",
    )

    assert run_local_project(tmp_path) is False


def test_valid_manifest_executes_relative_entrypoint(tmp_path: Path):
    marker = tmp_path / "ran.txt"
    (tmp_path / "gentis.json").write_text(
        json.dumps({"template": "azure-support", "entrypoint": "app.py"}),
        encoding="utf-8",
    )
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('yes', encoding='utf-8')\n",
        encoding="utf-8",
    )

    assert run_local_project(tmp_path) is True
    assert marker.read_text(encoding="utf-8") == "yes"


@pytest.mark.parametrize(
    "entrypoint",
    ["../outside.py", str(Path.cwd().anchor + "outside.py")],
)
def test_manifest_rejects_paths_outside_project(tmp_path: Path, entrypoint: str):
    (tmp_path / "gentis.json").write_text(
        json.dumps({"entrypoint": entrypoint}),
        encoding="utf-8",
    )

    with pytest.raises(ProjectRunError, match="entrypoint must be a relative file"):
        run_local_project(tmp_path)


def test_manifest_rejects_malformed_json(tmp_path: Path):
    (tmp_path / "gentis.json").write_text("{", encoding="utf-8")

    with pytest.raises(ProjectRunError, match="manifest is not valid JSON"):
        run_local_project(tmp_path)


def test_missing_entrypoint_fails_cleanly(tmp_path: Path):
    (tmp_path / "gentis.json").write_text(
        json.dumps({"template": "azure-support"}),
        encoding="utf-8",
    )

    with pytest.raises(ProjectRunError, match="entrypoint must be a relative file"):
        run_local_project(tmp_path)


def test_project_exception_is_wrapped_without_original_detail(tmp_path: Path):
    (tmp_path / "gentis.json").write_text(
        json.dumps({"entrypoint": "app.py"}),
        encoding="utf-8",
    )
    (tmp_path / "app.py").write_text(
        "raise RuntimeError('secret-runtime-detail')\n",
        encoding="utf-8",
    )

    with pytest.raises(ProjectRunError) as error:
        run_local_project(tmp_path)

    assert str(error.value) == (
        "Project failed to run. Run the entrypoint directly for a traceback."
    )
    assert "secret-runtime-detail" not in str(error.value)


def test_project_imports_local_modules_and_restores_execution_context(tmp_path):
    previous_directory, previous_path = Path.cwd(), sys.path[:]
    (tmp_path / "gentis.json").write_text('{"entrypoint": "app.py"}')
    (tmp_path / "project_runner_test_helper.py").write_text("VALUE = 'local helper'\n")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from project_runner_test_helper import VALUE\n"
        "Path('ran.txt').write_text(VALUE)\n"
    )
    try:
        assert run_local_project(tmp_path)
        assert (tmp_path / "ran.txt").read_text() == "local helper"
        assert Path.cwd() == previous_directory
        assert sys.path == previous_path
    finally:
        sys.modules.pop("project_runner_test_helper", None)


@pytest.mark.parametrize(
    "runtime,ui,expected",
    [
        ("python", True, "streamlit_app.py"),
        ("streamlit", False, "app.py"),
        ("streamlit", True, "streamlit_app.py"),
    ],
)
def test_streamlit_uses_project_files_and_current_python(
    tmp_path, monkeypatch, runtime, ui, expected
):
    (tmp_path / "gentis.json").write_text(
        json.dumps(
            {
                "runtime": runtime,
                "entrypoint": "app.py",
                "ui": "streamlit_app.py",
            }
        )
    )
    (tmp_path / "app.py").touch()
    (tmp_path / "streamlit_app.py").touch()
    calls = []
    monkeypatch.setattr("gentis_ai.project_runner.find_spec", lambda _: object())
    monkeypatch.setattr(
        "gentis_ai.project_runner.subprocess.run",
        lambda command, **kwargs: (
            calls.append((command, kwargs)) or SimpleNamespace(returncode=0)
        ),
    )

    assert run_local_project(tmp_path, ui=ui, port=8765, headless=True)
    command, options = calls[0]
    assert command[:5] == [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(tmp_path / expected),
    ]
    assert "--server.port=8765" in command
    assert "--server.headless=true" in command
    assert "--server.address=127.0.0.1" in command
    assert options == {"cwd": tmp_path, "check": False}


@pytest.mark.parametrize(
    "manifest,expected",
    [
        ({"entrypoint": "app.py"}, "No Streamlit UI"),
        ({"entrypoint": "app.py", "ui": "../outside.py"}, "relative file"),
        ({"entrypoint": "app.py", "ui": "missing.py"}, "does not exist"),
        ({"runtime": ["streamlit"]}, "runtime must"),
    ],
)
def test_ui_rejects_invalid_project_configuration(tmp_path, manifest, expected):
    (tmp_path / "gentis.json").write_text(json.dumps(manifest))
    with pytest.raises(ProjectRunError, match=expected):
        run_local_project(tmp_path, ui=True)


def test_ui_without_project_gives_init_guidance(tmp_path):
    with pytest.raises(ProjectRunError, match="gentis init"):
        run_local_project(tmp_path, ui=True)


def test_ui_without_streamlit_gives_install_guidance(tmp_path, monkeypatch):
    (tmp_path / "gentis.json").write_text(
        '{"runtime": "streamlit", "entrypoint": "app.py"}'
    )
    (tmp_path / "app.py").touch()
    monkeypatch.setattr("gentis_ai.project_runner.find_spec", lambda _: None)
    with pytest.raises(ProjectRunError, match=r"gentis-ai\[demo\]"):
        run_local_project(tmp_path)


@pytest.mark.parametrize("port", [0, 65536])
def test_ui_rejects_invalid_port_before_starting(tmp_path, port):
    (tmp_path / "gentis.json").write_text(
        '{"runtime": "streamlit", "entrypoint": "app.py"}'
    )
    (tmp_path / "app.py").touch()
    with pytest.raises(ProjectRunError, match="Port must"):
        run_local_project(tmp_path, port=port)


def test_ui_preserves_server_failure_status(tmp_path, monkeypatch):
    (tmp_path / "gentis.json").write_text(
        '{"runtime": "streamlit", "entrypoint": "app.py"}'
    )
    (tmp_path / "app.py").touch()
    monkeypatch.setattr("gentis_ai.project_runner.find_spec", lambda _: object())
    monkeypatch.setattr(
        "gentis_ai.project_runner.subprocess.run",
        lambda *a, **k: SimpleNamespace(returncode=7),
    )
    with pytest.raises(ProjectRunError) as error:
        run_local_project(tmp_path)
    assert error.value.exit_code == 7
