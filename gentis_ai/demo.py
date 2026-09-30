"""Launch bundled Streamlit apps using the same Python as the CLI."""

from __future__ import annotations

from importlib import resources
from importlib.util import find_spec
import os
import subprocess
import sys

from gentis_ai.config import load_environment
from gentis_ai.providers import ConfigurationError, ProviderSettings


DEMO_CHOICES = ("customer-rescue", "launch-war-room")


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
