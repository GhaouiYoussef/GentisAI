import unittest
from gentis_ai.router import Router
from gentis_ai.types import Expert
from gentis_ai.llm.base import BaseLLM
from gentis_ai.llm.mock import MockLLM


class StaticLLM(BaseLLM):
    def __init__(self, response):
        self.response = response

    def generate(self, messages, system_prompt=None, tools=None, stream=False, **kwargs):
        return self.response

    def get_token_usage(self):
        return {"total": 0}

    def count_tokens(self, text):
        return len(text) // 4


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
        decision = self.router.classify("I want to buy something", "orchestrator")
        self.assertEqual(decision.experts, ["sales"])
        self.assertEqual(decision.mode, "single")

    def test_classify_support(self):
        decision = self.router.classify("I need help", "orchestrator")
        self.assertEqual(decision.experts, ["support"])

    def test_classify_no_change(self):
        decision = self.router.classify("random text", "orchestrator")
        self.assertEqual(decision.experts, ["orchestrator"])

    def test_classify_names_backcompat_helper(self):
        names = self.router.classify_names("I need help", "orchestrator")
        self.assertEqual(names, ["support"])

    def test_hybrid_json_response(self):
        router = Router(
            self.experts,
            StaticLLM('{"experts":["sales","support"],"mode":"hybrid","confidence":0.9}'),
        )
        decision = router.classify("billing bug", "orchestrator")
        self.assertEqual(decision.experts, ["sales", "support"])
        self.assertEqual(decision.mode, "hybrid")

    def test_unknown_expert_falls_back_to_current(self):
        router = Router(
            self.experts,
            StaticLLM('{"experts":["unknown"],"mode":"single","confidence":0.9}'),
        )
        decision = router.classify("anything", "support")
        self.assertEqual(decision.experts, ["support"])
        self.assertEqual(decision.mode, "fallback")

    def test_low_confidence_falls_back(self):
        router = Router(
            self.experts,
            StaticLLM('{"experts":["sales"],"mode":"single","confidence":0.1}'),
            confidence_threshold=0.5,
        )
        decision = router.classify("maybe buy", "support")
        self.assertEqual(decision.experts, ["support"])
        self.assertEqual(decision.mode, "fallback")

    def test_malformed_response_falls_back(self):
        router = Router(self.experts, StaticLLM("not an expert"))
        decision = router.classify("anything", "support")
        self.assertEqual(decision.experts, ["support"])
        self.assertEqual(decision.mode, "fallback")

    def test_keyword_router_without_llm(self):
        router = Router(self.experts, llm=None, rules={"buy": "sales"})
        decision = router.classify("I want to buy", "orchestrator")
        self.assertEqual(decision.experts, ["sales"])

if __name__ == '__main__':
    unittest.main()
