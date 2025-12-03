import os
import json
import datetime
from typing import Dict, List, Any, Optional
from .types import Agent, Message, TurnResponse
from .router import Router
from .memory import MemoryOptimizer
from .llm.base import BaseLLM
from .utils import Colors
class ConversationManager:
    def __init__(self, router: Router, llm: BaseLLM, debug: bool = False):
        self.router = router
        self.llm = llm
        self.debug = debug
            
        # In-memory storage for demo purposes. 
        # In production, this should be replaced by a persistent store (Redis/Mongo).
        self._sessions: Dict[str, Dict[str, Any]] = {} 
        
        # Ensure debug cache directory exists
        if self.debug:
            os.makedirs("debug-cache", exist_ok=True)

    def _get_session(self, user_id: str) -> Dict[str, Any]:
        if user_id not in self._sessions:
            self._sessions[user_id] = {
                "history": [],
                "current_agent": self.router.default_agent.name
            }
        return self._sessions[user_id]

    def _log_debug_memory(self, user_id: str, agent_name: str, history: List[Message]):
        """
        Logs the memory context to a file for debugging purposes.
        """
        if not self.debug:
            return

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"debug-cache/{user_id}_{timestamp}_{agent_name}.json"
        
        try:
            # Convert Message objects to serializable dicts
            serializable_history = [msg.model_dump() for msg in history]

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(serializable_history, f, indent=2)
        except Exception as e:
            print(f"Debug Log Error: {e}")

    def process_turn(self, message: str, user_id: Optional[str] = None) -> TurnResponse:
        session = self._get_session(user_id)
        current_agent_name = session["current_agent"]
        history = session["history"]

        # 1. Classify / Route
        # Extract simple text history for the router
        text_history = [f"{m.role}: {m.content}" for m in history[-5:]]
        next_agent_name = self.router.classify(message, current_agent_name, text_history)
        
        switched = next_agent_name != current_agent_name
        if switched:

            print(f"{Colors.CYAN}--------Switched context from {current_agent_name} to {next_agent_name}------{Colors.ENDC}")
            # Prune history to remove old system prompts
            history = MemoryOptimizer.sanitize_for_switch(history)
            session["current_agent"] = next_agent_name
            current_agent_name = next_agent_name

        current_agent = self.router.get_agent(current_agent_name)

        # 2. Prepare Context for LLM
        # We construct the messages list for the LLM
        
        # Note: In a real chat session, we might not want to append system prompt to history list permanently
        # but send it as part of the request.
        
        # 2.5 Debug Logging
        # We log the history before appending the new message for debugging state
        self._log_debug_memory(user_id, current_agent_name, history)

        # 3. Generate Response
        response_text = "Error: LLM not initialized."
        token_usage = {"total": 0}
        
        try:
            # Prepare messages for generation: History + New Message
            # We don't modify the persistent history yet
            messages_for_llm = history.copy()
            messages_for_llm.append(Message(role="user", content=message))
            
            response_text = self.llm.generate(
                messages=messages_for_llm,
                system_prompt=current_agent.system_prompt,
                tools=current_agent.tools
            )
            
            token_usage = self.llm.get_token_usage()

        except Exception as e:
            response_text = f"I encountered an error: {str(e)}"

        # 4. Update History
        # We append the user message and the assistant response to our internal history
        history.append(Message(role="user", content=message))
        history.append(Message(role="assistant", content=response_text))
        
        # Prune if too long
        session["history"] = MemoryOptimizer.prune(history)

        return TurnResponse(
            content=response_text,
            agent_name=current_agent_name,
            switched_context=switched,
            token_usage=token_usage
        )
