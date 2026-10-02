"""Launch bundled Streamlit apps using the same Python as the CLI."""

from __future__ import annotations

from importlib import resources
from importlib.util import find_spec
import json
import os
from pathlib import Path
import subprocess
import sys

from gentis_ai.config import load_environment
from gentis_ai.onboarding import configuration_example
from gentis_ai.providers import ConfigurationError, ProviderSettings


DEMO_CHOICES = ("customer-rescue", "launch-war-room")


def export_demo(name: str, destination: str | Path) -> Path:
    """Create a self-contained, editable copy of a packaged demo."""
    if name not in DEMO_CHOICES:
        raise ConfigurationError(
            "Unknown demo. Choose " + " or ".join(DEMO_CHOICES) + "."
        )
    root = Path(destination)
    if root.is_symlink() or (
        root.exists() and (not root.is_dir() or any(root.iterdir()))
    ):
        raise ConfigurationError(
            "Demo destination must be new or empty; existing files are never overwritten."
        )

    source_root = resources.files("gentis_ai.demos")
    source = source_root.joinpath(name.replace("-", "_"))
    files = {}
    for asset in source.iterdir():
        if not asset.is_file() or not asset.name.endswith(".py"):
            continue
        output = "app.py" if asset.name == "app.py" else f"demo_app/{asset.name}"
        # Keep all application imports local so changing a copied helper takes effect.
        content = asset.read_text(encoding="utf-8").replace(
            f"gentis_ai.demos.{name.replace('-', '_')}", "demo_app"
        ).replace("gentis_ai.demos.", "demo_app.")
        files[output] = content
    for shared in ("telemetry.py", "getting_started.py"):
        files[f"demo_app/{shared}"] = source_root.joinpath(shared).read_text(
            encoding="utf-8"
        )
    files.update(
        {
            "gentis.json": json.dumps(
                {"template": name, "entrypoint": "app.py", "runtime": "streamlit"},
                indent=2,
            ) + "\n",
            "requirements.txt": "gentis-ai[demo]>=0.2.31\n",
            ".gitignore": ".env\n.env.*\n!.env.example\n__pycache__/\n.pytest_cache/\n.venv/\n",
            ".env.example": configuration_example("mock"),
            "README.md": _export_readme(name),
            "tests/test_demo.py": _export_test(name),
        }
    )
    root.mkdir(parents=True, exist_ok=True)
    for filename, content in files.items():
        target = root / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8") as handle:
            handle.write(content)
    return root


