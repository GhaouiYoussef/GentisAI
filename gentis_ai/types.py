from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict

class Expert(BaseModel):
    """
    Defines a specific persona or expert within the system.
    """
    name: str
    system_prompt: str
    description: str
    model_name: str = "gemini-2.0-flash" # Default model for this agent
    tools: Optional[List[Any]] = None # List of callable tools

class Message(BaseModel):
    """
    Standardized message format.
    """
    role: str # 'user', 'model', 'system'
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TurnResponse(BaseModel):
    """
    The result of a single conversation turn.
    """
    content: str
    agent_name: str
    switched_context: bool
    token_usage: Dict[str, int] = Field(default_factory=lambda: {"total": 0})
