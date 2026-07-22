from __future__ import annotations

import os

from gentis_ai import Expert, Flow, Router
from gentis_ai.llm import MockLLM, OpenAICompatibleLLM


DEFAULT_BRIEF = "A lightweight Python framework that routes real-time requests to specialized AI experts without hidden manager loops."
EXPERT_LABELS = {
    "product_strategist": "Product Strategist", "growth_marketer": "Growth Marketer",
    "technical_architect": "Technical Architect", "risk_analyst": "Risk Analyst",
    "financial_analyst": "Financial Analyst", "copywriter": "Copywriter",
}
EXPERT_DESCRIPTIONS = {
    "product_strategist": "Owns positioning, user value, prioritization, and synthesis.",
    "growth_marketer": "Plans launch channels, acquisition, and growth mechanics.",
    "technical_architect": "Evaluates feasibility, scope, systems, and delivery trade-offs.",
    "risk_analyst": "Identifies product, market, operational, and adoption risks.",
    "financial_analyst": "Evaluates pricing, cost, runway, and unit economics.",
    "copywriter": "Writes concise headlines, hooks, and launch copy.",
}
SCENARIOS = {
    "Risk review": "Find the biggest risks in this product.",
    "Launch hooks": "Write three launch hooks.",
    "Weekend MVP": "Can this MVP be built in one weekend?",
    "Full recommendation": "Create a complete launch recommendation.",
    "Session follow-up": "Make the second hook more technical.",
}
MOCK_ROUTES = {
    "biggest risks": ["risk_analyst", "product_strategist"],
    "launch hooks": ["growth_marketer", "copywriter"],
    "one weekend": ["technical_architect", "product_strategist"],
    "complete launch recommendation": list(EXPERT_LABELS),
    "second hook": ["growth_marketer", "copywriter"],
}
MOCK_RESPONSES = {
    "biggest risks": "The primary risks are unclear urgency, crowded positioning, and onboarding friction.",
    "launch hooks": "1. Route every question to the right expert. 2. Stop paying for agents you did not need. 3. Make multi-expert AI feel instant.",
    "one weekend": "Yes, if the MVP limits scope to explicit routing, two integrations, and one measurable workflow.",
    "complete launch recommendation": "Lead with routing visualization, target developer teams, and validate retention before expanding.",
    "second hook": "Technical rewrite: Execute only the expert path your request actually requires.",
}


def _build_llm(provider: str):
    if provider == "mock":
        return MockLLM(MOCK_RESPONSES, MOCK_ROUTES, "The product strategist can frame the next decision."), "MockLLM"
    if provider != "openai":
        raise RuntimeError("GENTIS_PROVIDER must be 'mock' or 'openai'.")
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is required when GENTIS_PROVIDER=openai")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return OpenAICompatibleLLM(api_key=key, base_url=os.getenv("OPENAI_BASE_URL") or None, model_name=model, timeout=45.0, max_tokens=900), model


def build_flow(provider: str | None = None) -> tuple[Flow, str]:
    llm, label = _build_llm((provider or os.getenv("GENTIS_PROVIDER", "mock")).lower())
    experts = {name: Expert(name=name, description=desc) for name, desc in EXPERT_DESCRIPTIONS.items()}
    router = Router(list(experts.values()), llm=llm, default_expert=experts["product_strategist"])
    return Flow(router, llm, parallel_execution=True), label
