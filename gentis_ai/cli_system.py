from __future__ import annotations

import argparse
import importlib
import json
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import Any

from gentis_ai import Expert, Flow, Router
from gentis_ai.llm import (
    AzureOpenAILLM,
    BedrockLLM,
    GeminiLLM,
    MockLLM,
    OllamaLLM,
    OpenAICompatibleLLM,
    VLLMLLM,
)


PROVIDER_CHOICES = ["azure", "gemini", "openai", "ollama", "bedrock", "vllm"]
PROJECT_MANIFEST_FILE = "gentis.project.json"
ROUTING_MODE_CHOICES = ["fast_router", "orchestrator", "both"]
FIRST_ENCOUNTER_CHOICES = ["fast_router", "orchestrator"]
PROVIDER_SHORTCUTS = {
    "azure": "azure",
    "google": "gemini",
    "gemini": "gemini",
    "openai": "openai",
    "chatgpt": "openai",
    "ollama": "ollama",
    "bedrock": "bedrock",
    "aws": "bedrock",
    "vllm": "vllm",
}


@dataclass(frozen=True)
class ProjectSpec:
    name: str
    default_provider: str
    routing_mode: str
    first_encounter: str
    orchestrator_provider: str | None


@dataclass(frozen=True)
class AgentSpec:
    name: str
    description: str
    keywords: list[str]
    example: bool = False
    enabled: bool = True

    @property
    def prompt_path(self) -> str:
        return f"agents/{self.name}/prompt.md"

    @property
    def tools_path(self) -> str:
        return f"agents/{self.name}/tools.py"

    @property
    def agent_path(self) -> str:
        return f"agents/{self.name}/agent.json"

    @property
    def tools_module(self) -> str:
        return f"agents.{self.name}.tools"



def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="gentis")
    subcommands = parser.add_subparsers(dest="command", required=True)

    new_parser = subcommands.add_parser("new", help="Create a new GentisAI project.")
    new_parser.add_argument("name")
    new_parser.add_argument("--provider", choices=PROVIDER_CHOICES)
    new_parser.add_argument("--azure", action="store_true", help="Use Azure OpenAI.")
    new_parser.add_argument("--google", action="store_true", help="Use Gemini.")
    new_parser.add_argument("--openai", action="store_true", help="Use OpenAI.")
    new_parser.add_argument("--ollama", action="store_true", help="Use Ollama.")
    new_parser.add_argument("--bedrock", action="store_true", help="Use AWS Bedrock.")
    new_parser.add_argument("--vllm", action="store_true", help="Use vLLM.")
    new_parser.add_argument(
        "--routing-mode",
        choices=ROUTING_MODE_CHOICES,
        help="Routing setup for the generated project.",
    )
    new_parser.add_argument(
        "--first-encounter",
        choices=FIRST_ENCOUNTER_CHOICES,
        help="Which router handles the first encounter when both are enabled.",
    )
    new_parser.add_argument(
        "--orchestrator-provider",
        choices=PROVIDER_CHOICES,
        help="Provider for the orchestrator when it differs from the default provider.",
    )
    new_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files in the generated project.",
    )

    agent_parser = subcommands.add_parser(
        "agent",
        help="Manage agents inside an existing GentisAI project.",
    )
    agent_subcommands = agent_parser.add_subparsers(dest="agent_command", required=True)
    add_parser = agent_subcommands.add_parser("add", help="Add a new agent to a project.")
    add_parser.add_argument("name")
    add_parser.add_argument("--project", help="Path to the project root.")
    add_parser.add_argument("--description")
    add_parser.add_argument("--keywords", help="Comma-separated routing keywords.")
    add_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing agent files if the agent already exists.",
    )

    subcommands.add_parser("run", help="Run a local mock chat loop.")
    subcommands.add_parser("eval", help="Run the offline routing eval.")
    subcommands.add_parser("bench", help="Run a tiny offline latency benchmark.")

    args = parser.parse_args(argv)
    if args.command == "new":
        provider = _resolve_provider(args, parser)
        routing_mode = args.routing_mode or _prompt_routing_mode()
        first_encounter = _resolve_first_encounter(args, routing_mode)
        orchestrator_provider = _resolve_orchestrator_provider(
            args,
            provider,
            routing_mode,
        )
        create_project(
            name=args.name,
            default_provider=provider,
            routing_mode=routing_mode,
            first_encounter=first_encounter,
            orchestrator_provider=orchestrator_provider,
            overwrite=args.overwrite,
        )
    elif args.command == "agent" and args.agent_command == "add":
        add_agent(
            name=args.name,
            project_root=Path(args.project).expanduser().resolve() if args.project else None,
            description=args.description,
            keywords=_split_csv(args.keywords),
            overwrite=args.overwrite,
        )
    elif args.command == "run":
        run_mock_chat()
    elif args.command == "eval":
        run_eval()
    elif args.command == "bench":
        run_bench()



def create_project(
    name: str,
    default_provider: str,
    routing_mode: str,
    first_encounter: str,
    orchestrator_provider: str | None,
    overwrite: bool = False,
) -> None:
    root = Path(name).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    spec = ProjectSpec(
        name=name,
        default_provider=default_provider,
        routing_mode=routing_mode,
        first_encounter=first_encounter,
        orchestrator_provider=orchestrator_provider,
    )
    manifest = _build_project_manifest(spec, agents=_initial_agents())
    files = _project_files(spec, manifest)

    created, skipped = _write_files(root, files, overwrite=overwrite)
    print(
        json.dumps(
            {
                "project": str(root),
                "created": created,
                "skipped": skipped,
            },
            indent=2,
        )
    )



def add_agent(
    name: str,
    project_root: Path | None,
    description: str | None,
    keywords: list[str],
    overwrite: bool = False,
) -> None:
    root = project_root or _find_project_root(Path.cwd())
    if root is None:
        if not _prompt_yes_no(
            "No Gentis project was found. Create a new project system now?",
            default=True,
        ):
            raise SystemExit(1)

        project_name = _prompt_text("Project name")
        default_provider = _resolve_provider_from_prompt()
        routing_mode = _prompt_routing_mode()
        first_encounter = _resolve_first_encounter_from_prompt(routing_mode)
        orchestrator_provider = _resolve_orchestrator_provider_from_prompt(
            default_provider,
            routing_mode,
        )
        create_project(
            name=project_name,
            default_provider=default_provider,
            routing_mode=routing_mode,
            first_encounter=first_encounter,
            orchestrator_provider=orchestrator_provider,
            overwrite=overwrite,
        )
        root = Path(project_name).expanduser().resolve()

    manifest = _load_project_manifest(root)
    if manifest is None:
        raise SystemExit(f"No Gentis project manifest found in {root}.")

    agent = AgentSpec(
        name=name,
        description=description or f"Handles {name} requests.",
        keywords=keywords or [name],
    )
    updated_manifest = _apply_agent_to_manifest(manifest, agent)
    created = _write_agent_bundle(root, agent, overwrite=overwrite)
    _save_json(root / PROJECT_MANIFEST_FILE, updated_manifest)

    manifest_files = _project_files_from_manifest(updated_manifest)
    _write_text(root / "routing/fast_router.json", manifest_files["routing/fast_router.json"], overwrite=True)
    _write_text(root / "routing/fast_router.py", manifest_files["routing/fast_router.py"], overwrite=True)
    _write_text(root / "app.py", manifest_files["app.py"], overwrite=True)

    print(
        json.dumps(
            {
                "project": str(root),
                "agent_added": agent.name,
                "created": [
                    f"agents/{agent.name}/prompt.md",
                    f"agents/{agent.name}/tools.py",
                    f"agents/{agent.name}/agent.json",
                ],
                "updated": [PROJECT_MANIFEST_FILE, "routing/fast_router.json", "routing/fast_router.py", "app.py"],
            },
            indent=2,
        )
    )



