import os
import sys
import time

# Ensure the library is in the path for this tutorial
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from switchboard_ai import Agent, Router, ConversationManager

def print_step(title, description):
    print(f"\n{'-'*50}")
    print(f"📘 STEP: {title}")
    print(f"{description}")
    print(f"{'-'*50}\n")
    time.sleep(1)

def main():
    print("🎓 Welcome to the SwitchboardAI Tutorial App!")
    print("This app will guide you through building a multi-agent system.\n")

    # 0. Setup API Key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️  GOOGLE_API_KEY environment variable not found.")
        api_key = input("🔑 Please enter your Google Gemini API Key to continue: ").strip()
        if not api_key:
            print("❌ API Key is required to run the demo. Exiting.")
            return

    # 1. Define Agents
    print_step("Defining Agents", 
               "We start by creating 'Agent' objects. Each agent has a name, \n"
               "a description (used by the Router to decide when to switch), \n"
               "and a system prompt (instructions for the LLM).")

    # Agent 1: The Python Tutor
    python_tutor = Agent(
        name="python_tutor",
        description="Expert in Python programming, debugging, and code explanation.",
        system_prompt="You are a friendly Python Tutor. You help users write clean, pythonic code. "
                      "Always explain your code snippets."
    )
    print(f"✅ Created Agent: {python_tutor.name}")

    # Agent 2: The Math Wizard
    math_wizard = Agent(
        name="math_wizard",
        description="Expert in mathematics, calculus, algebra, and solving complex problems.",
        system_prompt="You are a Math Wizard. Solve problems step-by-step. Use LaTeX formatting for equations where possible."
    )
    print(f"✅ Created Agent: {math_wizard.name}")

    # Note: We don't strictly need to define an 'orchestrator' manually because 
    # the Router will create a default one if we don't provide a default_agent.
    # But let's define one to be explicit.
    orchestrator = Agent(
        name="orchestrator",
        description="Handles general greetings, small talk, and routing.",
        system_prompt="You are a helpful assistant. If the user asks about Python or Math, guide them to ask specific questions."
    )
    print(f"✅ Created Agent: {orchestrator.name}")

    # 2. Initialize Router
    print_step("Initializing the Router",
               "The Router takes our list of agents and decides which one should handle a user message.\n"
               "It uses a fast LLM model to classify intent based on the agent descriptions.")

    router = Router(
        agents=[python_tutor, math_wizard, orchestrator],
        default_agent=orchestrator,
        api_key=api_key
    )
    print("✅ Router initialized.")

    # 3. Initialize Conversation Manager
    print_step("Initializing Conversation Manager",
               "The Manager handles the chat loop, maintains history, and executes the agent switches.\n"
               "We are enabling 'debug=True' to see the internal memory logs in the 'debug-cache/' folder.")

    manager = ConversationManager(router=router, api_key=api_key, debug=True)
    print("✅ ConversationManager initialized with debug=True.")

    # 4. Interactive Loop
    print_step("Interactive Demo",
               "Now, try chatting! The system will switch agents based on your intent.\n"
               "Try asking: 'How do I define a function in Python?' or 'What is the derivative of x^2?'\n"
               "Type 'exit' to quit.")

    user_id = "tutorial_user"

    while True:
        try:
            user_input = input(f"\n👤 You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("👋 Goodbye!")
                break

            print("... thinking ...")
            
            # Process the turn
            response = manager.process_turn(user_id, user_input)

            # Check if a switch happened
            if response.switched_context:
                print(f"\n🔄 [System] Context Switched! Now talking to: {response.agent_name.upper()}")
            else:
                print(f"\n🔹 [System] Agent: {response.agent_name}")

            print(f"🤖 AI: {response.content}")
            
            if response.token_usage:
                print(f"   (Tokens used: {response.token_usage.get('total', 0)})")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
