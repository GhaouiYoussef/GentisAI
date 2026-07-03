from __future__ import annotations

from typing import Protocol

from .decisions import RoutingDecision


class RoutingStrategy(Protocol):
    def route(
        self,
        user_message: str,
        current_expert_name: str,
        available_experts: set[str],
        enable_hybrid: bool,
    ) -> RoutingDecision | None:
        ...


class KeywordRoutingStrategy:
    """Deterministic zero-LLM router based on keyword matches."""

    def __init__(
        self,
        rules: dict[str, str | list[str]],
        confidence: float = 1.0,
    ):
        self.rules = {keyword.lower(): target for keyword, target in rules.items()}
        self.confidence = confidence

    def route(
        self,
        user_message: str,
        current_expert_name: str,
        available_experts: set[str],
        enable_hybrid: bool,
    ) -> RoutingDecision | None:
        text = user_message.lower()
        selected: list[str] = []

        for keyword, target in self.rules.items():
            if keyword not in text:
                continue

            targets = target if isinstance(target, list) else [target]
            for name in targets:
                if name in available_experts and name not in selected:
                    selected.append(name)

            if selected and not enable_hybrid:
                break

        if not selected:
            return None

        if not enable_hybrid:
            selected = selected[:1]

        return RoutingDecision(
            experts=selected,
            mode="hybrid" if len(selected) > 1 else "single",
            confidence=self.confidence,
            reason="Matched deterministic routing rule.",
        )
