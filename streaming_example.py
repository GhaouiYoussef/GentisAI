import os
import sys
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
            
            # We enable streaming here
            # Note: In the current implementation of process_turn, it consumes the stream internally
            # to update history, so we won't see the character-by-character effect in the console 
            # unless we modify process_turn to yield chunks or take a callback.
            # However, this proves the API accepts the flag.
            
            print(f"{Colors.BLUE}Agent is thinking... (Streaming enabled){Colors.ENDC}")
            start_time = time.time()
            
            # We print the agent name prefix first
            # Note: We don't know the agent name until AFTER classification, which happens inside process_turn.
            # So the streaming output will appear, and then we print the summary below.
            
            response = flow.process_turn(user_input, user_id=user_id, stream=True)
            end_time = time.time()
            
            # Since we printed the stream directly to stdout in process_turn, 
            # we don't need to print response.content again here.
            
            print(f"\n{Colors.CYAN}Time taken: {end_time - start_time:.2f}s | Agent: {response.agent_name}{Colors.ENDC}\n")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
