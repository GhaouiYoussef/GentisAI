from demos.launch_war_room.gentis_setup import DEFAULT_BRIEF, build_flow


def test_risk_question_routes_risk_and_product():
    flow, provider = build_flow("mock")
    response = flow.process_turn(f"Product brief: {DEFAULT_BRIEF}\nQuestion: Find the biggest risks in this product.", session_id="risks")
    assert provider == "MockLLM"
    assert response.structured["routing"]["experts"] == ["risk_analyst", "product_strategist"]


def test_launch_hooks_route_growth_and_copywriter():
    flow, _ = build_flow("mock")
    response = flow.process_turn("Write three launch hooks.", session_id="hooks")
    assert response.structured["routing"]["experts"] == ["growth_marketer", "copywriter"]


def test_weekend_question_routes_technical_and_product():
    flow, _ = build_flow("mock")
    response = flow.process_turn("Can this MVP be built in one weekend?", session_id="weekend")
    assert response.structured["routing"]["experts"] == ["technical_architect", "product_strategist"]


def test_follow_up_reuses_only_its_session_history():
    flow, _ = build_flow("mock")
    flow.process_turn("Write three launch hooks.", session_id="alpha")
    flow.process_turn("Make the second hook more technical.", session_id="alpha")
    alpha = flow.session_store.get("alpha", "product_strategist")
    beta = flow.session_store.get("beta", "product_strategist")
    assert len(alpha.history) == 4
    assert beta.history == []
