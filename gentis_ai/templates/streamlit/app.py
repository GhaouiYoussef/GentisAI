"""Run with gentis run or python app.py."""

from uuid import uuid4

from project import build_flow


def main():
    flow = build_flow()
    session_id = uuid4().hex
    print("GentisAI chat. Type exit to quit or /agent NAME to select an agent.")
    print("Agents: " + ", ".join(flow.router.experts))
    if flow.router.llm is None:
        print(
            "Offline mode: responses are simulated; /agent selects an agent explicitly."
        )
    while True:
        try:
            message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if message.lower() in {"exit", "quit"}:
            return
        if not message:
            continue
        if message.startswith("/agent "):
            selected = message.removeprefix("/agent ").strip()
            if selected not in flow.router.experts:
                print("Unknown agent. Choose: " + ", ".join(flow.router.experts))
                continue
            session_id = uuid4().hex
            flow.session_store.save(flow.session_store.get(session_id, selected))
            print(f"Started a new conversation with {selected}.")
            continue
        response = flow.process_turn(message, session_id=session_id)
        print(f"{response.agent_name}: {response.content}")


if __name__ == "__main__":
    main()
