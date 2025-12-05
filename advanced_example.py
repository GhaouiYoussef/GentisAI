import os
import sys
from aghenticMinds import Expert, Router, Flow
from aghenticMinds.llm import GeminiLLM
from aghenticMinds.utils import Colors

# Import pre-defined prompts for quick start
from aghenticMinds.prompts import QUICK_START_SALES, QUICK_START_SUPPORT, QUICK_START_ORCHESTRATOR

from dotenv import load_dotenv
load_dotenv()

def main():
    # 1. Setup LLM
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        print("Please set the GOOGLE_API_KEY environment variable.")
        return

    llm = GeminiLLM(model_name="gemini-2.0-flash", api_key=api_key)

    # 2. Load Prompts (Now using imported constants)
    sales_prompt = QUICK_START_SALES
    support_prompt = QUICK_START_SUPPORT
    orch_prompt = QUICK_START_ORCHESTRATOR

    # 3. Define Experts
    sales_expert = Expert(
        name="sales",
        description="Handles sales inquiries, pricing, and product features.",
        system_prompt=sales_prompt
    )

    support_expert = Expert(
        name="support",
        description="Handles technical support, troubleshooting, and bugs.",
        system_prompt=support_prompt
    )

    orchestrator = Expert(
        name="orchestrator",
        description="The central guide. Routes users to Sales or Support.",
        system_prompt=orch_prompt
    )

    # 4. Setup Router
    # We pass the orchestrator as the default_expert
    router = Router(
        experts=[sales_expert, support_expert, orchestrator],
        llm=llm,
        default_expert=orchestrator
    )

    # 5. Create Flow
    flow = Flow(router=router, llm=llm, debug=True)

    print(f"{Colors.HEADER}=== aghenticMinds Advanced Example ==={Colors.ENDC}")
    print("Type 'exit' to quit.\n")

    # 6. Interactive Loop
    user_id = "user_123"
    
    while True:
        try:
            user_input = input(f"{Colors.GREEN}You: {Colors.ENDC}")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            response = flow.process_turn(user_input, user_id=user_id)
            
            agent_color = Colors.BLUE
            if response.agent_name == "sales":
                agent_color = Colors.YELLOW
            elif response.agent_name == "support":
                agent_color = Colors.RED
            
            print(f"{agent_color}[{response.agent_name.upper()}]: {Colors.ENDC}{response.content}\n")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