def run_mock_chat() -> None:
    flow = _build_demo_flow()
    print("GentisAI mock chat. Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in {"exit", "quit"}:
            return
        response = flow.process_turn(user_input, session_id="cli")
        print(f"{response.agent_name}: {response.content}")



def run_eval() -> None:
    flow = _build_demo_flow()
    cases = {
        "I need help with login": "support",
        "I want to buy a plan": "sales",
        "hello": "orchestrator",
    }
    results = []
    for query, expected in cases.items():
        response = flow.process_turn(query, session_id=f"eval-{query}")
        results.append(response.agent_name == expected)
        print(json.dumps({"query": query, "expected": expected, "got": response.agent_name}))
    accuracy = sum(results) / len(results)
    print(json.dumps({"accuracy": accuracy}))
    if accuracy < 1.0:
        raise SystemExit(1)



def run_bench() -> None:
    flow = _build_demo_flow()
    samples = []
    for index in range(10):
        start = time.perf_counter()
        flow.process_turn("I need help with login", session_id=f"bench-{index}")
        samples.append((time.perf_counter() - start) * 1000)

    sorted_samples = sorted(samples)
    print(
        json.dumps(
            {
                "runs": len(samples),
                "p50_ms": statistics.median(sorted_samples),
                "p95_ms": sorted_samples[min(len(sorted_samples) - 1, int(len(sorted_samples) * 0.95))],
            }
        )
    )



def _build_demo_flow() -> Flow:
    llm = MockLLM(
        routing_rules={"help": "support", "buy": "sales", "hello": "orchestrator"},
        responses={
            "help": "I can help troubleshoot that.",
            "buy": "I can explain plans and pricing.",
            "hello": "Hello. How can I help?",
        },
    )
    experts = [
        Expert(name="support", description="Handles product support."),
        Expert(name="sales", description="Handles sales and pricing."),
    ]
    return Flow(Router(experts, llm=llm), llm=llm)



def _resolve_provider(args: argparse.Namespace, parser: argparse.ArgumentParser) -> str:
    explicit = [name for name in PROVIDER_SHORTCUTS if getattr(args, name, False)]
    if args.provider and explicit:
        parser.error("Use either --provider or one provider shortcut, not both.")
    if args.provider:
        return args.provider
    if len(explicit) > 1:
        parser.error("Choose only one provider shortcut.")
    if explicit:
        return PROVIDER_SHORTCUTS[explicit[0]]
    return _resolve_provider_from_prompt()



def _resolve_provider_from_prompt() -> str:
    options = [
        ("azure", "Azure OpenAI"),
        ("gemini", "Gemini"),
        ("openai", "OpenAI-compatible"),
        ("ollama", "Ollama"),
        ("bedrock", "AWS Bedrock"),
        ("vllm", "vLLM"),
    ]
    print("Choose a provider:")
    for index, (_, label) in enumerate(options, start=1):
        print(f"  {index}. {label}")
    while True:
        response = input("Provider [1]: ").strip().lower()
        if not response:
            return "azure"
        if response.isdigit() and 1 <= int(response) <= len(options):
            return options[int(response) - 1][0]
        for key, label in options:
            if response in {key, label.lower()}:
                return key
        print("Please choose one of the listed providers.")



def _prompt_routing_mode() -> str:
    print("Routing setup:")
    print("  1. Fast router only")
    print("  2. Orchestrator only")
    print("  3. Both")
    while True:
        response = input("Routing mode [3]: ").strip()
        if not response:
            return "both"
        if response == "1":
            return "fast_router"
        if response == "2":
            return "orchestrator"
        if response == "3":
            return "both"
        print("Please choose 1, 2, or 3.")



def _resolve_first_encounter(args: argparse.Namespace, routing_mode: str) -> str:
    if routing_mode != "both":
        return routing_mode
    if args.first_encounter:
        return args.first_encounter
    return _resolve_first_encounter_from_prompt(routing_mode)



def _resolve_first_encounter_from_prompt(routing_mode: str) -> str:
    if routing_mode != "both":
        return routing_mode
    print("First encounter router:")
    print("  1. Fast router")
    print("  2. Orchestrator")
    while True:
        response = input("First encounter [1]: ").strip()
        if not response:
            return "fast_router"
        if response == "1":
            return "fast_router"
        if response == "2":
            return "orchestrator"
        print("Please choose 1 or 2.")



def _resolve_orchestrator_provider(
    args: argparse.Namespace,
    default_provider: str,
    routing_mode: str,
) -> str | None:
    if routing_mode == "fast_router":
        return None
    if args.orchestrator_provider:
        return args.orchestrator_provider
    same_provider = _prompt_yes_no(
        "Use same provider for orchestrator as default provider?",
        default=True,
    )
    if same_provider:
        return default_provider
    return _resolve_provider_from_prompt()



def _resolve_orchestrator_provider_from_prompt(
    default_provider: str,
    routing_mode: str,
) -> str | None:
    if routing_mode == "fast_router":
        return None
    same_provider = _prompt_yes_no(
        "Use same provider for orchestrator as default provider?",
        default=True,
    )
    if same_provider:
        return default_provider
    return _resolve_provider_from_prompt()



def _prompt_yes_no(question: str, default: bool) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        response = input(f"{question} {suffix} ").strip().lower()
        if not response:
            return default
        if response in {"y", "yes"}:
            return True
        if response in {"n", "no"}:
            return False
        print("Please answer yes or no.")



def _prompt_text(question: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    response = input(f"{question}{suffix}: ").strip()
    if response:
        return response
    return default or ""



def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]



def _find_project_root(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / PROJECT_MANIFEST_FILE).exists():
            return candidate
    return None



def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))



def _save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")



def _write_text(path: Path, content: str, overwrite: bool = False) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        return False
    path.write_text(content, encoding="utf-8")
    return True



def _write_json(path: Path, data: dict[str, Any], overwrite: bool = False) -> bool:
    return _write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n", overwrite=overwrite)