def _export_readme(name: str) -> str:
    tools_line = (
        "    tools.py             Fictional account, invoice, and support tools\n"
        if name == "customer-rescue" else ""
    )
    tools_guidance = (
        "Edit `demo_app/tools.py` to change the fictional tool implementations. "
        "Register additional callables in `build_flow()` and select calls in "
        "`rescue_tool_policy()` in `demo_app/gentis_setup.py`.\n\n"
        if name == "customer-rescue" else
        "This demo has no tools by default. Register your callables in a `ToolRegistry`, "
        "wrap it in a `ToolExecutor`, and supply that executor and a `tool_policy` to "
        "the `Flow` in `demo_app/gentis_setup.py` when adding tools.\n\n"
    )
    return (
        f"# {name.replace('-', ' ').title()}\n\n"
        "This is your editable copy of the complete GentisAI demo. "
        "The UI imports the local `demo_app` package; changing these files changes your app.\n\n"
        "## Run locally\n\n"
        "From this directory:\n\n"
        "```sh\npython -m pip install -r requirements.txt\ngentis configure --provider mock\ngentis run\n```\n\n"
        "`gentis run` reads `gentis.json` and starts `app.py` with Streamlit. "
        "You can also run `python -m streamlit run app.py`. Mock mode works without credentials.\n\n"
        "## Project structure\n\n"
        "```text\napp.py                   Streamlit UI, chat, and event streaming\n"
        "demo_app/\n    __init__.py\n"
        "    gentis_setup.py      Experts, prompts, provider setup, router, and flow\n"
        f"{tools_line}"
        "    telemetry.py         Trace rendering\n"
        "    getting_started.py   In-app CLI guidance\n"
        "tests/test_demo.py       Offline routing and streaming checks\n"
        "gentis.json              Streamlit launch configuration\n"
        ".env.example             Shareable settings with no credentials\n"
        "requirements.txt         Runtime dependencies\n```\n\n"
        "## Make it yours\n\n"
        "Update `EXPERT_LABELS` and `EXPERT_DESCRIPTIONS` in `demo_app/gentis_setup.py` "
        "to introduce an expert. Edit the scenarios, expert descriptions, and mock responses "
        "there, and edit `app.py` for the UI. Mock routing is scripted for demonstration; "
        "choose a live provider to evaluate contextual routing. Restart Streamlit after "
        "changing agent setup so session state rebuilds the flow.\n\n"
        f"{tools_guidance}"
        "For a new project with CLI-managed agent and tool modules, run `gentis init my-agent`. "
        "Inside that project, use `gentis add agent billing --description \"Handles invoices and refunds\"`, "
        "`gentis add tool lookup_invoice --agent billing`, and `gentis run --ui`. "
        "Those commands extend the new modular project; edit the demo files listed above "
        "to customize this exported demo.\n\n"
        "## Connect a provider\n\n"
        "Install its extra, for example `python -m pip install \"gentis-ai[openai]\"`, "
        "then run `gentis configure --provider openai`, `gentis doctor`, and `gentis run`. "
        "Azure, Gemini, and Bedrock use their corresponding extra and provider name. "
        "If `.env` already exists, it is preserved; use the generated `.env.example` as "
        "a reference and edit your configuration locally. Never commit `.env`.\n\n"
        "## Check your changes\n\n"
        "```sh\npython -m pip install pytest\npython -m pytest tests\n```\n\n"
        "The tests use MockLLM and an explicit environment, so they require no provider credentials.\n"
    )


def _export_test(name: str) -> str:
    prompt, experts = (
        ("Please check invoice INV-2048.", ["billing"])
        if name == "customer-rescue" else
        ("Write three launch hooks.", ["growth_marketer", "copywriter"])
    )
    return f'''from unittest.mock import patch

from demo_app import gentis_setup


def test_local_flow_routes_and_streams_offline():
    with patch.object(gentis_setup, "load_environment", return_value={{"GENTIS_PROVIDER": "mock"}}):
        flow, provider = gentis_setup.build_flow("mock")
    events = list(flow.stream_turn({prompt!r}, session_id="test-demo"))
    decision = next(event.data["decision"] for event in events if event.type == "route_finished")
    assert provider == "MockLLM"
    assert decision["experts"] == {experts!r}
    assert any(event.type == "token" for event in events)
    final = next(event.data["response"] for event in events if event.type == "final")
    assert final.content
'''


def launch_demo(
    name: str = "customer-rescue",
    *,
    provider: str | None = None,
    port: int = 8501,
    headless: bool = False,
) -> int:
    if name not in DEMO_CHOICES:
        raise ConfigurationError(
            "Unknown demo. Choose " + " or ".join(DEMO_CHOICES) + "."
        )
    if not 1 <= port <= 65535:
        raise ConfigurationError("Port must be between 1 and 65535.")
    if find_spec("streamlit") is None:
        raise ConfigurationError(
            'Install the demo extra: python -m pip install "gentis-ai[demo]"'
        )
    environment = load_environment()
    settings = ProviderSettings.from_environment(environment, provider)
    settings.check_dependencies()
    child_environment = {
        **os.environ,
        **environment,
        "GENTIS_PROVIDER": settings.provider,
    }
    app = resources.files("gentis_ai.demos").joinpath(name.replace("-", "_"), "app.py")
    with resources.as_file(app) as path:
        command = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(path),
            "--server.address=127.0.0.1",
            f"--server.port={port}",
            f"--server.headless={str(headless).lower()}",
            "--browser.gatherUsageStats=false",
        ]
        print(
            f"Starting {name} with {settings.provider} at http://127.0.0.1:{port}",
            flush=True,
        )
        return subprocess.run(command, env=child_environment, check=False).returncode
