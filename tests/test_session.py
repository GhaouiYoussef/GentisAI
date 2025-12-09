import unittest
from gentis_ai.session import Flow
from gentis_ai.router import Router
from gentis_ai.types import Expert
from gentis_ai.llm.mock import MockLLM

class TestSession(unittest.TestCase):
    def setUp(self):
        self.experts = [
            Expert(name="orchestrator", description="General", system_prompt="sys"),
            Expert(name="sales", description="Sales expert", system_prompt="sales sys")
        ]
        self.mock_llm = MockLLM(
            responses={"hello": "Hello there!", "buy": "Sure, what do you want?"},
            routing_rules={"buy": "sales", "hello": "orchestrator"}
        )
        self.router = Router(self.experts, self.mock_llm)
        self.flow = Flow(self.router, self.mock_llm)

    def test_process_turn_no_switch(self):
        response = self.flow.process_turn("hello", user_id="user1")
        self.assertEqual(response.agent_name, "orchestrator")
        self.assertEqual(response.content, "Hello there!")
        self.assertFalse(response.switched_context)

    def test_process_turn_switch(self):
        # First turn to set context
        self.flow.process_turn("hello", user_id="user1")
        
        # Second turn triggers switch
        response = self.flow.process_turn("I want to buy", user_id="user1")
        self.assertEqual(response.agent_name, "sales")
        self.assertTrue(response.switched_context)

    def test_session_persistence(self):
        self.flow.process_turn("hello", user_id="user1")
        session = self.flow._get_session("user1")
        self.assertEqual(len(session["history"]), 2) # User + Assistant

        # New user should have empty history
        session2 = self.flow._get_session("user2")
        self.assertEqual(len(session2["history"]), 0)

if __name__ == '__main__':
    unittest.main()
