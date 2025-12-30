import unittest
from gentis_ai.router import Router
from gentis_ai.types import Expert
from gentis_ai.llm.mock import MockLLM

class TestRouter(unittest.TestCase):
    def setUp(self):
        self.experts = [
            Expert(name="orchestrator", description="General", system_prompt="sys"),
            Expert(name="sales", description="Sales expert", system_prompt="sales sys"),
            Expert(name="support", description="Support expert", system_prompt="support sys")
        ]
        self.mock_llm = MockLLM(routing_rules={
            "buy": "sales",
            "help": "support",
            "hello": "orchestrator"
        })
        self.router = Router(self.experts, self.mock_llm)

    def test_default_expert(self):
        self.assertEqual(self.router.default_expert.name, "orchestrator")

    def test_classify_sales(self):
        expert = self.router.classify("I want to buy something", "orchestrator")
        self.assertEqual(expert, ["sales"])

    def test_classify_support(self):
        expert = self.router.classify("I need help", "orchestrator")
        self.assertEqual(expert, ["support"])

    def test_classify_no_change(self):
        # MockLLM returns "orchestrator" if no rule matches (default behavior in my mock setup)
        expert = self.router.classify("random text", "orchestrator")
        self.assertEqual(expert, ["orchestrator"])

if __name__ == '__main__':
    unittest.main()
