from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict
from ..types import Message

class BaseLLM(ABC):
    """
    Abstract Base Class for LLM providers.
    """
    
    @abstractmethod
    def generate(self, messages: List[Message], system_prompt: str = None, tools: List[Any] = None, **kwargs) -> str:
        """
        Generates a response from the LLM.
        
        Args:
            messages: The conversation history.
            system_prompt: Optional system instruction.
            tools: Optional list of tools/functions.
            **kwargs: Additional model-specific parameters (e.g., temperature).
            
        Returns:
            The string response content.
        """
        pass

    @abstractmethod
    def get_token_usage(self) -> Dict[str, int]:
        """
        Returns the token usage of the last call.
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Counts the number of tokens in the given text.
        """
        pass
