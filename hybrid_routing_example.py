import os
import time
from gentis_ai.session import Flow
from gentis_ai.router import Router
from gentis_ai.types import Expert
from gentis_ai.llm.ollama import OllamaLLM
from gentis_ai.utils import Colors

# 1. Setup LLM
llm = OllamaLLM(model_name="granite4:micro")

# 2. Define Experts
math_expert = Expert(
    name="math",
    description="Expert in mathematics, calculus, algebra, and geometry.",
    system_prompt="You are a mathematician. Explain concepts clearly using mathematical notation where appropriate."
)

history_expert = Expert(
    name="history",
    description="Expert in world history, historical figures, and events.",
    system_prompt="You are a historian. Provide accurate historical context, dates, and significance of events."
)

coding_expert = Expert(
    name="coding",
    description="Expert in programming, software engineering, and code.",
    system_prompt="You are a senior software engineer. Write clean, efficient code and explain it."
)

# 3. Initialize Router and Flow
router = Router(experts=[math_expert, history_expert, coding_expert], llm=llm)
flow = Flow(router=router, llm=llm, debug=True, parallel_execution=True)

def chat_loop():
    print(f"{Colors.GREEN}=== gentis_ai Hybrid Routing Example ==={Colors.ENDC}")
    print("Type 'exit' to quit.\n")
    
    user_id = "user_hybrid_test"
    
    while True:
        try:
            user_input = input(f"{Colors.BOLD}You: {Colors.ENDC}")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            print(f"{Colors.BLUE}Agent is thinking... (Hybrid Routing enabled){Colors.ENDC}")
            start_time = time.time()
            
            # We use stream=True to see the synthesis happening in real-time
            response = flow.process_turn(user_input, user_id=user_id, stream=True)
            end_time = time.time()
            
            print(f"\n{Colors.CYAN}Time taken: {end_time - start_time:.2f}s | Agent: {response.agent_name}{Colors.ENDC}\n")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.ENDC}")

if __name__ == "__main__":
    chat_loop()
