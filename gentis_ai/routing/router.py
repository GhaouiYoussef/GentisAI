from __future__ import annotations

import json
import logging
import re

from gentis_ai.core.types import Expert, Message
from gentis_ai.llm.base import BaseLLM

from .decisions import RoutingDecision
from .strategies import KeywordRoutingStrategy, RoutingStrategy

logger = logging.getLogger(__name__)


class Router:
    def __init__(
        self,
        experts: list[Expert],
        llm: BaseLLM | None = None,
        default_expert: Expert | None = None,
        enable_hybrid: bool = True,
        rules: dict[str, str | list[str]] | None = None,
        routing_strategy: RoutingStrategy | None = None,
        confidence_threshold: float = 0.35,
        fallback_strategy: str = "current",
    ):
        self.experts = {expert.name: expert for expert in experts}
        self.llm = llm
        self.enable_hybrid = enable_hybrid
        self.confidence_threshold = confidence_threshold
        self.fallback_strategy = fallback_strategy

        if default_expert is None:
            self.default_expert = self.experts.get(
                "orchestrator",
                Expert(
                    name="orchestrator",
                    description="Handles general queries, greetings, and routing fallback.",
                ),
            )
        else:
            self.default_expert = default_expert

        self.experts.setdefault(self.default_expert.name, self.default_expert)
        self.routing_strategy = routing_strategy or (
            KeywordRoutingStrategy(rules) if rules else None
        )

    def classify(
        self,
        user_message: str,
        current_expert_name: str,
        recent_history: list[str] | None = None,
    ) -> RoutingDecision:
        """Return a validated routing decision for the next turn."""

        current_expert_name = self._known_or_default(current_expert_name)

        if self.routing_strategy:
            rule_decision = self.routing_strategy.route(
                user_message=user_message,
                current_expert_name=current_expert_name,
                available_experts=set(self.experts),
                enable_hybrid=self.enable_hybrid,
            )
            if rule_decision is not None:
                return self._validate_decision(rule_decision, current_expert_name)

        if self.llm is None:
            return self._fallback(
                current_expert_name,
                "No LLM or deterministic routing strategy configured.",
            )

        try:
            raw_output = self.llm.generate(
                messages=[
                    Message(
                        role="user",
                        content=self._build_prompt(
                            user_message,
                            current_expert_name,
                            recent_history or [],
                        ),
                    )
                ],
                max_tokens=512,
            )
            if hasattr(raw_output, "__iter__") and not isinstance(raw_output, str):
                raw_output = "".join(raw_output)
            decision = self._parse_response(str(raw_output))
            return self._validate_decision(decision, current_expert_name)
        except Exception:
            logger.exception("Router failed to classify message")
            return self._fallback(current_expert_name, "Router classification failed.")

    def classify_names(
        self,
        user_message: str,
        current_expert_name: str,
        recent_history: list[str] | None = None,
    ) -> list[str]:
        return self.classify(user_message, current_expert_name, recent_history).experts

    def get_expert(self, name: str) -> Expert:
        return self.experts.get(name, self.default_expert)

    def _build_prompt(
        self,
        user_message: str,
        current_expert_name: str,
        recent_history: list[str],
    ) -> str:
        experts_desc = "\n".join(
            f"- {name}: {expert.description}" for name, expert in self.experts.items()
        )
        history_text = "\n".join(recent_history[-5:])
        mode_instruction = (
            "Select one or more experts when the request spans domains."
            if self.enable_hybrid
            else "Select exactly one expert."
        )

        return f"""You are an Intent Router.

Current Expert: {current_expert_name}
Recent Context:
{history_text}

User Message: "{user_message}"

Available Experts:
{experts_desc}

{mode_instruction}

Return JSON only with this shape:
{{"experts":["expert_name"],"mode":"single|hybrid|fallback","confidence":0.0,"reason":"short reason"}}

Rules:
1. Keep the current expert when the request still fits their domain.
2. Use only names from Available Experts.
3. If unsure, use "{self.default_expert.name}" with mode "fallback".
"""

    def _parse_response(self, text: str) -> RoutingDecision:
        json_text = self._extract_json(text)
        if json_text:
            data = json.loads(json_text)
            if isinstance(data, dict):
                experts = data.get("experts", [])
                if isinstance(experts, str):
                    experts = [experts]
                return RoutingDecision(
                    experts=[str(name).strip() for name in experts],
                    mode=data.get("mode") or ("hybrid" if len(experts) > 1 else "single"),
                    confidence=float(data.get("confidence", 1.0)),
                    reason=str(data.get("reason", "")),
                )
            if isinstance(data, list):
                return RoutingDecision(
                    experts=[str(name).strip() for name in data],
                    mode="hybrid" if len(data) > 1 else "single",
                    confidence=0.8,
                    reason="Parsed list response.",
                )

        names = [part.strip() for part in text.strip().split(",") if part.strip()]
        if not names:
            raise ValueError("Router response did not contain expert names.")

        return RoutingDecision(
            experts=names,
            mode="hybrid" if len(names) > 1 else "single",
            confidence=0.7,
            reason="Parsed legacy comma-separated response.",
        )

    def _extract_json(self, text: str) -> str | None:
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
            stripped = re.sub(r"```$", "", stripped).strip()
        if stripped.startswith("{") or stripped.startswith("["):
            return stripped

        match = re.search(r"(\{.*\}|\[.*\])", stripped, re.DOTALL)
        return match.group(1) if match else None

    def _validate_decision(
        self,
        decision: RoutingDecision,
        current_expert_name: str,
    ) -> RoutingDecision:
        matched = []
        names_by_lower = {name.lower(): name for name in self.experts}
        for raw_name in decision.experts:
            name = names_by_lower.get(raw_name.lower())
            if name and name not in matched:
                matched.append(name)

        if not matched:
            return self._fallback(
                current_expert_name,
                f"No known experts in router output: {decision.experts}",
            )

        if not self.enable_hybrid and len(matched) > 1:
            matched = matched[:1]

        mode = "hybrid" if len(matched) > 1 else "single"
        normalized = RoutingDecision(
            experts=matched,
            mode=mode if decision.mode != "fallback" else "fallback",
            confidence=decision.confidence,
            reason=decision.reason,
        )

        if normalized.confidence < self.confidence_threshold:
            return self._fallback(
                current_expert_name,
                f"Router confidence {normalized.confidence:.2f} below threshold.",
            )

        return normalized

    def _fallback(self, current_expert_name: str, reason: str) -> RoutingDecision:
        if self.fallback_strategy == "default":
            target = self.default_expert.name
        elif self.fallback_strategy == "ask_clarification":
            target = self.default_expert.name
            reason = f"{reason} Ask the user a clarifying question."
        else:
            target = self._known_or_default(current_expert_name)

        return RoutingDecision(
            experts=[target],
            mode="fallback",
            confidence=0.0,
            reason=reason,
        )

    def _known_or_default(self, name: str | None) -> str:
        if name in self.experts:
            return str(name)
        return self.default_expert.name
