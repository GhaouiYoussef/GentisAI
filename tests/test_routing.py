from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gentis_ai.cli import main
from gentis_ai.llm import MockLLM


class TestRoutingSchemaCLI(unittest.TestCase):
    def _run_new(self, workspace: Path, args: list[str], inputs: list[str] | None = None) -> dict[str, object]:
        buffer = io.StringIO()
        current_dir = Path.cwd()
        os.chdir(workspace)
        try:
            with contextlib.redirect_stdout(buffer):
                if inputs is None:
                    main(["new", *args])
                else:
                    with patch("builtins.input", side_effect=inputs):
                        main(["new", *args])
        finally:
            os.chdir(current_dir)

        output = buffer.getvalue().splitlines()
        json_start = next(index for index, line in enumerate(output) if line.lstrip().startswith("{"))
        return json.loads("\n".join(output[json_start:]))

    def _load_generated_app(self, project_root: Path):
        module_name = f"generated_app_{project_root.name}"
        spec = importlib.util.spec_from_file_location(module_name, project_root / "app.py")
        module = importlib.util.module_from_spec(spec)
        assert spec is not None and spec.loader is not None
        current_dir = Path.cwd()
        os.chdir(project_root)
        try:
            spec.loader.exec_module(module)
        finally:
            os.chdir(current_dir)
        return module

    def test_new_project_creates_agent_centered_schema(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            result = self._run_new(
                workspace,
                ["multi-agent", "--azure"],
                inputs=["3", "1", "y"],
            )

            project_root = workspace / "multi-agent"
            manifest = json.loads((project_root / "gentis.project.json").read_text(encoding="utf-8"))

            self.assertEqual(result["project"], str(project_root))
            self.assertEqual(manifest["schema_version"], "0.2")
            self.assertEqual(manifest["routing"]["mode"], "both")
            self.assertTrue(manifest["routing"]["fast_router"]["enabled"])
            self.assertTrue(manifest["routing"]["orchestrator"]["enabled"])
            self.assertEqual(manifest["routing"]["first_encounter"], "fast_router")
            self.assertEqual([agent["name"] for agent in manifest["agents"]], ["support", "sales"])
            self.assertTrue(all(agent["example"] for agent in manifest["agents"]))

            self.assertTrue((project_root / "agents" / "support" / "agent.json").exists())
            self.assertTrue((project_root / "agents" / "support" / "prompt.md").exists())
            self.assertTrue((project_root / "agents" / "support" / "tools.py").exists())
            self.assertTrue((project_root / "agents" / "sales" / "agent.json").exists())
            self.assertTrue((project_root / "agents" / "sales" / "prompt.md").exists())
            self.assertTrue((project_root / "agents" / "sales" / "tools.py").exists())
            self.assertIn("Example prompt", (project_root / "agents" / "support" / "prompt.md").read_text(encoding="utf-8"))
            self.assertIn("Example prompt", (project_root / "agents" / "sales" / "prompt.md").read_text(encoding="utf-8"))
            self.assertTrue((project_root / "orchestrator" / "prompt.md").exists())
            self.assertTrue((project_root / "orchestrator" / "orchestrator.json").exists())
            self.assertTrue((project_root / "routing" / "fast_router.json").exists())
            self.assertTrue((project_root / "routing" / "fast_router.py").exists())
            self.assertTrue((project_root / "tests" / "test_routing.py").exists())

    def test_agent_add_creates_agent_bundle_and_updates_router(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            self._run_new(workspace, ["multi-agent", "--azure"], inputs=["3", "1", "y"])
            project_root = workspace / "multi-agent"

            current_dir = Path.cwd()
            os.chdir(workspace)
            try:
                with contextlib.redirect_stdout(io.StringIO()) as buffer:
                    main([
                        "agent",
                        "add",
                        "agent2",
                        "--project",
                        str(project_root),
                    ])
            finally:
                os.chdir(current_dir)

            output = json.loads(buffer.getvalue())
            manifest = json.loads((project_root / "gentis.project.json").read_text(encoding="utf-8"))
            fast_router = json.loads((project_root / "routing" / "fast_router.json").read_text(encoding="utf-8"))

            self.assertEqual(output["agent_added"], "agent2")
            self.assertEqual(
                output["created"],
                [
                    "agents/agent2/prompt.md",
                    "agents/agent2/tools.py",
                    "agents/agent2/agent.json",
                ],
            )
            self.assertEqual(
                output["updated"],
                ["gentis.project.json", "routing/fast_router.json", "routing/fast_router.py", "app.py"],
            )
            self.assertTrue((project_root / "agents" / "agent2" / "prompt.md").exists())
            self.assertTrue((project_root / "agents" / "agent2" / "tools.py").exists())
            self.assertTrue((project_root / "agents" / "agent2" / "agent.json").exists())
            self.assertIn("agent2", [agent["name"] for agent in manifest["agents"]])
            self.assertIn("agent2", fast_router["rules"].values())
            self.assertIn("agent2", (project_root / "routing" / "fast_router.py").read_text(encoding="utf-8"))
            self.assertIn("agent2", (project_root / "app.py").read_text(encoding="utf-8"))

    def test_generated_app_builds_flow_with_mock_llm(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            self._run_new(workspace, ["multi-agent", "--azure"], inputs=["3", "1", "y"])
            project_root = workspace / "multi-agent"
            app = self._load_generated_app(project_root)

            flow = app.build_flow(
                MockLLM(
                    routing_rules={"help": "support", "price": "sales"},
                    responses={"help": "support response", "price": "sales response"},
                )
            )
            response = flow.process_turn("I need help with login.", session_id="schema-test")

            self.assertEqual(response.agent_name, "support")
            self.assertIn("support", response.content.lower())


if __name__ == "__main__":
    unittest.main()
