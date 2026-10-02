"""Runtime for editable projects created by ``gentis init``."""

from __future__ import annotations

import importlib.util
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType
from typing import Any
import sys

from gentis_ai import (
    Expert,
    Flow,
    Router,
    RoutingDecision,
    ToolCall,
    ToolExecutor,
    ToolRegistry,
)
from gentis_ai.config import load_environment
from gentis_ai.providers import ProviderSettings, build_llm


def project_file(root: Path, relative: str) -> Path:
    """Resolve a project-owned path, rejecting escapes and symbolic links."""
    base = root.resolve()
    candidate = base / relative
    if (
        not relative
        or Path(relative).is_absolute()
        or not candidate.resolve().is_relative_to(base)
    ):
        raise ValueError("Project paths must be relative files inside the project.")
    for part in (candidate, *candidate.parents):
        if part == base:
            break
        if part.is_symlink():
            raise ValueError(
                "Project files and directories must not be symbolic links."
            )
    return candidate


def load_project_manifest(root: Path) -> dict[str, Any]:
    """Validate explicit agent/tool registrations before loading local code."""
    path = project_file(root, "gentis.json")
    if not path.is_file():
        raise ValueError("No Gentis project found. Run gentis init first.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Project gentis.json must contain valid JSON.") from exc
    if (
        not isinstance(data, dict)
        or not isinstance(data.get("agents"), dict)
        or not data["agents"]
    ):
        raise ValueError(
            "Project needs an agents registry. Run gentis init in a new directory."
        )
    if not isinstance(data.get("tools"), dict):
        raise ValueError("Project gentis.json needs a tools registry.")
    if (
        not isinstance(data.get("default_agent"), str)
        or data["default_agent"] not in data["agents"]
    ):
        raise ValueError("Project default_agent must name a registered agent.")
    for name, entry in data["tools"].items():
        if not isinstance(entry, dict) or not isinstance(entry.get("function"), str):
            raise ValueError(f"Tool {name!r} needs a function name.")
        _registered_file(root, entry.get("module"), suffix=".py")
    for name, entry in data["agents"].items():
        if not isinstance(entry, dict):
            raise ValueError(f"Invalid registration for agent {name!r}.")
        _registered_file(root, entry.get("module"), suffix=".py")
        _registered_file(root, entry.get("prompt"), suffix=".md")
        attached = entry.get("tools")
        if (
            not isinstance(attached, list)
            or not all(isinstance(tool, str) for tool in attached)
            or len(set(attached)) != len(attached)
            or any(tool not in data["tools"] for tool in attached)
        ):
            raise ValueError(f"Agent {name!r} must list unique registered tools.")
    return data


def _registered_file(root: Path, value: object, *, suffix: str) -> Path:
    if not isinstance(value, str) or Path(value).suffix != suffix:
        raise ValueError(f"Registered project files must use {suffix} paths.")
    path = project_file(root, value)
    if not path.is_file():
        raise ValueError(f"Registered project file does not exist: {value}.")
    return path


def _load_module(path: Path) -> ModuleType:
    identifier = hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(f"gentis_project_{identifier}", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load project module {path.name}.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    # Reload edits immediately, even when file size and cached timestamp match.
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), module.__dict__)
    return module


def build_project_flow(
    root: Path | str, environment: Mapping[str, str] | None = None
) -> Flow:
    """Build isolated session state and execute the selected agent's context tools."""
    root = Path(root).resolve()
    manifest = load_project_manifest(root)
    environment = (
        load_environment(root / ".env") if environment is None else environment
    )
    settings = ProviderSettings.from_environment(environment)
    llm = build_llm(environment)
    registry = ToolRegistry()
    for name, entry in manifest["tools"].items():
        module = _load_module(project_file(root, entry["module"]))
        function = getattr(module, entry["function"], None)
        if not callable(function):
            raise ValueError(f"Tool {name!r} must refer to a callable function.")
        spec = registry.register(function)
        if (
            spec.name != name
            or set(spec.parameters["properties"]) != {"query"}
            or spec.parameters["properties"]["query"].get("type") != "string"
        ):
            raise ValueError(
                f"Tool {name!r} must have the same function name and accept query: str."
            )

    experts = []
    for name, entry in manifest["agents"].items():
        module = _load_module(project_file(root, entry["module"]))
        factory = getattr(module, "build_agent", None)
        if not callable(factory):
            raise ValueError(f"Agent {name!r} must define build_agent(system_prompt).")
        prompt = project_file(root, entry["prompt"]).read_text(encoding="utf-8")
        expert = factory(prompt)
        if not isinstance(expert, Expert) or expert.name != name:
            raise ValueError(
                f"Agent {name!r} must build an Expert with its registered name."
            )
        if expert.tools:
            raise ValueError(
                "Register context tools in gentis.json; native Expert.tools need a custom execution flow."
            )
        experts.append(expert)

    def context_tools(message: str, decision: RoutingDecision) -> list[ToolCall]:
        names = dict.fromkeys(
            tool
            for agent in decision.experts
            for tool in manifest["agents"][agent]["tools"]
        )
        return [ToolCall(name=name, arguments={"query": message}) for name in names]

    default = next(
        expert for expert in experts if expert.name == manifest["default_agent"]
    )
    router = Router(
        experts,
        llm=llm if settings.provider != "mock" else None,
        default_expert=default,
        enable_hybrid=False,
        routing_max_tokens=settings.routing_max_tokens,
    )
    return Flow(
        router,
        llm=llm,
        tool_policy=context_tools,
        tool_executor=ToolExecutor(
            registry, max_tool_calls=max(1, len(manifest["tools"]))
        ),
    )
