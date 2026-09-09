from __future__ import annotations

import logging
import time
import uuid

import streamlit as st

from demos.customer_rescue.gentis_setup import EXPERT_LABELS, SCENARIOS, build_flow
from demos.telemetry import render_trace
from gentis_ai.observability.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


st.set_page_config(
    page_title="Customer Rescue Command Center", page_icon="◆", layout="wide"
)
st.markdown(
    """
<style>
:root{--paper:#f3efe4;--ink:#13232f;--signal:#ef6a3a;--teal:#2b7a78;--line:#c8c0ad}
.stApp{background:radial-gradient(circle at 80% 0,#d7e5df 0,transparent 30%),linear-gradient(#0000 31px,#d8d0bf 32px),linear-gradient(90deg,#0000 31px,#d8d0bf 32px),var(--paper);background-size:auto,32px 32px,32px 32px;color:var(--ink)}
h1,h2,h3{font-family:"Aptos Display","Trebuchet MS",sans-serif;letter-spacing:-.03em}.eyebrow{font:700 .72rem Aptos,sans-serif;letter-spacing:.16em;text-transform:uppercase;color:var(--signal)}
.mast{border:1px solid var(--ink);background:#f8f4ea;padding:1.2rem 1.4rem;box-shadow:6px 6px 0 var(--ink);margin-bottom:1.2rem}.badges{display:flex;gap:.5rem;flex-wrap:wrap}.badge{border:1px solid var(--ink);padding:.25rem .55rem;background:#fff;font:700 .7rem Aptos,sans-serif;text-transform:uppercase}
.experts{display:grid;grid-template-columns:repeat(6,1fr);gap:.5rem;margin:1rem 0}.expert{min-height:76px;border:1px solid var(--ink);background:#f8f4ea;padding:.65rem;font:700 .75rem Aptos,sans-serif;text-transform:uppercase}.expert.active{background:var(--signal);color:#fff;box-shadow:3px 3px 0 var(--ink)}
.event{border-left:4px solid var(--teal);background:#fff;padding:.55rem .7rem;margin:.4rem 0;font:.78rem Consolas,monospace}.metric{font:700 1rem Consolas,monospace;color:var(--teal)}
@media(max-width:760px){.experts{grid-template-columns:repeat(2,1fr)}.mast{box-shadow:3px 3px 0 var(--ink)}}
</style>""",
    unsafe_allow_html=True,
)


def initialize_state() -> None:
    if "rescue_flow" not in st.session_state:
        flow, label = build_flow()
        st.session_state.rescue_flow = flow
        st.session_state.rescue_provider = label
    st.session_state.setdefault("rescue_session_id", f"rescue-{uuid.uuid4().hex[:8]}")
    st.session_state.setdefault("rescue_messages", [])
    st.session_state.setdefault("rescue_events", [])
    st.session_state.setdefault("rescue_selected", [])


def new_session() -> None:
    st.session_state.rescue_session_id = f"rescue-{uuid.uuid4().hex[:8]}"
    st.session_state.rescue_messages = []
    st.session_state.rescue_events = []
    st.session_state.rescue_selected = []


try:
    initialize_state()
except Exception:
    logger.exception("Customer Rescue provider setup failed")
    st.error("Provider setup failed. Check the selected provider configuration and try again.")
    st.stop()
st.caption("Fictional customer data and tools. MockLLM uses scripted routes and answers.")
st.markdown(
    f"""<div class="mast"><div class="eyebrow">GentisAI / Live routing demo</div><h1>Customer Rescue Command Center</h1><div class="badges"><span class="badge">{st.session_state.rescue_provider}</span><span class="badge">Session {st.session_state.rescue_session_id}</span></div></div>""",
    unsafe_allow_html=True,
)

top = st.columns([4, 1])
with top[0]:
    st.caption("Choose a scenario or type a real customer message.")
with top[1]:
    st.button("New session", on_click=new_session, use_container_width=True)

scenario_cols = st.columns(3)
chosen = None
for column, (label, prompt) in zip(scenario_cols, SCENARIOS.items()):
    if column.button(label, use_container_width=True):
        chosen = prompt

cards = st.empty()


def render_cards():
    cards.markdown(
        '<div class="experts">'
        + "".join(
            f'<div class="expert {"active" if name in st.session_state.rescue_selected else ""}">{label}</div>'
            for name, label in EXPERT_LABELS.items()
        )
        + "</div>",
        unsafe_allow_html=True,
    )


render_cards()
chat, rail = st.columns([2.1, 1])
with rail:
    st.subheader("Routing telemetry")
    trace_panel = st.empty()
render_trace(trace_panel, st.session_state.rescue_events)
with chat:
    for item in st.session_state.rescue_messages:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])
            if item.get("elapsed_ms") is not None:
                st.caption(f"{item['elapsed_ms']} ms measured")
    typed = st.chat_input("Describe the customer issue...")
    prompt = chosen or typed
    if prompt:
        st.session_state.rescue_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            placeholder = st.empty()
            started = time.perf_counter()
            text = ""
            timeline = []
            st.session_state.rescue_events = timeline
            st.session_state.rescue_selected = []
            render_cards()
            render_trace(trace_panel, timeline)
            final = None
            try:
                for event in st.session_state.rescue_flow.stream_turn(
                    prompt, session_id=st.session_state.rescue_session_id
                ):
                    if event.type == "route_finished":
                        st.session_state.rescue_selected = event.data["decision"][
                            "experts"
                        ]
                        timeline.append({"type": "route", **event.data["decision"]})
                        render_cards()
                        render_trace(trace_panel, timeline)
                    elif event.type in {
                        "expert_started",
                        "tool_call",
                        "tool_result",
                        "error",
                    }:
                        timeline.append(
                            {"type": event.type, "name": event.agent_name, "error": event.error, **event.data}
                        )
                        render_trace(trace_panel, timeline)
                    elif event.type == "token":
                        text += event.content
                        placeholder.markdown(text + "|")
                    elif event.type == "final":
                        final = event.data["response"]
            except Exception:
                logger.exception("Customer Rescue request failed")
                placeholder.empty()
                st.error("The request could not be completed. Please try again.")
            if final is not None:
                text = final.content
                placeholder.markdown(text)
                elapsed = round((time.perf_counter() - started) * 1000)
                st.session_state.rescue_events = timeline
                st.session_state.rescue_messages.append(
                    {"role": "assistant", "content": text, "elapsed_ms": elapsed}
                )
                st.caption(f"{elapsed} ms measured")
                st.rerun()