def _write_files(root: Path, files: dict[str, str], overwrite: bool = False) -> tuple[list[str], list[str]]:
    created: list[str] = []
    skipped: list[str] = []
    for relative_path, content in files.items():
        path = root / relative_path
        if _write_text(path, content, overwrite=overwrite):
            created.append(relative_path)
        else:
            skipped.append(relative_path)
    return created, skipped



def _write_project_changes(
    root: Path,
    files: dict[str, str],
    overwrite: bool = True,
    replace: bool = True,
) -> tuple[list[str], list[str]]:
    created: list[str] = []
    updated: list[str] = []
    for relative_path, content in files.items():
        path = root / relative_path
        existed = path.exists()
        if _write_text(path, content, overwrite=overwrite or replace):
            if existed:
                updated.append(relative_path)
            else:
                created.append(relative_path)
        elif existed:
            updated.append(relative_path)
    return created, updated



def _initial_agents() -> list[AgentSpec]:
    return [
        AgentSpec(
            name="support",
            description="Example agent for technical support and troubleshooting.",
            keywords=["help", "issue", "bug", "login"],
            example=True,
        ),
        AgentSpec(
            name="sales",
            description="Example agent for pricing and buying questions.",
            keywords=["price", "pricing", "buy", "plan"],
            example=True,
        ),
    ]



def _build_project_manifest(spec: ProjectSpec, agents: list[AgentSpec]) -> dict[str, Any]:
    return {
        "schema_version": "0.2",
        "name": spec.name,
        "default_provider": spec.default_provider,
        "routing": {
            "mode": spec.routing_mode,
            "first_encounter": spec.first_encounter,
            "fast_router": {
                "enabled": spec.routing_mode in {"fast_router", "both"},
                "type": "keyword",
                "provider": None,
                "config": "routing/fast_router.json",
            },
            "orchestrator": {
                "enabled": spec.routing_mode in {"orchestrator", "both"},
                "provider": spec.orchestrator_provider,
                "prompt": "orchestrator/prompt.md",
                "config": "orchestrator/orchestrator.json",
            },
        },
        "agents": [
            {
                "name": agent.name,
                "path": f"agents/{agent.name}",
                "enabled": agent.enabled,
                "example": agent.example,
            }
            for agent in agents
        ],
    }



def _apply_agent_to_manifest(manifest: dict[str, Any], agent: AgentSpec) -> dict[str, Any]:
    agents = list(manifest.get("agents", []))
    entry = {
        "name": agent.name,
        "path": f"agents/{agent.name}",
        "enabled": agent.enabled,
        "example": agent.example,
    }
    agents = [existing for existing in agents if existing.get("name") != agent.name]
    agents.append(entry)
    manifest["agents"] = agents
    return manifest



def _project_files(spec: ProjectSpec, manifest: dict[str, Any]) -> dict[str, str]:
    sample_agents = _initial_agents()
    files = {
        "app.py": _app_template(),
        "provider.py": _provider_template(spec.default_provider),
        PROJECT_MANIFEST_FILE: _json_text(manifest),
        "requirements.txt": _requirements_template(spec.default_provider),
        "Dockerfile": _dockerfile_template(),
        ".env.example": _env_template(spec.default_provider, spec.orchestrator_provider),
        "tests/test_routing.py": _project_test_template(),
        "orchestrator/prompt.md": _orchestrator_prompt_template(),
        "orchestrator/orchestrator.json": _orchestrator_config_template(spec),
        "routing/fast_router.json": _fast_router_json_template_from_agents(sample_agents),
        "routing/fast_router.py": _fast_router_py_template(),
    }
    for agent in sample_agents:
        files.update(_agent_files(agent, example=True))
    return files



def _project_files_from_manifest(manifest: dict[str, Any]) -> dict[str, str]:
    return {
        PROJECT_MANIFEST_FILE: _json_text(manifest),
        "routing/fast_router.json": _fast_router_json_template_from_manifest(manifest),
        "routing/fast_router.py": _fast_router_py_template(),
        "app.py": _app_template(),
    }



def _agent_files(agent: AgentSpec, example: bool) -> dict[str, str]:
    return {
        agent.agent_path: _agent_manifest_template(agent, example=example),
        agent.prompt_path: _agent_prompt_template(agent, example=example),
        agent.tools_path: _agent_tools_template(agent, example=example),
    }



def _agent_manifest_template(agent: AgentSpec, example: bool) -> str:
    payload = {
        "name": agent.name,
        "description": agent.description,
        "prompt": agent.prompt_path,
        "tools_module": agent.tools_module,
        "keywords": agent.keywords or [agent.name],
        "enabled": agent.enabled,
        "example": example,
    }
    return _json_text(payload)



def _agent_prompt_template(agent: AgentSpec, example: bool) -> str:
    header = "# Example prompt" if example else "# Agent prompt"
    return dedent(
        f"""
        {header}: {agent.name}

        You are the {agent.name} agent.
        - Focus: {agent.description}
        - Goal: Handle {agent.name} requests clearly and quickly.
        - Tone: concise, practical, and direct.
        """
    ).lstrip()



def _agent_tools_template(agent: AgentSpec, example: bool) -> str:
    if agent.name == "support" and example:
        return dedent(
            '''
            from __future__ import annotations


            def lookup_order_status(order_id: str) -> str:
                """Example support tool for checking an order status."""

                return f"Order {order_id} is currently in progress."


            def escalate_ticket(ticket_id: str, priority: str = "normal") -> str:
                """Example support tool for escalating a ticket."""

                return f"Ticket {ticket_id} escalated with {priority} priority."
            '''
        ).lstrip()

    if agent.name == "sales" and example:
        return dedent(
            '''
            from __future__ import annotations


            def get_price(plan_name: str) -> str:
                """Example sales tool for quoting a plan."""

                return f"Price requested for {plan_name}."


            def compare_plans(left: str, right: str) -> str:
                """Example sales tool for comparing plans."""

                return f"Compared {left} against {right}."
            '''
        ).lstrip()

    function_name = f"handle_{agent.name}_request"
    return dedent(
        f'''
        from __future__ import annotations


        def {function_name}(message: str) -> str:
            """Placeholder tool for the {agent.name} agent."""

            return f"{agent.name} received: {{message}}"
        '''
    ).lstrip()



def _orchestrator_prompt_template() -> str:
    return dedent(
        """
        # Example prompt: orchestrator

        You are the orchestrator agent.
        - Route the user to the right agent.
        - Keep responses concise and actionable.
        - Use the fast router when the request is obvious.
        """
    ).lstrip()



def _orchestrator_config_template(spec: ProjectSpec) -> str:
    payload = {
        "enabled": spec.routing_mode in {"orchestrator", "both"},
        "provider": spec.orchestrator_provider,
        "prompt": "orchestrator/prompt.md",
        "config": "orchestrator/orchestrator.json",
    }
    return _json_text(payload)



