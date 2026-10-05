"""Verify a built wheel outside the checkout, reusing installed test dependencies."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import venv
import zipfile


def probe() -> None:
    from importlib import resources
    import gentis_ai
    from streamlit.testing.v1 import AppTest
    from gentis_ai.demo import DEMO_CHOICES, export_demo
    from gentis_ai.project_runtime import build_project_flow
    from gentis_ai.scaffolding import add_agent, add_tool, init_project

    assert Path(gentis_ai.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
    for demo, button, expected in [
        ("customer_rescue", "Customer rescue", "Created demo ticket"),
        ("launch_war_room", "Launch hooks", "Route every question"),
    ]:
        app_path = resources.files("gentis_ai.demos").joinpath(demo, "app.py")
        with resources.as_file(app_path) as path:
            app = AppTest.from_file(str(path), default_timeout=30).run()
            assert not app.exception and not app.error
            next(item for item in app.button if item.label == button).click().run()
            assert not app.exception and not app.error
            assert any(expected in item.value for item in app.markdown)
        print(f"Installed {demo}: UI and scenario passed.")

    for name in DEMO_CHOICES:
        root = export_demo(name, Path.cwd() / name)
        sys.path.insert(0, str(root))
        try:
            app = AppTest.from_file(str(root / "app.py"), default_timeout=30).run()
            assert not app.exception and not app.error
        finally:
            sys.path.pop(0)
            for module in list(sys.modules):
                if module == "demo_app" or module.startswith("demo_app."):
                    del sys.modules[module]
        print(f"Installed {name}: exported files and local UI passed.")

    project = init_project(Path.cwd() / "modular-project")
    add_agent("billing", root=project)
    add_tool("lookup_invoice", root=project, agent="billing")
    flow = build_project_flow(project, environment={})
    flow.session_store.save(flow.session_store.get("billing-test", "billing"))
    response = flow.process_turn("Invoice help", session_id="billing-test")
    assert response.agent_name == "billing"
    assert response.structured["tools"][0]["name"] == "lookup_invoice"
    sys.path.insert(0, str(project))
    try:
        app = AppTest.from_file(
            str(project / "streamlit_app.py"), default_timeout=30
        ).run()
        assert not app.exception and not app.error
        app.chat_input[0].set_value("Hello").run()
        assert not app.exception and not app.error
    finally:
        sys.path.pop(0)
        sys.modules.pop("project", None)
    print("Installed modular starter: agent, tool, and Streamlit chat passed.")


def check(wheel: Path) -> None:
    wheel = wheel.resolve()
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        assert "gentis_ai/demos/customer_rescue/app.py" in names
        assert "gentis_ai/demos/launch_war_room/app.py" in names
        assert "gentis_ai/templates/streamlit/streamlit_app.py" in names
        assert "gentis_ai/templates/streamlit/agents/assistant.py" in names
        assert "gentis_ai/templates/streamlit/prompts/assistant.md" in names
        assert "gentis_ai/templates/streamlit/tools/get_started.py" in names
        assert not any(Path(name).name == ".env" for name in names)
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    for key in list(environment):
        if key.startswith("GENTIS_"):
            environment.pop(key)
    environment["GENTIS_PROVIDER"] = "mock"
    with tempfile.TemporaryDirectory(prefix="gentis-wheel-") as temporary:
        root = Path(temporary)
        virtualenv = root / "venv"
        venv.EnvBuilder(with_pip=True, system_site_packages=True).create(virtualenv)
        executable = virtualenv / (
            "Scripts/python.exe" if os.name == "nt" else "bin/python"
        )
        console = virtualenv / (
            "Scripts/gentis.exe" if os.name == "nt" else "bin/gentis"
        )

        def run(command: list[str], **kwargs):
            return subprocess.run(
                command, cwd=root, env=environment, check=True, timeout=120, **kwargs
            )

        run(
            [
                str(executable),
                "-I",
                "-m",
                "pip",
                "install",
                "--no-deps",
                "--no-index",
                str(wheel),
            ]
        )
        run([str(executable), "-I", str(Path(__file__).resolve()), "--probe"])
        run([str(console), "doctor"])
        run([str(console), "demo", "--help"])
        run([str(console), "new", "my-agent", "--template", "support"])
        output = subprocess.run(
            [str(console), "run"],
            cwd=root / "my-agent",
            env=environment,
            input="I need help\nexit\n",
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )
        assert "support: I can help" in output.stdout
        run([str(console), "init", "cli-project"])
        run([str(console), "add", "agent", "billing", "--project", "cli-project"])
        run(
            [
                str(console),
                "add",
                "tool",
                "lookup_invoice",
                "--agent",
                "billing",
                "--project",
                "cli-project",
            ]
        )
        output = subprocess.run(
            [str(console), "run"],
            cwd=root / "cli-project",
            env=environment,
            input="/agent billing\nInvoice help\nexit\n",
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )
        assert "billing:" in output.stdout
        print("Installed CLI and generated project passed outside the checkout.")


if __name__ == "__main__":
    if sys.argv[1:] == ["--probe"]:
        probe()
    else:
        if len(sys.argv) != 2:
            raise SystemExit(
                "Usage: python scripts/check_wheel.py dist/gentis_ai-VERSION-py3-none-any.whl"
            )
        check(Path(sys.argv[1]))
