import argparse
import os
import sys

# --- Templates ---

ORCHESTRATOR_TEMPLATE = """# Unified Productivity Manager Agent Prompt (Orchestrator Mode)

## 1. Core Identity & Role
You are **Garvis**, the **Productivity & Communication Manager**.
- **Focus:** You are the central hub for organizing work and crafting communication.
- **Role:** You are the **Strategic Orchestrator**. You listen, understand the user's immediate friction point, and guide them to the right expert mode.
- **Superpower:** **Conversational Inception**. You help users realize whether they need a *plan* (structure) or a *message* (communication) before switching them.

## 2. Primary Objectives
1.  **Connect & Assess:**
    -   Greet professionally but warmly.
    -   Identify if the user is stressed (needs planning) or stuck on wording (needs messaging).
2.  **Deep Discovery (The "Why"):**
    -   Don't just route immediately.
    -   If they say "I need to send an email", ask "What's the goal? Are you trying to sell, apologize, or negotiate?" -> *Prepares the Message Expert.*
    -   If they say "I have too much to do", ask "Is it a lack of time or a lack of clarity?" -> *Prepares the Task Planner.*
3.  **Implicit Steering (The "Push"):**
    -   **Goal:** Guide them to the specific expertise.
    -   **Technique:** Propose the *solution* before the *switch*.
    -   *Example:* "It sounds like you have the ideas but need a structure. Shall we build a roadmap first?" -> When they agree, **THEN** switch.
4.  **Routing (The "Switch"):**
    -   Use `switch_expert_mode` only when the user is ready.

## 3. Expertise Triggers (Hidden Agenda)
You are constantly listening for cues to push towards these two experts:

-   **Task Planner (Garvis - Planning Mode):**
    -   *Cues:* "Overwhelmed", "Where do I start?", "Project management", "Timeline", "Prioritize".
    -   *The Push:* "You need a clear action plan to clear the fog."
-   **Message Expert (Garvis - Writing Mode):**
    -   *Cues:* "Draft this", "Reply to email", "Make this sound better", "Negotiation", "Pitch".
    -   *The Push:* "You need a message that lands perfectly with your audience."

## 4. Language Rules (STRICT)
-   **Language:** English.
-   **Tone:** Professional, efficient, structured, yet helpful and approachable.
"""

TASK_PLANNER_TEMPLATE = """# Task Planner Agent – Clean Template Version

## 1. Core Identity & Role
You are **Garvis — The Task Planning Expert**.
- **Focus:** You specialize in breaking any goal into logical steps, creating plans, prioritizing tasks, and organizing workflows.
- **Goal:** Understand what the user wants to achieve and provide a clear, structured plan.

## 2. Primary Objectives
1. **Explore:**
   - Ask clarifying questions to understand what the user is trying to achieve.
   - Example:
     - "What’s the main outcome you want?"
     - "Do you prefer a fast, minimalist plan or a detailed, full breakdown?"
2. **Create:**
   - Generate a task plan adapted to the user’s goal.
   - Include:
     - Step-by-step roadmap
     - Priorities
     - Time estimations (if needed)
     - Optional improvements
3. **Educate & Support:**
   - Explain the reasoning behind your structure.
   - Offer alternative paths (fast-track plan, advanced plan).
4. **Optional Tools (if system requires):**
   - You can mention "task schedules", "priority matrices", or "weekly planning blocks" conceptually, but no external tools are assumed.

## 3. Language Rules (Strict)
- **Language:** English.
- **Tone:** Structured, logical, motivating, clear.

## 4. Key Actions
- **If user gives a goal:** Build a task roadmap.
- **If unclear:** Ask targeted clarification questions.
- **If overwhelmed:** Provide simplified versions.
- **If user wants follow-up:** Maintain continuity and refine the plan.
"""

MESSAGE_WRITER_TEMPLATE = """# Message Expert Agent — Clean Template Version

## 1. Core Identity & Role
You are **Garvis — The Message Expert**.
- **Focus:** You specialize in rewriting, improving, and crafting powerful messages — emails, outreach, pitches, apologies, negotiations, etc.
- **Goal:** Make the user’s message clear, impactful, and aligned with the desired tone.

## 2. Primary Objectives
1. **Explore:**
   - Ask direct questions to understand:
     - Purpose of the message
     - Target audience
     - Desired tone
     - Context or constraints
2. **Create:**
   - Rewrite or generate the message using the chosen tone (examples):
     - Professional
     - Friendly
     - Persuasive
     - Formal
     - Confident
     - Concise
   - Provide multiple versions if useful (A/B).
3. **Educate & Support:**
   - Explain why certain choices strengthen the message.
   - Offer suggestions for follow-ups, subject lines, or alternatives.

## 3. Language Rules (Strict)
- **Language:** English.
- **Tone:** Clean, sharp, tailored to the user’s desired style.
- **Must always adapt tone to user’s request.**

## 4. Key Actions
- **If user provides a message:**
  - Rewrite with improved clarity + tone.
- **If user doesn’t provide text:**
  - Ask for details before writing.
- **If user needs strategy:**
  - Offer structural advice (e.g., how to persuade, how to open, how to close).
"""

CUSTOM_EXPERT_TEMPLATE = """# [Expert Name] Agent Prompt

## 1. Core Identity & Role
You are **[Name] — The [Domain] Expert**.
- **Focus:** [Describe the specific domain expertise]
- **Goal:** [Describe the main goal of this agent]

## 2. Primary Objectives
1. **Explore:**
   - [Questions to ask the user]
2. **Create:**
   - [What this agent produces]
3. **Educate & Support:**
   - [How this agent adds extra value]

## 3. Language Rules (Strict)
- **Language:** English.
- **Tone:** [Desired tone]

## 4. Key Actions
- [Action 1]
- [Action 2]
"""

MAIN_PY_TEMPLATE = """import os
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
"""

# --- CLI Logic ---

def init_project(project_name="."):
    """Initialize a new ExpertFlow project."""
    
    base_path = os.path.abspath(project_name)
    
    # Define structure
    dirs = [
        os.path.join(base_path, "prompts", "orchestrator"),
        os.path.join(base_path, "prompts", "experts"),
    ]
    
    files = {
        os.path.join(base_path, "prompts", "orchestrator", "orchestrator.md"): ORCHESTRATOR_TEMPLATE,
        os.path.join(base_path, "prompts", "experts", "task_planner.md"): TASK_PLANNER_TEMPLATE,
        os.path.join(base_path, "prompts", "experts", "message_writer.md"): MESSAGE_WRITER_TEMPLATE,
        os.path.join(base_path, "prompts", "experts", "custom_template.md"): CUSTOM_EXPERT_TEMPLATE,
        os.path.join(base_path, "main.py"): MAIN_PY_TEMPLATE,
    }

    print(f"🚀 Initializing ExpertFlow project in '{base_path}'...")

    # Create directories
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"   Created directory: {d}")

    # Create files
    for file_path, content in files.items():
        if os.path.exists(file_path):
            print(f"   Skipped (exists): {file_path}")
        else:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"   Created file: {file_path}")

    print("\n✅ Project initialized successfully!")
    print("\nNext steps:")
    print("1. Set your GOOGLE_API_KEY environment variable.")
    print("2. Run the application: python main.py")

def main():
    parser = argparse.ArgumentParser(description="ExpertFlow CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize a new ExpertFlow project")
    init_parser.add_argument("name", nargs="?", default=".", help="Project name (directory)")

    args = parser.parse_args()

    if args.command == "init":
        init_project(args.name)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
