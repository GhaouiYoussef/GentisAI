from typing import List, Any, Dict
from ..types import Message
from .base import BaseLLM

class MockLLM(BaseLLM):
    """
    A Mock LLM for testing purposes.
    Returns predefined responses or echoes input.
    """
    def __init__(self, responses: Dict[str, str] = None, routing_rules: Dict[str, str] = None, default_response: str = "Mock Response"):
        self.responses = responses or {}
        self.routing_rules = routing_rules or {}
        self.default_response = default_response
        self._last_usage = {"total": 0}

    def generate(self, messages: List[Message], system_prompt: str = None, tools: List[Any] = None, **kwargs) -> str:
        last_msg = messages[-1].content if messages else ""
        response_text = self.default_response
        
        # 1. Handle Routing Requests (detected via Router prompt signature)
        if "You are an Intent Router" in last_msg:
            # Extract the User Message line to avoid matching history
            import re
            match = re.search(r'User Message: "(.*?)"', last_msg, re.DOTALL)
            target_text = match.group(1) if match else last_msg

            response_text = "orchestrator"
            for keyword, agent_name in self.routing_rules.items():
                if keyword.lower() in target_text.lower():
                    response_text = agent_name
                    break
        else:
            # 2. Handle Conversation Requests (Substring match)
            for key, response in self.responses.items():
                if key.lower() in last_msg.lower():
                    response_text = response
                    break
            
        # Calculate tokens
        input_text = (system_prompt or "") + "".join([m.content for m in messages])
        input_tokens = self.count_tokens(input_text)
        output_tokens = self.count_tokens(response_text)
        
        self._last_usage = {
            "prompt_tokens": input_tokens,
            "completion_tokens": output_tokens,
            "total": input_tokens + output_tokens
        }
        
        return response_text

    def get_token_usage(self) -> Dict[str, int]:
        return self._last_usage

    def count_tokens(self, text: str) -> int:
        return len(text) // 4
