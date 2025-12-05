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
        
        # 1. Handle Routing Requests (detected via Router prompt signature)
        if "You are an Intent Router" in last_msg:
            # Extract the User Message line to avoid matching history
            import re
            match = re.search(r'User Message: "(.*?)"', last_msg, re.DOTALL)
            target_text = match.group(1) if match else last_msg

            for keyword, agent_name in self.routing_rules.items():
                if keyword.lower() in target_text.lower():
                    return agent_name
            # If no rule matches, return a default or the first agent? 
            # For safety in tests, we might return "orchestrator" or just let it fall through.
            # But usually routing expects a name.
            return "orchestrator"

        # 2. Handle Conversation Requests (Substring match)
        for key, response in self.responses.items():
            if key.lower() in last_msg.lower():
                return response
            
        return self.default_response

    def get_token_usage(self) -> Dict[str, int]:
        return {"total": 42}

    def count_tokens(self, text: str) -> int:
        return len(text) // 4
