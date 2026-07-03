import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gentis_ai import Expert, Flow, Router
from gentis_ai.llm import MockLLM

llm = MockLLM(
    routing_rules={"problem": "support", "cost": "sales"},
    responses={
        "problem": "I can help troubleshoot that.",
        "cost": "The premium plan starts at $29/month.",
    },
)

support_expert = Expert(
    name="support",
    description="Handles technical support queries.",
)

sales_expert = Expert(
    name="sales",
    description="Handles sales inquiries and pricing.",
)

router = Router(experts=[support_expert, sales_expert], llm=llm)
flow = Flow(router=router, llm=llm)

print("--- Turn 1 ---")
response = flow.process_turn("I have a problem with my account.", session_id="simple")
print(f"Agent: {response.agent_name}")
print(f"Response: {response.content}")
print(f"Token Usage: {response.token_usage}")

print("\n--- Turn 2 ---")
response = flow.process_turn("How much does the premium plan cost?", session_id="simple")
print(f"Agent: {response.agent_name}")
print(f"Response: {response.content}")
print(f"Token Usage: {response.token_usage}")
