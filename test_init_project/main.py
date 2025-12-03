import os
from expertflow import Agent, Router, ConversationManager, GeminiLLM

# 1. Load Prompts
def load_prompt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# Ensure you have your API key set
# os.environ["GOOGLE_API_KEY"] = "your_api_key_here"

def main():
    # Paths to prompts
    base_dir = os.path.dirname(os.path.abspath(__file__))
    orch_path = os.path.join(base_dir, "prompts", "orchestrator", "orchestrator.md")
    task_path = os.path.join(base_dir, "prompts", "experts", "task_planner.md")
    msg_path = os.path.join(base_dir, "prompts", "experts", "message_writer.md")

    # 2. Initialize Agents
    # Orchestrator
    orchestrator = Agent(
        name="Garvis",
        system_prompt=load_prompt(orch_path),
        description="Strategic Orchestrator and Productivity Manager."
    )

    # Experts
    task_planner = Agent(
        name="Task Planner",
        system_prompt=load_prompt(task_path),
        description="Expert in planning, prioritizing, and organizing tasks."
    )

    message_writer = Agent(
        name="Message Expert",
        system_prompt=load_prompt(msg_path),
        description="Expert in writing, editing, and refining messages."
    )

    # 3. Setup Router
    # The router manages the agents and the default entry point
    router = Router(
        agents=[task_planner, message_writer],
        default_agent=orchestrator,
        llm=GeminiLLM() # Or MockLLM() for testing
    )

    # 4. Start Conversation
    manager = ConversationManager(router=router)
    
    print("🤖 Garvis is ready! (Type 'quit' to exit)")
    print("-" * 50)
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit"]:
            break
            
        response = manager.process_turn(user_input)
        print(f"Garvis ({response.active_agent}): {response.content}")
        print("-" * 50)

if __name__ == "__main__":
    main()
