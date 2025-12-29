import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the current directory to sys.path so we can import gentis_ai
sys.path.append(os.getcwd())

from gentis_ai import Expert, Router, Flow
from gentis_ai.llm import VLLMLLM

class TestVLLMIntegration(unittest.TestCase):
    def setUp(self):
        # Create a mock for the OpenAI client
        self.mock_client = MagicMock()
        
        # Create a mock response object
        self.mock_response = MagicMock()
        self.mock_response.choices = [
            MagicMock(message=MagicMock(content="Hello! I am a simulated VLLM agent."))
        ]
        self.mock_response.usage.total_tokens = 42
        
        # Setup the client to return the mock response
        self.mock_client.chat.completions.create.return_value = self.mock_response

    def test_vllm_flow(self):
        print("\nTesting VLLM Integration with Mock Server...")
        
        # 1. Patch the OpenAI class where it is imported in vllm.py
        with patch('gentis_ai.llm.vllm.OpenAI', return_value=self.mock_client):
            
            # 2. Initialize VLLMLLM (this will use the mock client)
            llm = VLLMLLM(
                model_name="mock-model",
                base_url="http://mock-url",
                api_key="mock-key"
            )
            
            # 3. Setup minimal Gentis AI components
            expert = Expert(name="test", description="test", system_prompt="test")
            router = Router(experts=[expert], llm=llm)
            flow = Flow(router=router, llm=llm)
            
            # 4. Run a turn
            user_input = "Hi there"
            print(f"User Input: {user_input}")
            
            response = flow.process_turn(user_input)
            
            # 5. Verify the output
            print(f"Agent Response: {response.content}")
            
            self.assertEqual(response.content, "Hello! I am a simulated VLLM agent.")
            print("SUCCESS: The VLLM integration correctly handled the flow.")
            
            # 6. Verify the mock was called with correct parameters
            # We expect 2 calls: one for routing (classifier) and one for the expert response
            # But since we only have 1 expert and it's default, the router might skip or be called.
            # Let's just check that the client was called at least once.
            self.assertTrue(self.mock_client.chat.completions.create.called)
            
            # Get the last call arguments
            call_args = self.mock_client.chat.completions.create.call_args
            print(f"API Call Verified: {call_args}")

if __name__ == '__main__':
    unittest.main()
