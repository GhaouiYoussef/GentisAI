from __future__ import annotations

import json
from importlib.util import find_spec
import os
import runpy
from pathlib import Path
import subprocess
import sys


class ProjectRunError(RuntimeError):
    """Raised when a local GentisAI project cannot be executed safely."""

    def __init__(self, message: str, *, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


def run_local_project(
    root: Path | None = None,
    *,
    ui: bool = False,
    port: int = 8501,
    headless: bool = False,
) -> bool:
    project_root = (root or Path.cwd()).resolve()
    manifest_path = project_root / "gentis.json"
    if not manifest_path.is_file():
        if ui:
            raise ProjectRunError(
                "No Gentis project found. Run gentis init, then gentis run --ui."
            )
        return False

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectRunError("Gentis project manifest is not valid JSON.") from exc

    if not isinstance(manifest, dict):
        raise ProjectRunError("Gentis project manifest must be a JSON object.")
    runtime = manifest.get("runtime", "python")
    if runtime not in ("python", "streamlit"):
        raise ProjectRunError("Project runtime must be python or streamlit.")
    use_streamlit = ui or runtime == "streamlit"
    entrypoint = manifest.get("ui" if ui else "entrypoint")
    if ui and not entrypoint:
        if runtime == "streamlit":
            entrypoint = manifest.get("entrypoint")
        else:
            raise ProjectRunError(
                'No Streamlit UI configured. Add "ui": "streamlit_app.py" to gentis.json '
                "or create a starter with gentis init my-agent."
            )
    if not isinstance(entrypoint, str) or not entrypoint.strip():
        raise ProjectRunError(
            "Project entrypoint must be a relative file inside the project."
        )

    entrypoint_path = Path(entrypoint)
    candidate = (project_root / entrypoint_path).resolve()
    if entrypoint_path.is_absolute() or not candidate.is_relative_to(project_root):
        raise ProjectRunError(
            "Project entrypoint must be a relative file inside the project."
        )
    if not candidate.is_file():
        raise ProjectRunError("Project entrypoint does not exist.")

    if use_streamlit:
        _run_streamlit(candidate, project_root, port=port, headless=headless)
        return True

    previous_directory = Path.cwd()
    previous_path = sys.path[:]
    try:
        os.chdir(project_root)
        sys.path.insert(0, str(project_root))
        runpy.run_path(str(candidate), run_name="__main__")
    except Exception as exc:
        raise ProjectRunError(
            "Project failed to run. Run the entrypoint directly for a traceback."
        ) from exc
    finally:
        os.chdir(previous_directory)
        sys.path[:] = previous_path
    return True


def _run_streamlit(
    entrypoint: Path, project_root: Path, *, port: int, headless: bool
) -> None:
    if not 1 <= port <= 65535:
        raise ProjectRunError("Port must be between 1 and 65535.")
    if find_spec("streamlit") is None:
        raise ProjectRunError(
            'Install the demo extra: python -m pip install "gentis-ai[demo]"'
        )
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(entrypoint),
        "--server.address=127.0.0.1",
        f"--server.port={port}",
        f"--server.headless={str(headless).lower()}",
        "--browser.gatherUsageStats=false",
    ]
    print(f"Starting {entrypoint.name} at http://127.0.0.1:{port}", flush=True)
    try:
        result = subprocess.run(command, cwd=project_root, check=False)
    except OSError as exc:
        raise ProjectRunError(
            "Could not start Streamlit. Check your Python installation and project permissions."
        ) from exc
    if result.returncode:
        raise ProjectRunError(
            "Streamlit stopped with an error. Check its output for details.",
            exit_code=result.returncode,
        )
