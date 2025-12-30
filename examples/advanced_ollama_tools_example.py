import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import random
from gentis_ai import Expert, Router, Flow
from gentis_ai.llm import OllamaLLM
from gentis_ai.utils import Colors

# Import pre-defined prompts for quick start
from gentis_ai.prompts import QUICK_START_SALES, QUICK_START_SUPPORT, QUICK_START_ORCHESTRATOR

# --- Define Tools ---

def debug_account(user_id: str) -> str:
    """
    Checks the system logs for a specific user ID to identify recent errors.
    
    Args:
        user_id: The ID of the user to debug (e.g., "user_123").
    """
    print(f"{Colors.RED}[Tool] Debugging account for {user_id}...{Colors.ENDC}")
    # Mock logic
    statuses = [
        "Account is active. No recent errors found.",
        "Error 503 detected in last login attempt. Suggest clearing cache.",
        "Payment method expired. This might be causing access issues.",
        "Account locked due to multiple failed password attempts."
    ]
    return random.choice(statuses)

def get_exclusive_deal(category: str) -> str:
    """
    Retrieves an exclusive deal or discount code for a specific product category.
    
    Args:
        category: The product category (e.g., "electronics", "clothing", "software").
    """
    print(f"{Colors.YELLOW}[Tool] Fetching deal for {category}...{Colors.ENDC}")
    # Mock logic
    deals = {
        "electronics": "Use code TECH20 for 20% off all gadgets.",
        "software": "Use code SOFT50 for 50% off annual subscriptions.",
        "clothing": "Buy one get one free on all summer items.",
        "general": "Use code WELCOME10 for 10% off your first order."
    }
    return deals.get(category.lower(), deals["general"])

def main():
    # 1. Setup LLM
    # Ensure you have Ollama running (ollama serve) and the model pulled
    llm = OllamaLLM(
        model_name="granite4:micro", 
        host="http://localhost:11434"
    )

    # 2. Load Prompts
    sales_prompt = QUICK_START_SALES
    support_prompt = QUICK_START_SUPPORT
    orch_prompt = QUICK_START_ORCHESTRATOR

    # 3. Define Experts with Tools
    sales_expert = Expert(
        name="sales",
        description="Handles sales inquiries, pricing, and product features.",
        system_prompt=sales_prompt + "\nYou have access to a tool 'get_exclusive_deal' to find discounts for customers.",
        tools=[get_exclusive_deal]
    )

    support_expert = Expert(
        name="support",
        description="Handles technical support, troubleshooting, and bugs.",
        system_prompt=support_prompt + "\nYou have access to a tool 'debug_account' to check user logs.",
        tools=[debug_account]
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

    print(f"{Colors.HEADER}=== gentis_ai Advanced Ollama Example (With Tools) ==={Colors.ENDC}")
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
