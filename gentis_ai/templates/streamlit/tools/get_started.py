def get_started(query: str) -> dict[str, str]:
    """Return the editable project's getting-started guide."""
    return {
        "guide": "Edit agents/assistant.py and prompts/assistant.md to customize your agent.",
        "add_agent": "gentis add agent billing --description 'Handles billing questions.'",
        "add_tool": "gentis add tool lookup_invoice --agent billing",
    }
