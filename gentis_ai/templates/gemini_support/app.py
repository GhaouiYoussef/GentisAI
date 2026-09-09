from __future__ import annotations

from pathlib import Path
from collections.abc import Callable, Mapping
from typing import Any

from gentis_ai import Expert, Flow, Router
from gentis_ai.config import load_environment
from gentis_ai.llm import GeminiLLM


DEFAULT_MODEL = "gemini-2.5-flash"


def build_llm(
    environment: Mapping[str, str] | None = None,
    *,
    gemini_factory: Callable[..., Any] = GeminiLLM,
    output: Callable[[str], None] = print,
) -> tuple[Any, str]:
    environment = load_environment(Path(__file__).with_name(".env")) if environment is None else environment
    api_key = environment.get("GOOGLE_API_KEY") or environment.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Set GOOGLE_API_KEY (or GEMINI_API_KEY) before running this demo."
        )

    model = environment.get("GEMINI_MODEL", DEFAULT_MODEL)
    llm = gemini_factory(api_key=api_key, model_name=model)
    provider = f"Gemini ({model})"
    output(f"[GentisAI] Provider: {provider}.")
    return llm, provider


def build_flow(llm: Any) -> Flow:
    technical_support = Expert(
        name="technical_support",
        description="Handles login problems, errors, and troubleshooting.",
        system_prompt=(
            "You are a concise customer support engineer. Give safe, practical "
            "troubleshooting steps and ask for missing details when needed."
        ),
    )
    billing_support = Expert(
        name="billing_support",
        description="Handles invoices, charges, refunds, and subscriptions.",
        system_prompt=(
            "You are a concise billing support specialist. Explain next steps "
            "without inventing account details or claiming actions were completed."
        ),
    )
    account_support = Expert(
        name="account_support",
        description="Handles account access and general customer questions.",
        system_prompt=(
            "You are a concise account support specialist. Protect credentials and "
            "never ask the customer to share passwords or API keys."
        ),
    )
    experts = [technical_support, billing_support, account_support]
    router = Router(
        experts=experts,
        llm=llm,
        default_expert=account_support,
        routing_max_tokens=128,
    )
    return Flow(router=router, llm=llm)


def main(
    input_fn: Callable[[str], str] | None = None,
    output: Callable[[str], None] = print,
) -> None:
    input_fn = input if input_fn is None else input_fn
    try:
        llm, _ = build_llm(output=output)
    except (ImportError, RuntimeError, ValueError) as exc:
        output(f"[GentisAI] Setup error: {exc}")
        raise SystemExit(1) from exc

    flow = build_flow(llm)
    output("GentisAI Gemini chat. Type 'exit' to quit.")
    while True:
        message = input_fn("You: ").strip()
        if message.lower() in {"exit", "quit"}:
            return
        if not message:
            continue

        try:
            response = flow.process_turn(message, session_id="gemini-demo")
        except Exception:
            output("[GentisAI] Gemini request failed. Check the model, key, and network.")
            continue
        output(f"{response.agent_name}: {response.content}")


if __name__ == "__main__":
    main()
