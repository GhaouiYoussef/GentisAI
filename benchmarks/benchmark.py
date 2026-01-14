import os
import time
import asyncio
from dotenv import load_dotenv
from gentis_ai import Expert, Router, Flow
from gentis_ai.llm import GeminiLLM
from gentis_ai.types import Message
from gentis_ai.prompts import QUICK_START_SUPPORT, QUICK_START_ORCHESTRATOR, QUICK_START_SALES

from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()

# Configuration
MODEL_NAME = "gemini-2.5-flash" # Using available model from list
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    print("Error: GOOGLE_API_KEY not found in .env")
    exit(1)

# Scenario: Sales & Support Switching
TURNS = [
    "I can't log in to my account. It keeps spinning.",
    "Okay, clearing the cache worked. Thanks. I'm actually interested in upgrading my plan. What are the options?",
    "How much does the Enterprise plan cost for 10 users?"
]

def log_to_file(filename, content):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(content + "\n")

# --- GentisAI Setup ---
def run_gentis_ai():
    filename = "comparison/gentis_ai_results.txt"
    if os.path.exists(filename): os.remove(filename)
    
    log_to_file(filename, "--- Starting GentisAI Benchmark ---")
    print("\n--- Starting GentisAI Benchmark ---")
    start_time = time.time()
    
    # 1. Setup LLM
    llm = GeminiLLM(model_name=MODEL_NAME, api_key=API_KEY)
    
    # 2. Define Experts
    # Orchestrator (Default) acts as the central guide
    orchestrator = Expert(
        name="orchestrator",
        description="The central guide. Routes users to Support or Sales.",
        system_prompt=QUICK_START_ORCHESTRATOR
    )
    
    support_expert = Expert(
        name="SupportExpert",
        description="Diagnose technical issues, login problems, and bugs.",
        system_prompt=QUICK_START_SUPPORT
    )
    
    sales_expert = Expert(
        name="SalesExpert",
        description="Handle pricing inquiries, plan upgrades, and product features.",
        system_prompt=QUICK_START_SALES
    )
    
    # 3. Setup Router
    # Note: The default expert (Orchestrator) will handle the initial triage/clarification
    router = Router(experts=[support_expert, sales_expert, orchestrator], llm=llm, default_expert=orchestrator)
    
    # 4. Create Flow
    flow = Flow(router=router, llm=llm)
    
    total_tokens = 0
    total_latency = 0
    
    for i, user_input in enumerate(TURNS):
        # Sleep to avoid rate limits
        if i > 0:
            print("Sleeping for 60s to respect rate limits...")
            time.sleep(60)
        
        turn_start = time.time()
        log_to_file(filename, f"\n--- Turn {i+1} ---")
        log_to_file(filename, f"User: {user_input}")
        print(f"Turn {i+1} User: {user_input}")
        
        try:
            response = flow.process_turn(user_input, user_id="benchmark_user_am")
            
            turn_end = time.time()
            latency = (turn_end - turn_start) * 1000
            total_latency += latency
            
            tokens = response.token_usage.get("total", 0)
            total_tokens += tokens
            
            log_to_file(filename, f"Agent: {response.agent_name}")
            log_to_file(filename, f"Latency: {latency:.2f} ms")
            log_to_file(filename, f"Tokens: {tokens}")
            log_to_file(filename, f"Response:\n{response.content}\n")
            
            print(f"Turn {i+1} Agent: {response.agent_name}")
            print(f"Turn {i+1} Latency: {latency:.2f} ms")
            print(f"Turn {i+1} Tokens: {tokens}")
            
        except Exception as e:
            error_msg = f"Turn {i+1} Error: {e}"
            log_to_file(filename, error_msg)
            print(error_msg)

    end_time = time.time()
    total_time = (end_time - start_time) * 1000
    
    summary = f"\nGentisAI Results:\nTotal Time (incl overhead): {total_time:.2f} ms\nSum of Turn Latencies: {total_latency:.2f} ms\nTotal Tokens: {total_tokens}"
    log_to_file(filename, summary)
    print(summary)
    
    return {
        "framework": "GentisAI",
        "latency": total_latency,
        "tokens": total_tokens
    }

