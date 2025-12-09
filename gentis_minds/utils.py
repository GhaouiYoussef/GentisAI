# ANSI Color Codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    GREY = '\033[90m'

EMOJI_RANGE_REGEX = r"[\U0001F300-\U0001FAFF\U0001F000-\U0001F02F\u2600-\u27BF]"
VARIATION_JOINERS_REGEX = r"[\uFE0F\u200D]"
import os
def load_prompt(filename):
    """Helper to load prompt content from the prompts directory."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "prompts", filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Could not find prompt file: {path}")
        return ""