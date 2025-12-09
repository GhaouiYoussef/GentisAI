import unittest
from aghentic_minds.session import Flow
from aghentic_minds.router import Router
from aghentic_minds.types import Expert, Message
from aghentic_minds.llm.mock import MockLLM

class TestTokenUsage(unittest.TestCase):
    def setUp(self):
        self.experts = [
            Expert(name="orchestrator", description="General", system_prompt="sys")
        ]
        self.mock_llm = MockLLM(
            responses={"hello": "Hello there!"}
        )
        self.router = Router(self.experts, self.mock_llm)
        self.flow = Flow(self.router, self.mock_llm)

    def test_mock_llm_token_usage(self):
        # Test direct LLM usage
        messages = [Message(role="user", content="hello")]
        self.mock_llm.generate(messages)
        usage = self.mock_llm.get_token_usage()
        
        self.assertIn("total", usage)
        self.assertIn("prompt_tokens", usage)
        self.assertIn("completion_tokens", usage)
        self.assertGreater(usage["total"], 0)
        
        # Verify calculation (MockLLM uses len/4)
        # Input: "hello" (5 chars) -> 1 token
        # Output: "Hello there!" (12 chars) -> 3 tokens
        # Total: 4
        self.assertEqual(usage["prompt_tokens"], 1)
        self.assertEqual(usage["completion_tokens"], 3)
        self.assertEqual(usage["total"], 4)
        
    def test_flow_token_usage(self):
        # Test usage via Flow
        response = self.flow.process_turn("hello", user_id="test_user")
        
        self.assertIsNotNone(response.token_usage)
        self.assertIn("total", response.token_usage)
        self.assertGreater(response.token_usage["total"], 0)
        
        print(f"Token usage for turn: {response.token_usage}")

if __name__ == '__main__':
    unittest.main()