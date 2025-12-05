import os
from aghenticMinds import Expert, Router, Flow
from aghenticMinds.llm import GeminiLLM

# 1. Setup LLM
# Ensure GOOGLE_API_KEY is set in your environment
# os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY" 
llm = GeminiLLM(model_name="gemini-2.0-flash", api_key=os.getenv("GOOGLE_API_KEY", ""))

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
response = flow.process_turn("I have a problem with my account.")
print(f"Agent: {response.agent_name}")
print(f"Response: {response.content}")

print("\n--- Turn 2 ---")
response = flow.process_turn("How much does the premium plan cost?")
print(f"Agent: {response.agent_name}")
print(f"Response: {response.content}")
