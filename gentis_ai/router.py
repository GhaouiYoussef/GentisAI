from typing import List, Optional
from .types import Expert, Message
from .llm.base import BaseLLM
from .utils import Colors

class Router:
    def __init__(self, experts: List[Expert], llm: BaseLLM, default_expert: Optional[Expert] = None, enable_hybrid: bool = True):
        self.experts = {e.name: e for e in experts}
        self.llm = llm
        self.enable_hybrid = enable_hybrid
        
        # 1. Orchestrator Default Mitigation
        # If no default expert is provided, we create a generic "Orchestrator"
        if default_expert is None:
            # Check if one of the experts is named 'orchestrator'
            if "orchestrator" in self.experts:
                self.default_expert = self.experts["orchestrator"]
            else:
                self.default_expert = Expert(
                    name="orchestrator",
                    description="Handles general queries, greetings, and routing to other experts.",
                    system_prompt="You are a helpful AI assistant. You handle general queries and help route users to the right expert if needed."
                )
                self.experts[self.default_expert.name] = self.default_expert
        else:
            self.default_expert = default_expert
            if default_expert.name not in self.experts:
                self.experts[default_expert.name] = default_expert

    def classify(self, user_message: str, current_expert_name: str, recent_history: List[str] = None) -> List[str]:
        """
        Determines the best expert(s) to handle the user message.
        Returns a list of expert names.
        """
        # Construct the classification prompt
        experts_desc = "\n".join([f"- '{name}': {expert.description}" for name, expert in self.experts.items()])
        
        history_text = ""
        if recent_history:
            history_text = "\nRecent Context:\n" + "\n".join([f"- {msg}" for msg in recent_history[-5:]])

        if self.enable_hybrid:
            task_instruction = "Task: Determine if the user's intent requires switching to a different expert, or multiple experts."
            rule_3 = "3. If the user's request involves topics from multiple experts (e.g. history AND math, or coding AND math), YOU MUST list them all (comma-separated)."
            output_instruction = 'Output ONLY the expert name(s), separated by commas if multiple.\n        Example: "history, math" or "coding, math"'
        else:
            task_instruction = "Task: Determine the SINGLE best expert to handle the user message."
            rule_3 = "3. Select the one expert that best matches the user's intent."
            output_instruction = "Output ONLY the single expert name."

        prompt = f"""
        You are an Intent Router.
        
        Current Expert: {current_expert_name}
        {history_text}
        User Message: "{user_message}"
        
        Available Experts:
        {experts_desc}
        
        {task_instruction}
        
        Rules:
        1. If the user's request matches the Current Expert's domain, keep it.
        2. If the user explicitly asks for a topic covered by another expert, switch.
        {rule_3}
        4. If unsure, or for general chit-chat, default to '{self.default_expert.name}'.
        
        {output_instruction}
        """

        try:
            # We wrap the prompt in a Message object
            messages = [Message(role="user", content=prompt)]
            
            response_text = self.llm.generate(messages=messages)
            
            # Handle generator if streaming is enabled by default (though classify shouldn't stream)
            if hasattr(response_text, '__iter__') and not isinstance(response_text, str):
                full_text = ""
                for chunk in response_text:
                    full_text += chunk
                response_text = full_text

            raw_experts = response_text.strip().split(',')
            valid_experts = []
            
            # Validate
            for raw_name in raw_experts:
                clean_name = raw_name.strip().lower()
                # We do a loose match or exact match
                for name in self.experts.keys():
                    if name.lower() == clean_name:
                        valid_experts.append(name)
                        break
            
            if not valid_experts:
                return [current_expert_name]
                
            return valid_experts
            
        except Exception as e:
            # The LLM class handles printing the specific error (e.g. API key issues)
            # We just log a small warning here to indicate routing failed.
            print(f"{Colors.YELLOW}Router warning: Failed to classify intent. Staying with {current_expert_name}.{Colors.ENDC}")
            return [current_expert_name]

    def get_expert(self, name: str) -> Expert:
        return self.experts.get(name, self.default_expert)
