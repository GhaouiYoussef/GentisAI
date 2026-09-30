"""Customize these experts, then run gentis run from this directory."""

from gentis_ai import Expert, Flow, Router
from gentis_ai.config import load_environment
from gentis_ai.providers import ProviderSettings, build_llm


def build_flow(environment=None):
    environment = load_environment() if environment is None else environment
    settings = ProviderSettings.from_environment(environment)
    llm = build_llm(environment)
    experts = [
        Expert(
            name="support",
            description="Helps with account and product issues.",
            system_prompt="You are a support specialist. Give clear, practical next steps.",
        ),
        Expert(
            name="sales",
            description="Explains plans, pricing, and purchases.",
            system_prompt="You are a sales specialist. Ask about needs; do not invent prices.",
        ),
    ]
    router = Router(
        experts,
        llm=llm,
        default_expert=experts[0],
        routing_max_tokens=settings.routing_max_tokens,
    )
    return Flow(router, llm=llm)


def main():
    environment = load_environment()
    settings = ProviderSettings.from_environment(environment)
    flow = build_flow(environment)
    print(f"GentisAI support agent ({settings.provider}). Type exit to quit.")
    while True:
        try:
            message = input("You: ")
        except (EOFError, KeyboardInterrupt):
            return
        if message.lower() in {"exit", "quit"}:
            return
        response = flow.process_turn(message, session_id="local-demo")
        print(f"{response.agent_name}: {response.content}")


if __name__ == "__main__":
    main()
