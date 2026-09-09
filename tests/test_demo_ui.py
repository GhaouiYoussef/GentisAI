from pathlib import Path

import pytest
import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from streamlit.testing.v1 import AppTest

from gentis_ai.core.events import FlowEvent
from gentis_ai.core.types import TurnResponse


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("demo,button", [("customer_rescue", "Customer rescue"), ("launch_war_room", "Launch hooks")])
def test_demo_renders_events_before_generation_finishes(demo, button, monkeypatch):
    monkeypatch.setenv("GENTIS_PROVIDER", "mock")
    app = AppTest.from_file(str(ROOT / "demos" / demo / "app.py"), default_timeout=20).run()
    rendered = []
    original = DeltaGenerator.markdown

    def capture(self, body, *args, **kwargs):
        rendered.append(str(body))
        return original(self, body, *args, **kwargs)

    monkeypatch.setattr(DeltaGenerator, "markdown", capture)
    original_markdown = st.markdown

    def capture_markdown(body, *args, **kwargs):
        rendered.append(str(body))
        return original_markdown(body, *args, **kwargs)

    monkeypatch.setattr(st, "markdown", capture_markdown)
    expert = "billing" if demo == "customer_rescue" else "copywriter"

    class StreamingFlow:
        def stream_turn(self, *args, **kwargs):
            yield FlowEvent(type="route_finished", data={"decision": {"experts": [expert], "confidence": 1.0}})
            active_class = 'expert active' if demo == "customer_rescue" else 'card on'
            assert any(active_class in text for text in rendered), "Expert card must activate before tokens"
            assert any("ROUTE" in text for text in rendered), "Route must display before tokens"
            yield FlowEvent(type="token", content="A streamed answer")
            yield FlowEvent(type="final", data={"response": TurnResponse(content="A streamed answer", agent_name=expert, switched_context=False)})

    app.session_state["rescue_flow" if demo == "customer_rescue" else "war_flow"] = StreamingFlow()
    next(item for item in app.button if item.label == button).click().run()
    assert not app.exception
    assert not app.error
    assert any("ms measured" in item.value for item in app.caption)


def test_customer_rescue_displays_tool_result_payload(monkeypatch):
    monkeypatch.setenv("GENTIS_PROVIDER", "mock")
    app = AppTest.from_file(str(ROOT / "demos/customer_rescue/app.py"), default_timeout=20).run()
    next(item for item in app.button if item.label == "Customer rescue").click().run()
    assert not app.exception
    assert any("INV-2048" in item.value and "TOOL RESULT" in item.value for item in app.markdown)
    assert any("ticket_id" in item.value for item in app.markdown)


def test_trace_replacement_removes_previous_turn_rows():
    app = AppTest.from_string('''
import streamlit as st
from demos.telemetry import render_trace
panel = st.empty()
render_trace(panel, [{"type": "old one"}, {"type": "old two"}])
render_trace(panel, [])
render_trace(panel, [{"type": "new one"}])
''').run()
    assert not app.exception
    assert len(app.markdown) == 1
    assert "NEW ONE" in app.markdown[0].value


@pytest.mark.parametrize("demo,button,flow_key", [
    ("customer_rescue", "Customer rescue", "rescue_flow"),
    ("launch_war_room", "Launch hooks", "war_flow"),
])
def test_demo_errors_do_not_expose_provider_details(demo, button, flow_key, monkeypatch):
    monkeypatch.setenv("GENTIS_PROVIDER", "mock")
    app = AppTest.from_file(str(ROOT / "demos" / demo / "app.py"), default_timeout=20).run()

    class BrokenFlow:
        def stream_turn(self, *args, **kwargs):
            raise RuntimeError("private-provider-detail")

    app.session_state[flow_key] = BrokenFlow()
    next(item for item in app.button if item.label == button).click().run()
    assert not app.exception
    assert app.error[0].value == "The request could not be completed. Please try again."
    assert all("private-provider-detail" not in item.value for item in app.markdown)


def test_trace_escapes_tool_payload_html():
    app = AppTest.from_string('''
import streamlit as st
from demos.telemetry import render_trace
render_trace(st.empty(), [{"type": "tool_result", "result": {
    "name": "lookup", "output": "<script>alert(1)</script>"
}}])
''').run()
    assert not app.exception
    assert "<script>" not in app.markdown[0].value
    assert "&lt;script&gt;" in app.markdown[0].value
