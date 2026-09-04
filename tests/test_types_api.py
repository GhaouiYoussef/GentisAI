import unittest
import re
from pathlib import Path

from pydantic import ValidationError

from gentis_ai import Expert, Flow, Router
from gentis_ai.types import Message
from gentis_ai.llm import MockLLM


def test_project_version_is_0_2_1():
    root = Path(__file__).resolve().parents[1]
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', text, re.MULTILINE)
    assert match is not None
    assert match.group(1) == "0.2.1"


class TestTypesAndPublicApi(unittest.TestCase):
    def test_expert_system_prompt_defaults(self):
        expert = Expert(name="support", description="Handles support.")
        self.assertIn("support", expert.system_prompt)
        self.assertIn("Handles support.", expert.system_prompt)

    def test_message_normalizes_legacy_model_role(self):
        message = Message(role="model", content="hello")
        self.assertEqual(message.role, "assistant")

    def test_message_rejects_unknown_role(self):
        with self.assertRaises(ValidationError):
            Message(role="bot", content="hello")

    def test_minimal_import_surface_works(self):
        llm = MockLLM(routing_rules={"help": "support"}, responses={"help": "ok"})
        router = Router([Expert(name="support", description="Support.")], llm=llm)
        flow = Flow(router=router, llm=llm)
        self.assertEqual(flow.process_turn("help", session_id="api").content, "ok")


if __name__ == "__main__":
    unittest.main()
