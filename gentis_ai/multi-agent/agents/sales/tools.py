from __future__ import annotations


def get_price(plan_name: str) -> str:
    """Example sales tool for quoting a plan."""

    return f"Price requested for {plan_name}."


def compare_plans(left: str, right: str) -> str:
    """Example sales tool for comparing plans."""

    return f"Compared {left} against {right}."
