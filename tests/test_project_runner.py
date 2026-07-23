import json
from pathlib import Path

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
