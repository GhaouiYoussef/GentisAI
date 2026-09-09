from __future__ import annotations

import logging
import time
import uuid

import streamlit as st

from demos.telemetry import render_trace
from gentis_ai.observability.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

from demos.launch_war_room.gentis_setup import (
    DEFAULT_BRIEF,
    EXPERT_LABELS,
    SCENARIOS,
    build_flow,
)


st.set_page_config(
    page_title="AI Product Launch War Room", page_icon="▲", layout="wide"
)
st.markdown(
    """<style>:root{--paper:#f4f0e6;--ink:#102a35;--signal:#e85d35;--teal:#177e75}.stApp{background:linear-gradient(135deg,#0000 48%,#d9d0bd 49%,#0000 51%) 0 0/42px 42px,var(--paper)}h1,h2,h3{font-family:"Aptos Display","Trebuchet MS",sans-serif}.hero{border:1px solid var(--ink);background:#fbf8f0;padding:1.2rem;box-shadow:7px 7px 0 var(--ink)}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.6rem;margin:1rem 0}.card{border:1px solid var(--ink);background:#fbf8f0;padding:.8rem;font-weight:700;text-transform:uppercase}.card.on{background:var(--teal);color:#fff;box-shadow:3px 3px 0 var(--ink)}.trace{border-left:4px solid var(--signal);background:#fff;padding:.5rem;margin:.35rem 0;font-family:Consolas,monospace;font-size:.78rem}@media(max-width:760px){.grid{grid-template-columns:repeat(2,1fr)}}</style>""",
    unsafe_allow_html=True,
)

if "war_flow" not in st.session_state:
    try:
        st.session_state.war_flow, st.session_state.war_provider = build_flow()
    except Exception:
        logger.exception("War Room provider setup failed")
        st.error("Provider setup failed. Check the selected provider configuration and try again.")
        st.stop()
st.session_state.setdefault("war_session", f"war-{uuid.uuid4().hex[:8]}")
st.session_state.setdefault("war_messages", [])
st.session_state.setdefault("war_selected", [])
st.session_state.setdefault("war_trace", [])

st.markdown(
    f'<div class="hero"><small>GENTISAI / CONTEXTUAL EXPERT ROUTING</small><h1>AI Product Launch War Room</h1><b>{st.session_state.war_provider}</b> · {st.session_state.war_session}</div>',
    unsafe_allow_html=True,
)
st.caption("MockLLM uses scripted routes and answers. Use a real provider to evaluate contextual responses.")
brief = st.text_area("Product brief", DEFAULT_BRIEF, height=100)
cols = st.columns(len(SCENARIOS))
chosen = None
for col, (label, prompt) in zip(cols, SCENARIOS.items()):
    if col.button(label, use_container_width=True):
        chosen = prompt
cards = st.empty()


def render_cards():
    cards.markdown(
        '<div class="grid">'
        + "".join(
            f'<div class="card {"on" if name in st.session_state.war_selected else ""}">{i:02d} / {label}</div>'
            for i, (name, label) in enumerate(EXPERT_LABELS.items(), 1)
        )
        + "</div>",
        unsafe_allow_html=True,
    )


render_cards()
main, rail = st.columns([2, 1])
with rail:
    st.subheader("Decision trace")
    trace_panel = st.empty()
render_trace(trace_panel, st.session_state.war_trace)
with main:
    for item in st.session_state.war_messages:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])
            if item.get("elapsed_ms") is not None:
                st.caption(f"{item['elapsed_ms']} ms measured")
    typed = st.chat_input("Ask the launch team...")
    question = chosen or typed
    if question:
        request = f"Product brief: {brief.strip()}\nLaunch question: {question.strip()}"
        st.session_state.war_messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            out = st.empty()
            text = ""
            trace = []
            st.session_state.war_trace = trace
            st.session_state.war_selected = []
            render_cards()
            render_trace(trace_panel, trace)
            final = None
            started = time.perf_counter()
            try:
                for event in st.session_state.war_flow.stream_turn(
                    request, session_id=st.session_state.war_session
                ):
                    if event.type == "route_finished":
                        st.session_state.war_selected = event.data["decision"]["experts"]
                        trace.append({"type": "route", **event.data["decision"]})
                        render_cards()
                        render_trace(trace_panel, trace)
                    elif event.type == "expert_started":
                        trace.append({"type": "expert", "name": event.agent_name})
                        render_trace(trace_panel, trace)
                    elif event.type == "error":
                        trace.append({"type": "error", "error": "Request failed"})
                        render_trace(trace_panel, trace)
                    elif event.type == "token":
                        text += event.content
                        out.markdown(text + "|")
                    elif event.type == "final":
                        final = event.data["response"]
            except Exception:
                logger.exception("War Room request failed")
                out.empty()
                st.error("The request could not be completed. Please try again.")
            if final:
                out.markdown(final.content)
                elapsed = round((time.perf_counter() - started) * 1000)
                st.caption(f"{elapsed} ms measured")
                st.session_state.war_messages.append(
                    {"role": "assistant", "content": final.content, "elapsed_ms": elapsed}
                )
                st.session_state.war_trace = trace
                st.rerun()
