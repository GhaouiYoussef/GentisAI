import os
import json
import datetime
from typing import Dict, List, Any, Optional
from .types import Agent, Message, TurnResponse
from .router import Router
from .memory import MemoryOptimizer
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

class ConversationManager:
    def __init__(self, router: Router, api_key: str, debug: bool = False):
        self.router = router
        self.api_key = api_key
        self.debug = debug
        self._client = None
        if api_key and genai:
            self._client = genai.Client(api_key=api_key)
            
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

    def _log_debug_memory(self, user_id: str, agent_name: str, genai_history: List[Any]):
        """
        Logs the memory context to a file for debugging purposes.
        """
        if not self.debug:
            return

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"debug-cache/{user_id}_{timestamp}_{agent_name}.json"
        
        try:
            # Convert GenAI objects to serializable dicts
            serializable_history = []
            for item in genai_history:
                role = getattr(item, "role", "unknown")
                parts = []
                if hasattr(item, "parts"):
                    for p in item.parts:
                        if hasattr(p, "text"):
                            parts.append({"text": p.text})
                        elif hasattr(p, "function_call"):
                            parts.append({"function_call": str(p.function_call)})
                        else:
                            parts.append(str(p))
                serializable_history.append({"role": role, "parts": parts})

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(serializable_history, f, indent=2)
        except Exception as e:
            print(f"Debug Log Error: {e}")

    def process_turn(self, user_id: str, message: str) -> TurnResponse:
        session = self._get_session(user_id)
        current_agent_name = session["current_agent"]
        history = session["history"]

        # 1. Classify / Route
        # Extract simple text history for the router
        text_history = [f"{m.role}: {m.content}" for m in history[-5:]]
        next_agent_name = self.router.classify(message, current_agent_name, text_history)
        
        switched = next_agent_name != current_agent_name
        if switched:
            # Prune history to remove old system prompts
            history = MemoryOptimizer.sanitize_for_switch(history)
            session["current_agent"] = next_agent_name
            current_agent_name = next_agent_name

        current_agent = self.router.get_agent(current_agent_name)

        # 2. Prepare Context for LLM
        # Inject System Prompt
        # Note: In a real chat session, we might not want to append system prompt to history list permanently
        # but send it as part of the request.
        
        # Convert internal Message objects to GenAI Content objects
        genai_history = []
        
        # Add System Prompt
        genai_history.append(types.Content(
            role="user", # Gemini often treats system instructions better if passed in config or as first user msg
            parts=[types.Part(text=f"System Instruction: {current_agent.system_prompt}")]
        ))
        
        # Add History
        for msg in history:
            role = "model" if msg.role == "assistant" else "user"
            genai_history.append(types.Content(
                role=role,
                parts=[types.Part(text=msg.content)]
            ))
            
        # Add Current User Message
        genai_history.append(types.Content(
            role="user",
            parts=[types.Part(text=message)]
        ))

        # 2.5 Debug Logging
        self._log_debug_memory(user_id, current_agent_name, genai_history)

        # 3. Generate Response
        response_text = "Error: GenAI client not initialized."
        token_usage = {"total": 0}
        
        if self._client:
            try:
                # Configure tools if the agent has them
                tool_config = None
                if current_agent.tools:
                    tool_config = types.GenerateContentConfig(
                        tools=current_agent.tools,
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
                    )

                chat = self._client.chats.create(
                    model=current_agent.model_name,
                    history=genai_history[:-1], # History excluding the new message
                    config=tool_config
                )
                
                resp = chat.send_message(message)
                response_text = getattr(resp, "text", "") or ""
                
                # Track usage
                if resp.usage_metadata:
                    token_usage["total"] = resp.usage_metadata.total_token_count

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
