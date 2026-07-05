from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

from gentis_ai import Expert, Flow, Router
from provider import DEFAULT_PROVIDER, build_llm

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
PROJECT_CONFIG = PROJECT_ROOT / "gentis.project.json"


def _load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_project_config() -> dict[str, object]:
    return _load_json(PROJECT_CONFIG)


def _load_agent_config(agent_entry: dict[str, object]) -> dict[str, object]:
    agent_path = PROJECT_ROOT / str(agent_entry["path"]) / "agent.json"
    return _load_json(agent_path)


def _load_prompt(relative_path: str) -> str:
    path = PROJECT_ROOT / relative_path
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _load_tools(module_name: str | None) -> list[object]:
    if not module_name:
        return []
    module = importlib.import_module(module_name)
    tools = []
    for name in dir(module):
        if name.startswith("_"):
            continue
        value = getattr(module, name)
        if callable(value):
            tools.append(value)
    return tools


def _build_agent(agent_entry: dict[str, object]) -> Expert:
    agent_config = _load_agent_config(agent_entry)
    return Expert(
        name=str(agent_config["name"]),
        description=str(agent_config.get("description", "")),
        system_prompt=_load_prompt(str(agent_config["prompt"])),
        tools=_load_tools(agent_config.get("tools_module") if isinstance(agent_config.get("tools_module"), str) else None),
    )


def _build_orchestrator(project_config: dict[str, object]) -> Expert | None:
    routing = project_config.get("routing", {})
    orchestrator = routing.get("orchestrator", {})
    if not orchestrator.get("enabled"):
        return None
    orchestrator_config = _load_json(PROJECT_ROOT / str(orchestrator["config"]))
    return Expert(
        name="orchestrator",
        description=str(orchestrator_config.get("description", "Routes requests to the right agent.")),
        system_prompt=_load_prompt(str(orchestrator_config.get("prompt", "orchestrator/prompt.md"))),
    )


def _load_fast_router_rules(project_config: dict[str, object]) -> dict[str, str]:
    routing = project_config.get("routing", {})
    fast_router = routing.get("fast_router", {})
    if not fast_router.get("enabled"):
        return {}
    from routing.fast_router import load_fast_router_rules

    return load_fast_router_rules()


def build_router(llm=None) -> Router:
    project_config = _load_project_config()
    routing = project_config.get("routing", {})
    routing_mode = str(routing.get("mode", "both"))
    experts: list[Expert] = []

    orchestrator = _build_orchestrator(project_config)
    if orchestrator is not None and routing_mode in {"orchestrator", "both"}:
        experts.append(orchestrator)

    for agent_entry in project_config.get("agents", []):
        if agent_entry.get("enabled", True):
            experts.append(_build_agent(agent_entry))

    rules = _load_fast_router_rules(project_config)
    if rules:
        return Router(experts=experts, llm=llm, rules=rules)
    return Router(experts=experts, llm=llm)


def build_flow(llm=None) -> Flow:
    project_config = _load_project_config()
    llm = llm or build_llm(str(project_config.get("default_provider", DEFAULT_PROVIDER)))
    return Flow(router=build_router(llm), llm=llm)


def answer(message: str, session_id: str = "multi-agent-demo") -> str:
    return build_flow().process_turn(message, session_id=session_id).content


if __name__ == "__main__":
    print(answer("I need help with login."))
