from typing import List, Optional
from .types import Agent
try:
    from google import genai
except ImportError:
    genai = None

class Router:
    def __init__(self, agents: List[Agent], default_agent: Optional[Agent] = None, api_key: str = None):
        self.agents = {a.name: a for a in agents}
        
        # 1. Orchestrator Default Mitigation
        # If no default agent is provided, we create a generic "Orchestrator"
        if default_agent is None:
            # Check if one of the agents is named 'orchestrator'
            if "orchestrator" in self.agents:
                self.default_agent = self.agents["orchestrator"]
            else:
                self.default_agent = Agent(
                    name="orchestrator",
                    description="Handles general queries, greetings, and routing to other experts.",
                    system_prompt="You are a helpful AI assistant. You handle general queries and help route users to the right expert if needed."
                )
                self.agents[self.default_agent.name] = self.default_agent
        else:
            self.default_agent = default_agent
            if default_agent.name not in self.agents:
                self.agents[default_agent.name] = default_agent

        self.api_key = api_key
        self._client = None
        
        if api_key and genai:
            self._client = genai.Client(api_key=api_key)

    def classify(self, user_message: str, current_agent_name: str, recent_history: List[str] = None) -> str:
        """
        Determines the best agent to handle the user message.
        """
        if not self._client:
            return current_agent_name

        # Construct the classification prompt
        agents_desc = "\n".join([f"- '{name}': {agent.description}" for name, agent in self.agents.items()])
        
        history_text = ""
        if recent_history:
            history_text = "\nRecent Context:\n" + "\n".join([f"- {msg}" for msg in recent_history[-5:]])

        prompt = f"""
        You are an Intent Router.
        
        Current Agent: {current_agent_name}
        {history_text}
        User Message: "{user_message}"
        
        Available Agents:
        {agents_desc}
        
        Task: Determine if the user's intent requires switching to a different agent.
        
        Rules:
        1. If the user's request matches the Current Agent's domain, keep it.
        2. If the user explicitly asks for a topic covered by another agent, switch.
        3. If unsure, or for general chit-chat, default to '{self.default_agent.name}'.
        
        Output ONLY the agent name.
        """

        try:
            response = self._client.models.generate_content(
                model="gemini-2.0-flash-lite", # Fast model for routing
                contents=prompt
            )
            predicted_agent = (getattr(response, "text", None) or "").strip().lower()
            
            # Validate
            # We do a loose match or exact match
            for name in self.agents.keys():
                if name.lower() == predicted_agent:
                    return name
            
            return current_agent_name
            
        except Exception as e:
            print(f"Router Error: {e}")
            return current_agent_name

    def get_agent(self, name: str) -> Agent:
        return self.agents.get(name, self.default_agent)
