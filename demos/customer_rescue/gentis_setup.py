from __future__ import annotations

import os

from gentis_ai import Expert, Flow, Router, ToolCall
from gentis_ai.llm import MockLLM, OpenAICompatibleLLM
from gentis_ai.tools import ToolExecutor, ToolRegistry

from demos.customer_rescue.tools import (
    check_invoice,
    create_support_ticket,
    lookup_account,
)


SHOWCASE_PROMPT = (
    "I was charged twice, the application keeps crashing, "
    "and I'm thinking of cancelling."
)
SCENARIOS = {
    "Single expert": "Please check invoice INV-2048.",
    "Customer rescue": SHOWCASE_PROMPT,
    "Session follow-up": "Which invoice did you check, and what happens next?",
}
EXPERT_LABELS = {
    "technical_support": "Technical Support",
    "billing": "Billing",
    "sales": "Sales",
    "account_security": "Account Security",
    "customer_retention": "Customer Retention",
    "customer_rescue_lead": "Rescue Lead",
}
EXPERT_DESCRIPTIONS = {
    "technical_support": "Diagnoses crashes, errors, and incidents.",
    "billing": "Handles invoices, duplicate charges, and refunds.",
    "sales": "Handles plans, upgrades, and purchase questions.",
    "account_security": "Handles suspicious access and account protection.",
    "customer_retention": "Handles cancellations and customer recovery.",
    "customer_rescue_lead": "Synthesizes multi-expert customer rescue plans.",
}


def rescue_tool_policy(message, decision):
    selected = set(decision.experts)
    calls = []
    if "billing" in selected:
        calls.append(
            ToolCall(name="check_invoice", arguments={"invoice_ref": "INV-2048"})
        )
    if "technical_support" in selected:
        calls.append(
            ToolCall(
                name="create_support_ticket",
                arguments={"account_ref": "ACCT-1042", "issue": "Application crash"},
            )
        )
    if "account_security" in selected:
        calls.append(
            ToolCall(name="lookup_account", arguments={"account_ref": "ACCT-1042"})
        )
    return calls


def _build_llm(provider: str):
    if provider == "mock":
        return MockLLM(
            routing_rules={
                "charged twice": ["billing", "technical_support", "customer_retention"],
                "which invoice": "billing",
                "invoice": "billing",
                "crash": "technical_support",
                "upgrade": "sales",
                "suspicious": "account_security",
                "cancel": "customer_retention",
            },
            responses={
                "charged twice": "We confirmed the duplicate-charge review, opened a crash ticket, and prepared a retention follow-up.",
                "which invoice": "We checked INV-2048. Billing will review the duplicate charge while support follows the crash ticket.",
                "invoice": "Invoice INV-2048 is marked for duplicate-charge review.",
                "crash": "A fictional support ticket is ready for investigation.",
            },
            default_response="The rescue lead can coordinate the next best action.",
        ), "MockLLM"
    if provider != "openai":
        raise RuntimeError("GENTIS_PROVIDER must be 'mock' or 'openai'.")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required when GENTIS_PROVIDER=openai")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return OpenAICompatibleLLM(
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL") or None,
        model_name=model,
        timeout=45.0,
        max_tokens=900,
    ), model


def build_flow(provider: str | None = None) -> tuple[Flow, str]:
    llm, label = _build_llm((provider or os.getenv("GENTIS_PROVIDER", "mock")).lower())
    experts = {
        name: Expert(name=name, description=desc)
        for name, desc in EXPERT_DESCRIPTIONS.items()
    }
    registry = ToolRegistry()
    for tool in (lookup_account, check_invoice, create_support_ticket):
        registry.register(tool)
    router = Router(
        list(experts.values()), llm=llm, default_expert=experts["customer_rescue_lead"]
    )
    return Flow(
        router,
        llm,
        parallel_execution=True,
        tool_executor=ToolExecutor(registry, max_tool_calls=3, timeout_seconds=2.0),
        tool_policy=rescue_tool_policy,
    ), label
