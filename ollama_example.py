import os
from gentis_ai import Expert, Router, Flow
from gentis_ai.llm import OllamaLLM

# 1. Setup LLM
# Ensure you have Ollama running (ollama serve) and the model pulled (ollama pull llama3)
llm = OllamaLLM(
    model_name="granite4:micro", # Change to your installed model
    host="http://localhost:11434" # Default Ollama host
)

# 2. Define Experts
support_expert = Expert(
    name="support",
    description="Handles technical support queries.",
    system_prompt="You are a technical support specialist. Help users with their issues."
)

sales_expert = Expert(
    name="sales",
    description="Handles sales inquiries and pricing.",
    system_prompt="You are a sales representative. Answer questions about pricing and features."
)

# 3. Setup Router
router = Router(
    experts=[support_expert, sales_expert],
    llm=llm
)

# 4. Create Flow
flow = Flow(router=router, llm=llm) 

# 5. Run Conversation
print("--- Turn 1 ---")
try:
    response = flow.process_turn("I have a problem with my account.")
    print(f"Agent: {response.agent_name}")
    print(f"Response: {response.content}")
    print(f"Token Usage: {response.token_usage}")

    print("\n--- Turn 2 ---")
    response = flow.process_turn("How much does the premium plan cost?")
    print(f"Agent: {response.agent_name}")
    print(f"Response: {response.content}")
    print(f"Token Usage: {response.token_usage}")
except Exception as e:
    print(f"Error: {e}")
    print("Make sure Ollama is running and you have pulled the model (e.g., 'ollama pull llama3')")
