import sys
import os

# Add parent directory to path to import aghenticMinds
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aghenticMinds.session import Flow
from aghenticMinds.router import Router
from aghenticMinds.types import Expert
from aghenticMinds.llm.mock import MockLLM

def run_sanity_check():
    print("Running Sanity Check...")
    
    # Setup
    experts = [
        Expert(name="orchestrator", description="General", system_prompt="sys"),
        Expert(name="tech", description="Tech expert", system_prompt="tech sys")
    ]
    
    mock_llm = MockLLM(
        responses={
            "hi": "Hello!",
            "code": "Here is some code."
        },
        routing_rules={
            "code": "tech",
            "hi": "orchestrator"
        }
    )
    
    router = Router(experts, mock_llm)
    flow = Flow(router, mock_llm)
    
    # Step 1: General query
    print("Step 1: General query")
    resp1 = flow.process_turn("hi", user_id="sanity_user")
    assert resp1.expert_name == "orchestrator", f"Expected orchestrator, got {resp1.expert_name}"
    assert resp1.response == "Hello!", f"Expected 'Hello!', got '{resp1.response}'"
    print("Step 1 Passed.")
    
    # Step 2: Switch context
    print("Step 2: Switch context")
    resp2 = flow.process_turn("write some code", user_id="sanity_user")
    assert resp2.expert_name == "tech", f"Expected tech, got {resp2.expert_name}"
    assert resp2.switched == True, "Expected switched=True"
    print("Step 2 Passed.")
    
    print("Sanity Check Complete: SUCCESS")

if __name__ == "__main__":
    run_sanity_check()
