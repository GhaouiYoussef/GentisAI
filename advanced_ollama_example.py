import os
import sys
from gentis_ai import Expert, Router, Flow
from gentis_ai.llm import OllamaLLM
from gentis_ai.utils import Colors

# Import pre-defined prompts for quick start
from gentis_ai.prompts import QUICK_START_SALES, QUICK_START_SUPPORT, QUICK_START_ORCHESTRATOR

def main():
    # 1. Setup LLM
    # Ensure you have Ollama running (ollama serve) and the model pulled
    # Example: ollama pull granite4:micro
    llm = OllamaLLM(
        model_name="granite4:micro", 
        host="http://localhost:11434"
    )

    # 2. Load Prompts
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
    router = Router(
        experts=[sales_expert, support_expert, orchestrator],
        llm=llm,
        default_expert=orchestrator
    )

    # 5. Create Flow
    flow = Flow(router=router, llm=llm, debug=True)

    print(f"{Colors.HEADER}=== gentis_ai Advanced Ollama Example ==={Colors.ENDC}")
    print("Type 'exit' to quit.\n")

    # 6. Interactive Loop
    user_id = "user_ollama_1"
    
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
            print(f"{Colors.CYAN}Token Usage: {response.token_usage}{Colors.ENDC}\n")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
