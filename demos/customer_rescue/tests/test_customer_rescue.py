from demos.customer_rescue.gentis_setup import SHOWCASE_PROMPT, build_flow
from demos.customer_rescue.tools import (
    check_invoice,
    create_support_ticket,
    lookup_account,
)


def test_fictional_tools_are_deterministic():
    assert lookup_account("ACCT-1042")["plan"] == "Pro"
    assert check_invoice("INV-2048")["duplicate_charge"] is True
    first = create_support_ticket("ACCT-1042", "Application crash")
    second = create_support_ticket("ACCT-1042", "Application crash")
    assert first["ticket_id"] == second["ticket_id"]


def test_single_route_selects_billing():
    flow, provider = build_flow("mock")
    response = flow.process_turn("Please check invoice INV-2048", session_id="billing")
    assert provider == "MockLLM"
    assert response.structured["routing"]["experts"] == ["billing"]
    assert response.structured["tools"][0]["name"] == "check_invoice"


def test_showcase_routes_three_experts_and_two_tools():
    flow, _ = build_flow("mock")
    events = list(flow.stream_turn(SHOWCASE_PROMPT, session_id="showcase"))
    decision = next(
        event for event in events if event.type == "route_finished"
    ).data["decision"]
    tools = [event.data["name"] for event in events if event.type == "tool_call"]
    assert decision["experts"] == [
        "billing",
        "technical_support",
        "customer_retention",
    ]
    assert tools == ["check_invoice", "create_support_ticket"]
    assert any(event.type == "token" for event in events)


def test_sessions_are_isolated():
    flow, _ = build_flow("mock")
    flow.process_turn("Please check invoice INV-2048", session_id="alpha")
    alpha = flow.session_store.get("alpha", "customer_rescue_lead")
    beta = flow.session_store.get("beta", "customer_rescue_lead")
    assert len(alpha.history) == 2
    assert beta.history == []