# --- CrewAI Setup ---
def run_crewai():
    filename = "comparison/crewai_results.txt"
    if os.path.exists(filename): os.remove(filename)

    log_to_file(filename, "--- Starting CrewAI Benchmark (Conversational Mode) ---")
    print("\n--- Starting CrewAI Benchmark (Conversational Mode) ---")
    start_time = time.time()
    
    # 1. Setup LLM
    os.environ["GEMINI_API_KEY"] = API_KEY
    
    # 2. Define Agents
    support_agent = Agent(
        role='Support Expert',
        goal='Diagnose technical issues, login problems, and bugs.',
        backstory=QUICK_START_SUPPORT,
        llm=f"gemini/{MODEL_NAME}",
        verbose=False,
        allow_delegation=False
    )
    
    sales_agent = Agent(
        role='Sales Expert',
        goal='Handle pricing inquiries, plan upgrades, and product features.',
        backstory=QUICK_START_SALES,
        llm=f"gemini/{MODEL_NAME}",
        verbose=False,
        allow_delegation=False
    )
    
    history = []
    total_tokens = 0
    total_latency = 0
    
    for i, user_input in enumerate(TURNS):
        # Sleep to avoid rate limits
        if i > 0:
            print("Sleeping for 60s to respect rate limits...")
            time.sleep(60)
        
        log_to_file(filename, f"\n--- Turn {i+1} ---")
        log_to_file(filename, f"User: {user_input}")
        print(f"Turn {i+1} User: {user_input}")
        turn_start = time.time()
        
        # Construct task with history
        history_text = "\n".join([f"{role}: {text}" for role, text in history])
        task_description = f"""
        Current Conversation History:
        {history_text}
        
        User's New Input: {user_input}
        
        Respond to the user's input as a helpful Expert.
        If the user asks about technical errors, the Support Expert should answer.
        If the user asks about sales/pricing, the Sales Expert should answer.
        Keep the conversation going or provide the requested help.
        """
        
        task = Task(
            description=task_description,
            agent=None, # Let the manager decide
            expected_output="A helpful response to the user."
        )
        
        # Use hierarchical process to allow manager to select agent
        crew = Crew(
            agents=[support_agent, sales_agent],
            tasks=[task],
            process=Process.hierarchical,
            manager_llm=f"gemini/{MODEL_NAME}",
            verbose=False
        )
        
        try:
            result = crew.kickoff()
            
            turn_end = time.time()
            latency = (turn_end - turn_start) * 1000
            total_latency += latency
            
            # Extract tokens
            turn_tokens = 0
            if hasattr(crew, "usage_metrics"):
                metrics = crew.usage_metrics
                if hasattr(metrics, "total_tokens"):
                    turn_tokens = metrics.total_tokens
                else:
                    # Fallback if metrics is not structured as expected
                    try:
                        turn_tokens = int(str(metrics).split("total_tokens=")[1].split(",")[0])
                    except:
                        turn_tokens = 0 # Could not parse
            
            total_tokens += turn_tokens
            
            response_text = str(result)
            history.append(("User", user_input))
            history.append(("Agent", response_text))
            
            log_to_file(filename, f"Agent: Crew Manager")
            log_to_file(filename, f"Latency: {latency:.2f} ms")
            log_to_file(filename, f"Tokens: {turn_tokens}")
            log_to_file(filename, f"Response:\n{response_text}\n")
            
            print(f"Turn {i+1} Agent: Crew Manager")
            print(f"Turn {i+1} Latency: {latency:.2f} ms")
            print(f"Turn {i+1} Tokens: {turn_tokens}")
            
        except Exception as e:
            error_msg = f"Turn {i+1} Error: {e}"
            log_to_file(filename, error_msg)
            print(error_msg)
    
    end_time = time.time()
    total_time = (end_time - start_time) * 1000
    
    summary = f"\nCrewAI Results:\nTotal Time: {total_time:.2f} ms\nTotal Tokens: {total_tokens}"
    log_to_file(filename, summary)
    print(summary)
    
    return {
        "framework": "CrewAI",
        "latency": total_latency,
        "tokens": total_tokens
    }

if __name__ == "__main__":
    am_results = run_gentis_ai()
    
    print("\nSleeping for 60s before starting CrewAI to reset quotas...")
    time.sleep(60)

    # Note: CrewAI might take significantly longer, so we run it second.
    try:
        crew_results = run_crewai()
    except Exception as e:
        print(f"CrewAI Failed: {e}")
        crew_results = {"framework": "CrewAI", "latency": 0, "tokens": "Error"}

    print("\n\n=== FINAL COMPARISON ===")
    print(f"{'Framework':<15} | {'Latency (ms)':<15} | {'Tokens':<15}")
    print("-" * 50)
    print(f"{am_results['framework']:<15} | {am_results['latency']:<15.2f} | {am_results['tokens']:<15}")
    print(f"{crew_results['framework']:<15} | {crew_results['latency']:<15.2f} | {crew_results['tokens']:<15}")
