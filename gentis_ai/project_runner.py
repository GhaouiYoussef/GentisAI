from __future__ import annotations

import json
import runpy
from pathlib import Path


class ProjectRunError(RuntimeError):
    """Raised when a local GentisAI project cannot be executed safely."""


def run_local_project(root: Path | None = None) -> bool:
    project_root = (root or Path.cwd()).resolve()
    manifest_path = project_root / "gentis.json"
    if not manifest_path.is_file():
        return False

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectRunError(
            "Gentis project manifest is not valid JSON."
        ) from exc

    entrypoint = manifest.get("entrypoint") if isinstance(manifest, dict) else None
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

    try:
        runpy.run_path(str(candidate), run_name="__main__")
    except Exception as exc:
        raise ProjectRunError(
            "Project failed to run. Run the entrypoint directly for a traceback."
        ) from exc
    return True
