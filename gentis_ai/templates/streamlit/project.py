"""Shared backend for terminal chat, Streamlit, and your own application."""

from pathlib import Path

from gentis_ai.project_runtime import build_project_flow


ROOT = Path(__file__).resolve().parent


def build_flow(environment=None):
    """Create one Flow per UI session; pass environment={} for offline tests."""
    return build_project_flow(ROOT, environment=environment)
