from typing import List, Any
from .types import Message

class PNNet:
    """
    Handles the pruning and sanitization of conversation history.
    (Tiny PNNet interface)
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
        Cleans up history when switching experts.
        Removes old system prompts or expert-specific hints to prevent confusion.
        """
        clean_history = []
        for msg in history:
            # Skip system messages from previous turns (as we will inject a new one)
            if msg.role == "system":
                # Exception: Keep summaries
                if msg.content.startswith("Previous conversation summary:"):
                    clean_history.append(msg)
                continue
            
            # Skip "Context hints" if they were injected as model messages
            if msg.role == "model" and msg.content.startswith("Context hints:"):
                continue
                
            clean_history.append(msg)
            
        return clean_history

    @staticmethod
    def summarize_if_needed(history: List[Message], llm: Any, token_limit: int = 500, target_tokens: int = 150) -> List[Message]:
        """
        Checks if history exceeds token_limit. If so, summarizes the older part to target_tokens.
        """
        # 1. Count tokens
        full_text = "\n".join([f"{msg.role}: {msg.content}" for msg in history])
        
        current_tokens = 0
        if hasattr(llm, "count_tokens"):
            current_tokens = llm.count_tokens(full_text)
        else:
            current_tokens = len(full_text) // 4
            
        if current_tokens <= token_limit:
            return history
            
        # 2. Summarize
        # Keep last 2 turns (4 messages)
        if len(history) <= 4:
            return history
            
        messages_to_summarize = history[:-4]
        recent_messages = history[-4:]
        
        text_to_summarize = "\n".join([f"{msg.role}: {msg.content}" for msg in messages_to_summarize])
        
        prompt = f"Summarize the following conversation history into a concise summary of approximately {target_tokens} tokens. Preserve key information and context.\n\n{text_to_summarize}"
        
        try:
            summary_text = llm.generate(
                messages=[Message(role="user", content=prompt)],
                system_prompt="You are a helpful assistant that summarizes conversation history."
            )
            
            # Create new history with summary
            summary_msg = Message(role="system", content=f"Previous conversation summary: {summary_text}")
            return [summary_msg] + recent_messages
            
        except Exception as e:
            print(f"Summarization failed: {e}")
            return history
