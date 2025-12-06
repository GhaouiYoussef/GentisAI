import os
from aghentic_minds import Expert, Router, Flow
from aghentic_minds.llm import MockLLM
from aghentic_minds.utils import Colors

# 1. Setup Mock LLM (No API Key needed for testing)
# In a real app, use: from aghentic_minds.llm import GeminiLLM
llm = MockLLM(
    responses={
        "problem": "I can help with that. What seems to be the issue?",
        "cost": "Our premium plan starts at $29/month.",
    },
    routing_rules={
        "problem": "support",
        "cost": "sales"
    },
    default_response="I'm not sure how to help with that, but I'm learning!"
)

# 2. Define Experts
support_expert = Expert(
    name="support",
    description="Handles technical support queries.",
    system_prompt="You are a technical support specialist."
)

sales_expert = Expert(
    name="sales",
    description="Handles sales inquiries and pricing.",
    system_prompt="You are a sales representative."
)

# 3. Setup Router
# Note: MockLLM uses simple keyword matching for routing if configured, 
# or you can rely on its default behavior. 
# For this quick start, we'll assume the router works or defaults.
router = Router(
    experts=[support_expert, sales_expert],
    llm=llm
)

# 4. Create Flow
flow = Flow(router=router, llm=llm)

# 5. Run Conversation
print("--- Turn 1 ---")
user_input = "I have a problem with my account."
print(f"User: {user_input}")
response = flow.process_turn(user_input)
print(f"Agent: {response.agent_name}")
print(f"Response: {response.content}")

print("\n--- Turn 2 ---")
user_input = "How much does the premium plan cost?"
print(f"User: {user_input}")
response = flow.process_turn(user_input)
print(f"Agent: {response.agent_name}")
print(f"Response: {response.content}")
