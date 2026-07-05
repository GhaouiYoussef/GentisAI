from __future__ import annotations

import json
from pathlib import Path

FAST_ROUTER_CONFIG = Path(__file__).resolve().with_name("fast_router.json")


def load_fast_router_rules() -> dict[str, str]:
    if not FAST_ROUTER_CONFIG.exists():
        return {}
    data = json.loads(FAST_ROUTER_CONFIG.read_text(encoding="utf-8"))
    return {
        str(keyword).lower(): str(agent)
        for keyword, agent in data.get("rules", {}).items()
    }


FAST_ROUTER_RULES = load_fast_router_rules()
