import os
import time
import sys
from dotenv import load_dotenv
from gentis_ai.session import Flow
from gentis_ai.router import Router
from gentis_ai.types import Expert
from gentis_ai.llm.gemini import GeminiLLM
from gentis_ai.utils import Colors

# Load environment variables
load_dotenv()

def run_test():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print(f"{Colors.RED}Error: GOOGLE_API_KEY not found in environment.{Colors.ENDC}")
        print("Please set it in your .env file or environment variables.")
        return

    print(f"{Colors.GREEN}=== Gemini Parallel Execution Benchmark ==={Colors.ENDC}")
    
    # 1. Setup LLM
    # Using Flash Lite for speed, but the network latency will still be measurable
    llm = GeminiLLM(api_key=api_key, model_name="gemini-2.5-flash")

    # 2. Define Experts
    history_expert = Expert(
        name="history",
        description="Expert in world history, historical figures, and events.",
        system_prompt="You are a historian. Provide detailed historical context."
    )

    coding_expert = Expert(
        name="coding",
        description="Expert in programming, software engineering, and code.",
        system_prompt="You are a senior software engineer. Write clean, efficient code."
    )

    # 3. Define Query
    # A query that forces both experts to work
    query = "Explain the historical significance of the Enigma machine and write a Python script to simulate a simple substitution cipher."

    # --- Test 1: Sequential ---
    print(f"\n{Colors.YELLOW}--- Test 1: Sequential Execution (parallel_execution=False) ---{Colors.ENDC}")
    router_seq = Router(experts=[history_expert, coding_expert], llm=llm)
    flow_seq = Flow(router=router_seq, llm=llm, debug=False, parallel_execution=False)
    
    start_seq = time.time()
    print("Processing...")
    flow_seq.process_turn(query, user_id="test_seq")
    end_seq = time.time()
    time_seq = end_seq - start_seq
    print(f"Sequential Time: {time_seq:.2f}s")

    # --- Test 2: Parallel ---
    print(f"\n{Colors.BLUE}--- Test 2: Parallel Execution (parallel_execution=True) ---{Colors.ENDC}")
    router_par = Router(experts=[history_expert, coding_expert], llm=llm)
    flow_par = Flow(router=router_par, llm=llm, debug=False, parallel_execution=True)
    
    start_par = time.time()
    print("Processing...")
    flow_par.process_turn(query, user_id="test_par")
    end_par = time.time()
    time_par = end_par - start_par
    print(f"Parallel Time:   {time_par:.2f}s")

    # --- Results ---
    print(f"\n{Colors.GREEN}=== Results ==={Colors.ENDC}")
    print(f"Sequential: {time_seq:.2f}s")
    print(f"Parallel:   {time_par:.2f}s")
    
    if time_par < time_seq:
        improvement = ((time_seq - time_par) / time_seq) * 100
        print(f"{Colors.BOLD}Speedup: {improvement:.1f}%{Colors.ENDC}")
    else:
        print("No speedup observed (network latency might be low or variable).")

if __name__ == "__main__":
    run_test()