def _fast_router_json_template_from_agents(agents: list[AgentSpec]) -> str:
    rules: dict[str, str] = {}
    for agent in agents:
        if not agent.enabled:
            continue
        for keyword in agent.keywords or [agent.name]:
            keyword_text = str(keyword).strip().lower()
            if keyword_text:
                rules[keyword_text] = agent.name
    return _json_text({"rules": rules})


def _fast_router_json_template(manifest: dict[str, Any]) -> str:
    rules = _routing_rules_from_manifest(manifest)
    return _json_text({"rules": rules})



def _fast_router_py_template() -> str:
    return dedent(
        """
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
        """
    ).lstrip()



def _provider_template(default_provider: str) -> str:
    return dedent(
        f"""
        from __future__ import annotations

        import os

        from gentis_ai.llm import (
            AzureOpenAILLM,
            BedrockLLM,
            GeminiLLM,
            MockLLM,
            OllamaLLM,
            OpenAICompatibleLLM,
            VLLMLLM,
        )

        DEFAULT_PROVIDER = {default_provider!r}


        def build_llm(provider_name: str = DEFAULT_PROVIDER):
            provider_name = (provider_name or DEFAULT_PROVIDER).lower()

            if provider_name == "azure":
                return AzureOpenAILLM(
                    model_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
                    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                    temperature=0.2,
                )

            if provider_name == "gemini":
                return GeminiLLM(
                    api_key=os.getenv("GOOGLE_API_KEY"),
                    model_name=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite"),
                )

            if provider_name == "openai":
                return OpenAICompatibleLLM(
                    model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                    api_key=os.getenv("OPENAI_API_KEY"),
                    base_url=os.getenv("OPENAI_BASE_URL"),
                    temperature=0.2,
                )

            if provider_name == "ollama":
                return OllamaLLM(
                    model_name=os.getenv("OLLAMA_MODEL", "llama3.1"),
                    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
                    api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
                    temperature=0.2,
                )

            if provider_name == "bedrock":
                return BedrockLLM(
                    model_name=os.getenv("AWS_BEDROCK_MODEL_ID", "us.amazon.nova-lite-v1:0"),
                    region_name=os.getenv("AWS_REGION"),
                    temperature=0.2,
                    max_tokens=512,
                )

            if provider_name == "vllm":
                return VLLMLLM(
                    model_name=os.getenv("VLLM_MODEL", "facebook/opt-125m"),
                    base_url=os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1"),
                    api_key=os.getenv("VLLM_API_KEY", "EMPTY"),
                    temperature=0.2,
                )

            if provider_name == "mock":
                return MockLLM()

            raise ValueError(f"Unsupported provider: {{provider_name}}")
        """
    ).lstrip()



def _app_template() -> str:
    return dedent(
        """
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
        """
    ).lstrip()



def _dockerfile_template() -> str:
    return dedent(
        """
        FROM python:3.12-slim
        WORKDIR /app
        COPY requirements.txt .
        RUN pip install --no-cache-dir -r requirements.txt
        COPY . .
        CMD ["python", "app.py"]
        """
    ).lstrip()



def _requirements_template(default_provider: str) -> str:
    extras = {
        "azure": "openai",
        "gemini": "gemini",
        "openai": "openai",
        "ollama": "ollama",
        "bedrock": "bedrock",
        "vllm": "vllm",
    }
    return f"gentis-ai[{extras.get(default_provider, 'openai')}]\n"



def _env_template(default_provider: str, orchestrator_provider: str | None) -> str:
    lines = ["# Copy this file to .env and fill in the values you need."]
    if default_provider == "azure":
        lines.extend(
            [
                "AZURE_OPENAI_API_KEY=",
                "AZURE_OPENAI_ENDPOINT=",
                "AZURE_OPENAI_DEPLOYMENT=",
            ]
        )
    elif default_provider == "gemini":
        lines.extend(
            [
                "GOOGLE_API_KEY=",
                "GEMINI_MODEL=gemini-2.0-flash-lite",
            ]
        )
    elif default_provider == "openai":
        lines.extend(
            [
                "OPENAI_API_KEY=",
                "OPENAI_BASE_URL=",
                "OPENAI_MODEL=gpt-4o-mini",
            ]
        )
    elif default_provider == "ollama":
        lines.extend(
            [
                "OLLAMA_BASE_URL=http://localhost:11434/v1",
                "OLLAMA_MODEL=llama3.1",
                "OLLAMA_API_KEY=ollama",
            ]
        )
    elif default_provider == "bedrock":
        lines.extend(
            [
                "AWS_REGION=",
                "AWS_BEDROCK_MODEL_ID=us.amazon.nova-lite-v1:0",
            ]
        )
    elif default_provider == "vllm":
        lines.extend(
            [
                "VLLM_BASE_URL=http://localhost:8000/v1",
                "VLLM_MODEL=facebook/opt-125m",
                "VLLM_API_KEY=EMPTY",
            ]
        )

    if orchestrator_provider and orchestrator_provider != default_provider:
        lines.append(f"ORCHESTRATOR_PROVIDER={orchestrator_provider}")
    return "\n".join(lines) + "\n"



def _project_test_template() -> str:
    return dedent(
        """
        from gentis_ai.llm import MockLLM

        from app import build_flow


        def test_answer_routes_support_requests():
            flow = build_flow(
                MockLLM(
                    routing_rules={"help": "support", "price": "sales"},
                    responses={"help": "support response", "price": "sales response"},
                )
            )

            response = flow.process_turn("I need help with login.", session_id="multi-agent-test")

            assert response.agent_name == "support"
            assert "support" in response.content.lower()
        """
    ).lstrip()



def _orchestrator_prompt_config() -> dict[str, Any]:
    return {
        "enabled": True,
        "description": "Routes requests to the right agent.",
        "provider": None,
        "prompt": "orchestrator/prompt.md",
        "config": "orchestrator/orchestrator.json",
    }



def _routing_rules_from_manifest(manifest: dict[str, Any]) -> dict[str, str]:
    rules: dict[str, str] = {}
    for agent_entry in manifest.get("agents", []):
        if not isinstance(agent_entry, dict):
            continue
        if not agent_entry.get("enabled", True):
            continue
        agent_name = str(agent_entry.get("name", "")).strip()
        if not agent_name:
            continue
        agent_config = _load_agent_manifest_from_entry(agent_entry)
        keywords = agent_config.get("keywords", [])
        if not keywords:
            keywords = [agent_name]
        for keyword in keywords:
            keyword_text = str(keyword).strip().lower()
            if keyword_text:
                rules[keyword_text] = agent_name
    return rules



def _load_agent_manifest_from_entry(agent_entry: dict[str, Any]) -> dict[str, Any]:
    path = agent_entry.get("path")
    if not isinstance(path, str):
        return {}
    manifest_path = Path(path) / "agent.json"
    if not manifest_path.exists():
        return {}
    return json.loads(manifest_path.read_text(encoding="utf-8"))



