import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from gentis_ai import Expert, Router, Flow
from gentis_ai.llm import OllamaLLM
from gentis_ai.utils import Colors

# Import pre-defined prompts for quick start
from gentis_ai.prompts import QUICK_START_SALES, QUICK_START_SUPPORT, QUICK_START_ORCHESTRATOR

def main():
    # 1. Setup LLM
    llm = OllamaLLM(
        model_name="granite4:micro", 
        host="http://localhost:11434"
    )

    # 2. Define Experts
    sales_expert = Expert(
        name="sales",
        description="Handles sales inquiries, pricing, and product features.",
        system_prompt=QUICK_START_SALES
    )

    support_expert = Expert(
        name="support",
        description="Handles technical support, troubleshooting, and bugs.",
        system_prompt=QUICK_START_SUPPORT
    )

    orchestrator = Expert(
        name="orchestrator",
        description="The central guide. Routes users to Sales or Support.",
        system_prompt=QUICK_START_ORCHESTRATOR
    )

    # 3. Setup Router & Flow
    router = Router(
        experts=[sales_expert, support_expert, orchestrator],
        llm=llm,
        default_expert=orchestrator
    )

    flow = Flow(router=router, llm=llm, debug=True)

    print(f"{Colors.HEADER}=== gentis_ai Streaming Example ==={Colors.ENDC}")
    print("Type 'exit' to quit.\n")

    user_id = "user_stream_1"
    
    while True:
        try:
            user_input = input(f"{Colors.GREEN}You: {Colors.ENDC}")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            print(f"{Colors.BLUE}Agent is thinking... (Streaming enabled){Colors.ENDC}")
            start_time = time.time()
            response = None
            for event in flow.stream_turn(user_input, session_id=user_id):
                if event.type == "token":
                    print(event.content, end="", flush=True)
                elif event.type == "final":
                    response = event.data["response"]
                    print()
            end_time = time.time()

            if response is None:
                continue
            print(f"\n{Colors.CYAN}Time taken: {end_time - start_time:.2f}s | Agent: {response.agent_name}{Colors.ENDC}\n")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
