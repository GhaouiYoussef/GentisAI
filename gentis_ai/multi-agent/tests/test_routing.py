from gentis_ai.llm import MockLLM

from app import build_flow


def test_answer_routes_support_requests():
    flow = build_flow(
        MockLLM(
            routing_rules={"help": "support", "price": "sales"},
            responses={"help": "support response", "price": "sales response"},
        )
    )

    response = flow.process_turn("I need help with login.", session_id="multi-agent-test")

    assert response.agent_name == "support"
    assert "support" in response.content.lower()