def _json_text(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"



def _project_files_from_agent(agent: AgentSpec) -> dict[str, str]:
    return _agent_files(agent, example=False)



def _write_project_output(project_root: Path, files: dict[str, str], overwrite: bool = False) -> dict[str, list[str]]:
    created, skipped = _write_files(project_root, files, overwrite=overwrite)
    return {"created": created, "skipped": skipped}



def _build_agents_from_manifest(manifest: dict[str, Any]) -> list[Expert]:
    project_root = Path(".").resolve()
    experts: list[Expert] = []
    for agent_entry in manifest.get("agents", []):
        if not isinstance(agent_entry, dict):
            continue
        if not agent_entry.get("enabled", True):
            continue
        agent_config = _load_agent_manifest_from_entry(agent_entry)
        if not agent_config:
            continue
        experts.append(
            Expert(
                name=str(agent_config.get("name", "agent")),
                description=str(agent_config.get("description", "")),
                system_prompt=_load_text(project_root / str(agent_config.get("prompt", ""))),
                tools=_load_tools_module(agent_config.get("tools_module")),
            )
        )
    return experts



def _load_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")



def _load_tools_module(module_name: Any) -> list[object]:
    if not isinstance(module_name, str) or not module_name:
        return []
    module = importlib.import_module(module_name)
    tools: list[object] = []
    for name in dir(module):
        if name.startswith("_"):
            continue
        value = getattr(module, name)
        if callable(value):
            tools.append(value)
    return tools



def _project_output_paths() -> list[str]:
    return [
        PROJECT_MANIFEST_FILE,
        "routing/fast_router.json",
        "routing/fast_router.py",
        "app.py",
    ]



def _default_agent_keywords(name: str) -> list[str]:
    return [name]



def _build_sample_agent(name: str, example: bool = True) -> AgentSpec:
    descriptions = {
        "support": "Example agent for technical support and troubleshooting.",
        "sales": "Example agent for pricing and buying questions.",
    }
    return AgentSpec(
        name=name,
        description=descriptions.get(name, f"Example agent for {name} requests."),
        keywords=["help", "issue", "bug", "login"] if name == "support" else ["price", "pricing", "buy", "plan"] if name == "sales" else _default_agent_keywords(name),
        example=example,
    )



def _build_new_agent(name: str, description: str | None, keywords: list[str]) -> AgentSpec:
    return AgentSpec(
        name=name,
        description=description or f"Handles {name} requests.",
        keywords=keywords or _default_agent_keywords(name),
        example=False,
    )



def _write_agent_bundle(root: Path, agent: AgentSpec, overwrite: bool = False) -> list[str]:
    created: list[str] = []
    for relative_path, content in _agent_files(agent, example=agent.example).items():
        if _write_text(root / relative_path, content, overwrite=overwrite):
            created.append(relative_path)
    return created



def _build_project_update_files(manifest: dict[str, Any]) -> dict[str, str]:
    return {
        PROJECT_MANIFEST_FILE: _json_text(manifest),
        "routing/fast_router.json": _fast_router_json_template(manifest),
        "routing/fast_router.py": _fast_router_py_template(),
        "app.py": _app_template(),
    }



def _apply_agent_to_project(
    root: Path,
    manifest: dict[str, Any],
    agent: AgentSpec,
    overwrite: bool = False,
) -> tuple[list[str], list[str], dict[str, Any]]:
    manifest = _apply_agent_to_manifest(manifest, agent)
    _save_json(root / PROJECT_MANIFEST_FILE, manifest)
    created = _write_agent_bundle(root, agent, overwrite=overwrite)
    updated_files = _build_project_update_files(manifest)
    _write_files(root, updated_files, overwrite=True)
    return created, _project_output_paths(), manifest



def _project_files_for_new_project(spec: ProjectSpec) -> dict[str, str]:
    manifest = _build_project_manifest(spec, _initial_agents())
    return _project_files(spec, manifest)



def _initial_manifest_for_project(spec: ProjectSpec) -> dict[str, Any]:
    return _build_project_manifest(spec, _initial_agents())



def _resolve_orchestrator_provider_choice(
    default_provider: str,
    routing_mode: str,
    args: argparse.Namespace | None = None,
) -> str | None:
    if routing_mode == "fast_router":
        return None
    if args is not None and getattr(args, "orchestrator_provider", None):
        return args.orchestrator_provider
    same_provider = _prompt_yes_no(
        "Use same provider for orchestrator as default provider?",
        default=True,
    )
    if same_provider:
        return default_provider
    return _resolve_provider_from_prompt()



def _write_default_project_files(root: Path, spec: ProjectSpec) -> tuple[list[str], list[str]]:
    manifest = _initial_manifest_for_project(spec)
    files = _project_files(spec, manifest)
    return _write_files(root, files, overwrite=False)



def _resolve_provider_choices(args: argparse.Namespace) -> str | None:
    explicit = [name for name in PROVIDER_SHORTCUTS if getattr(args, name, False)]
    if args.provider and explicit:
        raise SystemExit("Use either --provider or one provider shortcut, not both.")
    if args.provider:
        return args.provider
    if len(explicit) > 1:
        raise SystemExit("Choose only one provider shortcut.")
    if explicit:
        return PROVIDER_SHORTCUTS[explicit[0]]
    return None



def _routing_rules_from_agent_files(root: Path, manifest: dict[str, Any]) -> dict[str, str]:
    rules: dict[str, str] = {}
    for agent_entry in manifest.get("agents", []):
        if not isinstance(agent_entry, dict):
            continue
        if not agent_entry.get("enabled", True):
            continue
        agent_path = root / str(agent_entry.get("path", "")) / "agent.json"
        if not agent_path.exists():
            continue
        agent_config = json.loads(agent_path.read_text(encoding="utf-8"))
        agent_name = str(agent_config.get("name", "")).strip()
        for keyword in agent_config.get("keywords", []) or [agent_name]:
            keyword_text = str(keyword).strip().lower()
            if keyword_text and agent_name:
                rules[keyword_text] = agent_name
    return rules



def _refresh_fast_router_artifacts(root: Path, manifest: dict[str, Any]) -> None:
    routing = manifest.get("routing", {})
    fast_router = routing.get("fast_router", {})
    if not fast_router.get("enabled"):
        return
    rules = _routing_rules_from_agent_files(root, manifest)
    _save_json(root / "routing/fast_router.json", {"rules": rules})
    _write_text(root / "routing/fast_router.py", _fast_router_py_template(), overwrite=True)



def _refresh_app(root: Path, manifest: dict[str, Any]) -> None:
    _write_text(root / "app.py", _app_template(), overwrite=True)



def _refresh_manifest(root: Path, manifest: dict[str, Any]) -> None:
    _save_json(root / PROJECT_MANIFEST_FILE, manifest)



def _load_project_manifest(root: Path) -> dict[str, Any] | None:
    manifest_path = root / PROJECT_MANIFEST_FILE
    if not manifest_path.exists():
        return None
    return json.loads(manifest_path.read_text(encoding="utf-8"))



def _agent_exists(manifest: dict[str, Any], name: str) -> bool:
    for agent_entry in manifest.get("agents", []):
        if isinstance(agent_entry, dict) and str(agent_entry.get("name")) == name:
            return True
    return False



def _merge_agent_files(root: Path, agent: AgentSpec, overwrite: bool) -> list[str]:
    files = _agent_files(agent, example=False)
    created, _ = _write_files(root, files, overwrite=overwrite)
    return created



def _create_agent_output(agent: AgentSpec, created: list[str], updated: list[str], root: Path) -> None:
    output = {
        "project": str(root),
        "agent_added": agent.name,
        "created": created,
        "updated": updated,
    }
    print(json.dumps(output, indent=2))



def _project_files_from_project_config(root: Path, manifest: dict[str, Any]) -> dict[str, str]:
    return {
        "app.py": _app_template(),
        "routing/fast_router.py": _fast_router_py_template(),
        "routing/fast_router.json": _fast_router_json_template(manifest),
    }



def _agent_files_from_manifest_entry(root: Path, agent_entry: dict[str, Any]) -> dict[str, str]:
    agent = AgentSpec(
        name=str(agent_entry.get("name", "agent")),
        description=str(agent_entry.get("description", f"Handles {agent_entry.get('name', 'agent')} requests.")),
        keywords=[str(keyword) for keyword in agent_entry.get("keywords", [])],
        example=bool(agent_entry.get("example", False)),
        enabled=bool(agent_entry.get("enabled", True)),
    )
    return _agent_files(agent, example=agent.example)



def _project_files_root(root: Path, spec: ProjectSpec, manifest: dict[str, Any]) -> dict[str, str]:
    return _project_files(spec, manifest)



def _project_file_content_for_agent(agent: AgentSpec) -> dict[str, str]:
    return _agent_files(agent, example=agent.example)



def _project_add_agent(root: Path, manifest: dict[str, Any], agent: AgentSpec, overwrite: bool) -> None:
    created = _write_agent_bundle(root, agent, overwrite=overwrite)
    _refresh_manifest(root, manifest)
    _refresh_fast_router_artifacts(root, manifest)
    _refresh_app(root, manifest)
    _create_agent_output(
        agent,
        created,
        [PROJECT_MANIFEST_FILE, "routing/fast_router.json", "routing/fast_router.py", "app.py"],
        root,
    )



def _build_project_files_for_root(spec: ProjectSpec) -> dict[str, str]:
    return _project_files(spec, _build_project_manifest(spec, _initial_agents()))



def _project_template_name(name: str) -> str:
    return name.replace("-", "_")



def _project_agent_list(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    agents = manifest.get("agents", [])
    return [agent for agent in agents if isinstance(agent, dict)]



def _project_agent_manifest_path(root: Path, name: str) -> Path:
    return root / f"agents/{name}/agent.json"



def _project_agent_prompt_path(root: Path, name: str) -> Path:
    return root / f"agents/{name}/prompt.md"



def _project_agent_tools_path(root: Path, name: str) -> Path:
    return root / f"agents/{name}/tools.py"



def _project_agent_folder(root: Path, name: str) -> Path:
    return root / f"agents/{name}"



def _agent_prompt_exists(root: Path, name: str) -> bool:
    return _project_agent_prompt_path(root, name).exists()



def _create_or_update_agent_bundle(root: Path, agent: AgentSpec, overwrite: bool = False) -> list[str]:
    return _merge_agent_files(root, agent, overwrite)



def _manifest_to_json(manifest: dict[str, Any]) -> str:
    return _json_text(manifest)



def _create_project_and_print(root: Path, files: dict[str, str], overwrite: bool = False) -> None:
    created, skipped = _write_files(root, files, overwrite=overwrite)
    print(
        json.dumps(
            {
                "project": str(root),
                "created": created,
                "skipped": skipped,
            },
            indent=2,
        )
    )



def _project_files_for_agent_add(root: Path, manifest: dict[str, Any], agent: AgentSpec) -> dict[str, str]:
    files = _agent_files(agent, example=False)
    files.update(
        {
            PROJECT_MANIFEST_FILE: _json_text(manifest),
            "routing/fast_router.json": _fast_router_json_template(manifest),
            "routing/fast_router.py": _fast_router_py_template(),
            "app.py": _app_template(),
        }
    )
    return files



def _project_root_from_name(name: str) -> Path:
    return Path(name).expanduser().resolve()



def _select_orchestrator_provider(default_provider: str, routing_mode: str) -> str | None:
    if routing_mode == "fast_router":
        return None
    same_provider = _prompt_yes_no(
        "Use same provider for orchestrator as default provider?",
        default=True,
    )
    if same_provider:
        return default_provider
    return _resolve_provider_from_prompt()



def _manifest_path(root: Path) -> Path:
    return root / PROJECT_MANIFEST_FILE



def _load_manifest(root: Path) -> dict[str, Any] | None:
    return _load_project_manifest(root)



def _sample_manifest_output(manifest: dict[str, Any]) -> str:
    return _json_text(manifest)



def _merge_manifest_agents(manifest: dict[str, Any], agent: AgentSpec) -> dict[str, Any]:
    return _apply_agent_to_manifest(manifest, agent)



def _routing_json_path() -> str:
    return "routing/fast_router.json"



def _routing_py_path() -> str:
    return "routing/fast_router.py"



def _app_py_path() -> str:
    return "app.py"



def _project_test_path() -> str:
    return "tests/test_routing.py"



def _project_files_for_existing_manifest(manifest: dict[str, Any]) -> dict[str, str]:
    return _build_project_update_files(manifest)



def _agent_json_path(agent: AgentSpec) -> str:
    return agent.agent_path



def _agent_prompt_path(agent: AgentSpec) -> str:
    return agent.prompt_path



def _agent_tools_path(agent: AgentSpec) -> str:
    return agent.tools_path



def _agent_tools_module(agent: AgentSpec) -> str:
    return agent.tools_module



def _add_agent_to_project(root: Path, manifest: dict[str, Any], agent: AgentSpec, overwrite: bool) -> None:
    agent_files = _agent_files(agent, example=False)
    _write_files(root, agent_files, overwrite=overwrite)
    manifest = _apply_agent_to_manifest(manifest, agent)
    _save_json(root / PROJECT_MANIFEST_FILE, manifest)
    _save_json(root / "routing/fast_router.json", {"rules": _routing_rules_from_manifest(manifest)})
    _write_text(root / "routing/fast_router.py", _fast_router_py_template(), overwrite=True)
    _write_text(root / "app.py", _app_template(), overwrite=True)
    print(
        json.dumps(
            {
                "project": str(root),
                "agent_added": agent.name,
                "created": list(agent_files.keys()),
                "updated": [PROJECT_MANIFEST_FILE, "routing/fast_router.json", "routing/fast_router.py", "app.py"],
            },
            indent=2,
        )
    )



def _project_files_for_new_agent(agent: AgentSpec) -> dict[str, str]:
    return _agent_files(agent, example=False)



def _manifest_default_provider(manifest: dict[str, Any]) -> str:
    return str(manifest.get("default_provider", "azure"))



def _manifest_routing_mode(manifest: dict[str, Any]) -> str:
    routing = manifest.get("routing", {})
    return str(routing.get("mode", "both"))



def _manifest_first_encounter(manifest: dict[str, Any]) -> str:
    routing = manifest.get("routing", {})
    return str(routing.get("first_encounter", "fast_router"))



def _manifest_orchestrator_provider(manifest: dict[str, Any]) -> str | None:
    routing = manifest.get("routing", {})
    orchestrator = routing.get("orchestrator", {})
    provider = orchestrator.get("provider")
    return provider if isinstance(provider, str) else None



def _project_files_for_new_project(spec: ProjectSpec) -> dict[str, str]:
    return _project_files(spec, _build_project_manifest(spec, _initial_agents()))



def _example_agent_files() -> dict[str, str]:
    files: dict[str, str] = {}
    for agent in _initial_agents():
        files.update(_agent_files(agent, example=True))
    return files



def _project_static_files(spec: ProjectSpec) -> dict[str, str]:
    return {
        "app.py": _app_template(),
        "provider.py": _provider_template(spec.default_provider),
        "requirements.txt": _requirements_template(spec.default_provider),
        "Dockerfile": _dockerfile_template(),
        ".env.example": _env_template(spec.default_provider, spec.orchestrator_provider),
        "tests/test_routing.py": _project_test_template(),
        "orchestrator/prompt.md": _orchestrator_prompt_template(),
        "orchestrator/orchestrator.json": _orchestrator_config_template(spec),
        "routing/fast_router.json": _fast_router_json_template(_build_project_manifest(spec, _initial_agents())),
        "routing/fast_router.py": _fast_router_py_template(),
    }



def _project_agent_files() -> dict[str, str]:
    files: dict[str, str] = {}
    for agent in _initial_agents():
        files.update(_agent_files(agent, example=True))
    return files



def _project_files_from_spec(spec: ProjectSpec) -> dict[str, str]:
    manifest = _build_project_manifest(spec, _initial_agents())
    files = _project_static_files(spec)
    files.update(_project_agent_files())
    files[PROJECT_MANIFEST_FILE] = _json_text(manifest)
    return files



def _build_project_files(spec: ProjectSpec) -> dict[str, str]:
    return _project_files_from_spec(spec)



def _write_project(spec: ProjectSpec, overwrite: bool = False) -> dict[str, list[str]]:
    root = _project_root_from_name(spec.name)
    root.mkdir(parents=True, exist_ok=True)
    files = _project_files_from_spec(spec)
    created, skipped = _write_files(root, files, overwrite=overwrite)
    return {"created": created, "skipped": skipped}



def _ensure_project_manifest(root: Path, spec: ProjectSpec) -> dict[str, Any]:
    manifest = _build_project_manifest(spec, _initial_agents())
    _save_json(root / PROJECT_MANIFEST_FILE, manifest)
    return manifest



def _create_project_files(root: Path, spec: ProjectSpec, overwrite: bool) -> tuple[list[str], list[str]]:
    manifest = _build_project_manifest(spec, _initial_agents())
    files = _project_files(spec, manifest)
    return _write_files(root, files, overwrite=overwrite)



def _project_files_from_manifest_spec(spec: ProjectSpec) -> dict[str, str]:
    return _project_files(spec, _build_project_manifest(spec, _initial_agents()))



def _project_manifest_payload(spec: ProjectSpec) -> dict[str, Any]:
    return _build_project_manifest(spec, _initial_agents())



def _build_project_output(spec: ProjectSpec, root: Path, overwrite: bool) -> dict[str, list[str]]:
    files = _project_files(spec, _build_project_manifest(spec, _initial_agents()))
    return {"created": _write_files(root, files, overwrite=overwrite)[0], "skipped": _write_files(root, files, overwrite=overwrite)[1]}



def _project_files_for_agent_bundle(agent: AgentSpec) -> dict[str, str]:
    return _agent_files(agent, example=agent.example)



def _update_project(root: Path, manifest: dict[str, Any]) -> None:
    _save_json(root / PROJECT_MANIFEST_FILE, manifest)



def _project_files_for_manifest(manifest: dict[str, Any]) -> dict[str, str]:
    return {
        PROJECT_MANIFEST_FILE: _json_text(manifest),
        "routing/fast_router.json": _fast_router_json_template(manifest),
        "routing/fast_router.py": _fast_router_py_template(),
        "app.py": _app_template(),
    }



def _project_files_for_full_project(spec: ProjectSpec) -> dict[str, str]:
    manifest = _build_project_manifest(spec, _initial_agents())
    files = _project_files_for_manifest(manifest)
    files.update(_project_agent_files())
    files.update(
        {
            "provider.py": _provider_template(spec.default_provider),
            "requirements.txt": _requirements_template(spec.default_provider),
            "Dockerfile": _dockerfile_template(),
            ".env.example": _env_template(spec.default_provider, spec.orchestrator_provider),
            "tests/test_routing.py": _project_test_template(),
            "orchestrator/prompt.md": _orchestrator_prompt_template(),
            "orchestrator/orchestrator.json": _orchestrator_config_template(spec),
        }
    )
    return files



def _project_files_for_new_schema(spec: ProjectSpec) -> dict[str, str]:
    return _project_files_for_full_project(spec)



def _project_output_data(root: Path, created: list[str], skipped: list[str]) -> dict[str, Any]:
    return {"project": str(root), "created": created, "skipped": skipped}



def _project_output_print(root: Path, created: list[str], skipped: list[str]) -> None:
    print(json.dumps(_project_output_data(root, created, skipped), indent=2))



def _project_create(root: Path, spec: ProjectSpec, overwrite: bool = False) -> None:
    files = _project_files_for_full_project(spec)
    created, skipped = _write_files(root, files, overwrite=overwrite)
    _project_output_print(root, created, skipped)



def _project_agent_rules(manifest: dict[str, Any]) -> dict[str, str]:
    return _routing_rules_from_manifest(manifest)



def _project_agent_files_for_manifest_entry(agent_entry: dict[str, Any]) -> dict[str, str]:
    agent = AgentSpec(
        name=str(agent_entry.get("name", "agent")),
        description=str(agent_entry.get("description", "")),
        keywords=[str(keyword) for keyword in agent_entry.get("keywords", [])],
        example=bool(agent_entry.get("example", False)),
        enabled=bool(agent_entry.get("enabled", True)),
    )
    return _agent_files(agent, example=agent.example)



def _project_agent_entry(name: str, description: str | None, keywords: list[str]) -> AgentSpec:
    return _build_new_agent(name, description, keywords)



def _project_manifest_load(root: Path) -> dict[str, Any] | None:
    return _load_project_manifest(root)



def _project_manifest_save(root: Path, manifest: dict[str, Any]) -> None:
    _save_json(root / PROJECT_MANIFEST_FILE, manifest)



def _project_manifest_update_agents(manifest: dict[str, Any], agent: AgentSpec) -> dict[str, Any]:
    return _apply_agent_to_manifest(manifest, agent)



def _project_agent_json(agent: AgentSpec) -> str:
    return _agent_manifest_template(agent, example=agent.example)



def _project_agent_prompt(agent: AgentSpec) -> str:
    return _agent_prompt_template(agent, example=agent.example)



def _project_agent_tools(agent: AgentSpec) -> str:
    return _agent_tools_template(agent, example=agent.example)



def _project_agent_bundle(agent: AgentSpec) -> dict[str, str]:
    return _agent_files(agent, example=agent.example)



def _project_agent_root(root: Path, agent_name: str) -> Path:
    return root / "agents" / agent_name



def _project_orchestrator_root(root: Path) -> Path:
    return root / "orchestrator"



def _project_routing_root(root: Path) -> Path:
    return root / "routing"



def _project_tests_root(root: Path) -> Path:
    return root / "tests"



def _build_agent_experts(project_root: Path, manifest: dict[str, Any]) -> list[Expert]:
    experts: list[Expert] = []
    for agent_entry in manifest.get("agents", []):
        if not isinstance(agent_entry, dict):
            continue
        if not agent_entry.get("enabled", True):
            continue
        agent_path = project_root / str(agent_entry.get("path", "")) / "agent.json"
        if not agent_path.exists():
            continue
        agent_config = json.loads(agent_path.read_text(encoding="utf-8"))
        tools = _load_tools_module(agent_config.get("tools_module"))
        prompt = _load_text(project_root / str(agent_config.get("prompt", "")))
        experts.append(
            Expert(
                name=str(agent_config.get("name", "agent")),
                description=str(agent_config.get("description", "")),
                system_prompt=prompt,
                tools=tools,
            )
        )
    return experts



def _build_orchestrator_expert(project_root: Path, manifest: dict[str, Any]) -> Expert | None:
    routing = manifest.get("routing", {})
    orchestrator_config = routing.get("orchestrator", {})
    if not orchestrator_config.get("enabled"):
        return None
    config_path = project_root / str(orchestrator_config.get("config", "orchestrator/orchestrator.json"))
    orchestrator_data = _load_json(config_path)
    prompt_path = str(orchestrator_data.get("prompt", "orchestrator/prompt.md"))
    return Expert(
        name="orchestrator",
        description=str(orchestrator_data.get("description", "Routes requests to the right agent.")),
        system_prompt=_load_text(project_root / prompt_path),
    )



def _project_router_rules(project_root: Path, manifest: dict[str, Any]) -> dict[str, str]:
    routing = manifest.get("routing", {})
    fast_router = routing.get("fast_router", {})
    if not fast_router.get("enabled"):
        return {}
    config_path = project_root / str(fast_router.get("config", "routing/fast_router.json"))
    data = _load_json(config_path)
    rules = data.get("rules", {}) if isinstance(data, dict) else {}
    return {str(keyword).lower(): str(agent) for keyword, agent in rules.items()}



def _project_build_router(project_root: Path, manifest: dict[str, Any], llm=None) -> Router:
    routing_mode = str(manifest.get("routing", {}).get("mode", "both"))
    experts: list[Expert] = []
    orchestrator = _build_orchestrator_expert(project_root, manifest)
    if orchestrator is not None and routing_mode in {"orchestrator", "both"}:
        experts.append(orchestrator)
    experts.extend(_build_agent_experts(project_root, manifest))
    rules = _project_router_rules(project_root, manifest)
    if rules:
        return Router(experts=experts, llm=llm, rules=rules)
    return Router(experts=experts, llm=llm)



def _project_build_flow(project_root: Path, manifest: dict[str, Any], llm=None) -> Flow:
    llm = llm or build_llm(str(manifest.get("default_provider", "azure")))
    return Flow(router=_project_build_router(project_root, manifest, llm), llm=llm)



def _project_app_smoke_test() -> str:
    return dedent(
        """
        from gentis_ai.llm import MockLLM

        from app import build_flow


        def test_answer_routes_support_requests():
            flow = build_flow(
                MockLLM(
                    routing_rules={"help": "support"},
                    responses={"help": "support response"},
                )
            )

            response = flow.process_turn("I need help with login.", session_id="smoke-test")

            assert response.agent_name == "support"
            assert "support" in response.content.lower()
        """
    ).lstrip()



def _project_test_template_content() -> str:
    return _project_app_smoke_test()



def _project_output_files() -> dict[str, str]:
    return {
        "tests/test_routing.py": _project_test_template_content(),
    }



def _project_config_path() -> str:
    return PROJECT_MANIFEST_FILE



def _project_agent_bundle_paths(agent_name: str) -> list[str]:
    return [
        f"agents/{agent_name}/prompt.md",
        f"agents/{agent_name}/tools.py",
        f"agents/{agent_name}/agent.json",
    ]



def _project_update_paths() -> list[str]:
    return [PROJECT_MANIFEST_FILE, "routing/fast_router.json", "routing/fast_router.py", "app.py"]



def _project_agent_name(name: str) -> str:
    return name.strip()



def _project_agent_description(name: str, description: str | None) -> str:
    return description or f"Handles {name} requests."



def _project_agent_keywords(name: str, keywords: list[str]) -> list[str]:
    return keywords or [name]



def _project_agent_spec(name: str, description: str | None, keywords: list[str]) -> AgentSpec:
    return AgentSpec(
        name=_project_agent_name(name),
        description=_project_agent_description(name, description),
        keywords=_project_agent_keywords(name, keywords),
        example=False,
    )



def _project_create_from_cli(name: str, default_provider: str, routing_mode: str, first_encounter: str, orchestrator_provider: str | None, overwrite: bool = False) -> None:
    create_project(name, default_provider, routing_mode, first_encounter, orchestrator_provider, overwrite=overwrite)



def _project_add_from_cli(name: str, project_root: Path | None, description: str | None, keywords: list[str], overwrite: bool = False) -> None:
    add_agent(name, project_root, description, keywords, overwrite=overwrite)



def _project_print_summary(root: Path, created: list[str], skipped: list[str]) -> None:
    print(
        json.dumps(
            {
                "project": str(root),
                "created": created,
                "skipped": skipped,
            },
            indent=2,
        )
    )
