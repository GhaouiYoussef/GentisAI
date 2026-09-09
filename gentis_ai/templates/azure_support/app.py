from __future__ import annotations

from pathlib import Path
import sys
import time
from collections.abc import Callable, Mapping
from typing import Any, TextIO

from gentis_ai import Expert, Flow, Router
from gentis_ai.config import AzureSettings, load_environment
from gentis_ai.llm import AzureOpenAILLM, BaseLLM, MockLLM


SESSION_ID = "azure-support-poc"


def build_llm(
    environment: Mapping[str, str] | None = None,
    *,
    azure_client: Any = None,
    output: Callable[[str], None] = print,
) -> tuple[BaseLLM, str]:
    env = load_environment(Path(__file__).with_name(".env")) if environment is None else environment
    settings = AzureSettings.from_environment(env)
    missing = settings.missing()

    if missing:
        output(
            "[GentisAI] Azure OpenAI is not fully configured; "
            "using the local mock provider."
        )
        output(f"[GentisAI] Missing: {', '.join(missing)}.")
        return _build_mock_llm(), "local mock"

    kwargs = settings.llm_options()
    if azure_client is not None:
        kwargs["client"] = azure_client

    llm = AzureOpenAILLM(**kwargs)
    output("[GentisAI] Provider: Azure OpenAI.")
    return llm, "Azure OpenAI"


def _build_mock_llm() -> MockLLM:
    return MockLLM(
        routing_rules={
            "charged": "billing_support",
            "invoice": "billing_support",
            "refund": "billing_support",
            "crash": "technical_support",
            "error": "technical_support",
            "upload": "technical_support",
            "sign in": "account_support",
            "login": "account_support",
            "account": "account_support",
        },
        responses={
            "charged": (
                "I found the billing issue. I will help verify the duplicate "
                "charge and explain the refund path."
            ),
            "invoice": "I can help review the invoice and payment details.",
            "refund": "I will explain the refund status and next step.",
            "crash": (
                "Let us isolate the crash, capture the failing step, and try "
                "a safe workaround."
            ),
            "upload": "I will help troubleshoot the upload failure.",
            "sign in": (
                "I will help restore access while keeping the account secure."
            ),
            "login": "I will help restore access to the account.",
            "account": "I can help with the account and access settings.",
        },
        default_response=(
            "I remember the current support context and will guide the next step."
        ),
    )


def build_flow(llm: BaseLLM) -> Flow:
    technical = Expert(
        name="technical_support",
        description="Application errors, bugs, outages, uploads, and troubleshooting.",
        system_prompt=(
            "You are a concise technical support agent. Diagnose safely, ask for "
            "the minimum useful detail, and give ordered troubleshooting steps."
        ),
    )
    billing = Expert(
        name="billing_support",
        description="Invoices, charges, refunds, subscriptions, and payments.",
        system_prompt=(
            "You are a concise billing support agent. Explain billing actions "
            "clearly and never invent account transactions."
        ),
    )
    account = Expert(
        name="account_support",
        description="Login, profile, access, and general account questions.",
        system_prompt=(
            "You are a concise account support agent. Protect account security "
            "and provide clear access-recovery steps."
        ),
    )
    router = Router(
        experts=[technical, billing, account],
        llm=llm,
        default_expert=account,
        enable_hybrid=False,
        routing_max_tokens=96,
    )
    return Flow(router=router, llm=llm)


def stream_support_turn(
    flow: Flow,
    message: str,
    *,
    stream: TextIO | None = None,
    clock: Callable[[], float] = time.perf_counter,
) -> str:
    destination = stream or sys.stdout
    route_started_at = 0.0
    final_content = ""

    for event in flow.stream_turn(message, session_id=SESSION_ID):
        if event.type == "route_started":
            route_started_at = clock()
        elif event.type == "route_finished":
            elapsed_ms = round((clock() - route_started_at) * 1000)
            decision = event.data["decision"]
            selected = decision["experts"][0]
            destination.write(f"[route] {selected} selected in {elapsed_ms} ms\n")
        elif event.type == "expert_started":
            destination.write(f"[agent] {event.agent_name}\n")
            destination.write("Agent: ")
        elif event.type == "token":
            destination.write(event.content)
            destination.flush()
        elif event.type == "error":
            destination.write("\n[error] The provider could not complete this turn.")
        elif event.type == "final":
            final_content = event.content

    destination.write("\n")
    return final_content


def main() -> int:
    try:
        llm, provider = build_llm()
    except (ImportError, ValueError):
        print(
            "[GentisAI] Azure provider setup failed. Verify the Azure extra "
            "and environment variables.",
            file=sys.stderr,
        )
        return 1

    flow = build_flow(llm)
    print(f"[GentisAI] Customer Support POC ready ({provider}).")
    print("[GentisAI] Agents: technical_support, billing_support, account_support")
    print("Try: I was charged twice this month.")
    print("Type 'exit' to quit.")

    while True:
        try:
            message = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return 0

        if message.lower() in {"exit", "quit"}:
            print("Goodbye.")
            return 0
        if not message:
            print("Please enter a support question.")
            continue
        stream_support_turn(flow, message)


if __name__ == "__main__":
    raise SystemExit(main())
