from typing import List, Any
from .types import Message

class MemoryOptimizer:
    """
    Handles the pruning and sanitization of conversation history.
    """
    
    @staticmethod
    def prune(history: List[Message], max_turns: int = 20) -> List[Message]:
        """
        Keeps the history within a manageable size.
        """
        # Simple truncation for now, but can be enhanced with summarization
        if len(history) > max_turns * 2:
            return history[-(max_turns * 2):]
        return history

    @staticmethod
    def sanitize_for_switch(history: List[Message]) -> List[Message]:
        """
        Cleans up history when switching agents.
        Removes old system prompts or agent-specific hints to prevent confusion.
        """
        clean_history = []
        for msg in history:
            # Skip system messages from previous turns (as we will inject a new one)
            if msg.role == "system":
                continue
            
            # Skip "Context hints" if they were injected as model messages
            if msg.role == "model" and msg.content.startswith("Context hints:"):
                continue
                
            clean_history.append(msg)
            
        return clean_history
