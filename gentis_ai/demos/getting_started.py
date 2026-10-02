"""Copyable CLI commands for users who want to extend a running demo."""

import streamlit as st


def render_getting_started(name: str) -> None:
    with st.expander("Build your own: export this demo or create an agent project"):
        st.markdown(
            "**Make this demo yours.** Run these commands in your terminal to copy "
            "the complete app, agent setup, tools, and telemetry into an editable folder."
        )
        st.code(
            f"gentis demo {name} --export my-{name}\n"
            f"cd my-{name}\n"
            "python -m pip install -r requirements.txt\n"
            "gentis configure --provider mock\n"
            "gentis run",
            language="bash",
        )
        st.caption(
            "Edit app.py for the interface and demo_app/gentis_setup.py for the agents. "
            "Restart the app after changing agent setup."
        )
        st.markdown("**Start a new agent project with CLI-managed modules.**")
        st.code(
            "gentis init my-agent\ncd my-agent\n"
            'gentis add agent billing --description "Handles invoices and refunds"\n'
            "gentis add tool lookup_invoice --agent billing\ngentis run --ui",
            language="bash",
        )
        st.caption(
            "The add commands extend the new modular project. Customize the exported "
            "demo by editing its local demo_app files."
        )
