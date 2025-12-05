import os

def _load_prompt(path_parts):
    """Reads a prompt file from within the package."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, *path_parts)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: Prompt file not found at {file_path}"

# Quick Start Prompts
QUICK_START_ORCHESTRATOR = _load_prompt(["orchestrator", "quick_start", "orchestrator.md"])
QUICK_START_SALES = _load_prompt(["experts", "quick_start", "sales_expert.md"])
QUICK_START_SUPPORT = _load_prompt(["experts", "quick_start", "support_expert.md"])