from __future__ import annotations

from collections.abc import Mapping
from functools import partial

from gentis_ai import Expert, Flow, Router, ToolCall
from gentis_ai.config import load_environment
from gentis_ai.tools import ToolExecutor, ToolRegistry
from gentis_ai.demos.customer_rescue.mock import RescueMockLLM

from gentis_ai.providers import ProviderFactory, ProviderSettings, build_cloud_llm
from gentis_ai.demos.customer_rescue.tools import (
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
    "account_security": "Looks up the customer's name and handles account protection.",
    "customer_retention": "Handles cancellations and customer recovery.",
    "customer_rescue_lead": "Synthesizes multi-expert customer rescue plans.",
}


# Edit this mapping, then restart the demo to change each agent's capabilities.
AGENT_TOOLS = {
    "technical_support": ("create_support_ticket",),
    "billing": ("check_invoice",),
    "sales": (),
    "account_security": ("lookup_account",),
    "customer_retention": (),
    "customer_rescue_lead": (),
}


def rescue_tool_policy(message, decision, *, agent_tools=None):
    attachments = AGENT_TOOLS if agent_tools is None else agent_tools
    names = dict.fromkeys(
        name for agent in decision.experts for name in attachments.get(agent, ())
    )
    arguments = {
        "check_invoice": {"invoice_ref": "INV-2048"},
        "lookup_account": {"account_ref": "ACCT-1042"},
        "create_support_ticket": {"account_ref": "ACCT-1042", "issue": message},
    }
    return [ToolCall(name=name, arguments=arguments[name]) for name in names]


def _build_llm(
    provider: str,
    environment: Mapping[str, str] | None = None,
    **provider_factories: ProviderFactory,
):
    if provider == "mock":
        return RescueMockLLM(
            routing_rules={
                "charged twice": ["billing", "technical_support", "customer_retention"],
                "which invoice": "billing",
                "invoice": "billing",
                "crash": "technical_support",
                "upgrade": "sales",
                "suspicious": "account_security",
                "cancel": "customer_retention",
            },
        ), "MockLLM"
    return build_cloud_llm(
        provider,
        environment,
        **provider_factories,
    )


def build_flow(provider: str | None = None) -> tuple[Flow, str]:
    environment = load_environment()
    settings = ProviderSettings.from_environment(environment, provider)
    llm, label = _build_llm(settings.provider, environment)
    attachments = {name: tuple(names) for name, names in AGENT_TOOLS.items()}
    experts = {
        name: Expert(
            name=name,
            description=desc,
            system_prompt=(
                f"You are {name}. {desc}\n"
                f"Assigned application tools: {', '.join(attachments.get(name, ())) or 'none'}.\n"
                + (
                    "You can create demo tickets using create_support_ticket.\n"
                    if "create_support_ticket" in attachments.get(name, ()) else
                    "You cannot create tickets: create_support_ticket is not assigned to you.\n"
                )
                + "Only report a ticket as created when a successful verified tool result "
                "contains its ticket_id. Never invent a ticket, account data, or an action. "
                "Other agents' permissions do not grant you access. If asked to create "
                "a ticket without access, explain the missing tool assignment. "
                "Tool results describe simulated demo actions, not an external help desk."
            ),
        )
        for name, desc in EXPERT_DESCRIPTIONS.items()
    }
    if isinstance(llm, RescueMockLLM):
        llm.tools_by_prompt = {
            expert.system_prompt: attachments.get(name, ())
            for name, expert in experts.items()
        }
    registry = ToolRegistry()
    for tool in (lookup_account, check_invoice, create_support_ticket):
        registry.register(tool)
    for name, names in attachments.items():
        if name not in experts:
            raise ValueError(f"Unknown agent in AGENT_TOOLS: {name}")
        for tool_name in names:
            registry.get(tool_name)
    router = Router(
        list(experts.values()), llm=llm, routing_max_tokens=settings.routing_max_tokens, default_expert=experts["customer_rescue_lead"]
    )
    return Flow(
        router,
        llm,
        parallel_execution=True,
        tool_executor=ToolExecutor(registry, max_tool_calls=3, timeout_seconds=2.0),
        tool_policy=partial(rescue_tool_policy, agent_tools=attachments),
    ), label
