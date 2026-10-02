"""Run with gentis run --ui or python -m streamlit run streamlit_app.py."""

from uuid import uuid4

import streamlit as st

from project import build_flow


st.set_page_config(page_title="My GentisAI Agents", page_icon="G", layout="centered")
st.title("My GentisAI Agents")
st.caption("Your agents, tools, and conversation in one place.")

# Never cache a Flow globally: each browser session owns its provider and memory.
if "gentis_flow" not in st.session_state:
    st.session_state.gentis_flow = build_flow()
    st.session_state.gentis_session_id = uuid4().hex
    st.session_state.gentis_messages = []

flow = st.session_state.gentis_flow
with st.sidebar:
    st.header("Your project")
    st.write("Agents: " + ", ".join(flow.router.experts))
    selected = flow.router.default_expert.name
    if flow.router.llm is None:
        st.info(
            "Offline mode uses simulated answers. Select an agent to try its tools."
        )
        selected = st.selectbox("Agent", list(flow.router.experts))
    else:
        st.caption(
            "Your provider routes requests using agent descriptions and conversation context."
        )
    if st.button("New conversation") or selected != st.session_state.get(
        "gentis_selected", selected
    ):
        st.session_state.gentis_session_id = uuid4().hex
        st.session_state.gentis_messages = []
    st.session_state.gentis_selected = selected
    st.caption("After editing agents or tools, reload the project.")
    if st.button("Reload project"):
        st.session_state.gentis_flow = build_flow()
        st.session_state.gentis_session_id = uuid4().hex
        st.session_state.gentis_messages = []
        st.rerun()

session_id = st.session_state.gentis_session_id
if flow.router.llm is None:
    flow.session_store.save(flow.session_store.get(session_id, selected))

for item in st.session_state.gentis_messages:
    with st.chat_message(item["role"]):
        if item.get("agent"):
            st.caption(item["agent"])
        st.markdown(item["content"])

if message := st.chat_input("Ask your agents anything"):
    st.session_state.gentis_messages.append({"role": "user", "content": message})
    with st.chat_message("user"):
        st.markdown(message)
    with st.chat_message("assistant"):
        with st.spinner("Working..."):
            response = flow.process_turn(message, session_id=session_id)
        st.caption(response.agent_name)
        st.markdown(response.content)
        if response.structured.get("tools"):
            with st.expander("Tool results"):
                st.json(response.structured["tools"])
    st.session_state.gentis_messages.append(
        {
            "role": "assistant",
            "agent": response.agent_name,
            "content": response.content,
        }
    )
