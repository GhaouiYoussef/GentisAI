from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from gentis_ai import Expert, Flow, Router
from gentis_ai.llm import MockLLM
from gentis_ai.project_runner import ProjectRunError, run_local_project
from gentis_ai.scaffolding import (
    TEMPLATE_CHOICES,
    add_agent,
    add_tool,
    create_project,
    init_project,
)
from gentis_ai.demo import DEMO_CHOICES, export_demo, launch_demo
from gentis_ai.onboarding import configure, doctor
from gentis_ai.providers import ConfigurationError, PROVIDER_CHOICES


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="gentis",
        description="Build, extend, and run multi-agent apps.",
        epilog=(
            "Start an editable app: gentis init my-agent\n"
            "Copy a complete demo: gentis demo customer-rescue --export my-demo\n"
            "Inside your project: gentis add agent billing; gentis run --ui"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    new_parser = subcommands.add_parser("new", help="Create a new GentisAI POC.")
    new_parser.add_argument("name")
    new_parser.add_argument(
        "--template",
        choices=TEMPLATE_CHOICES,
        default="basic",
        help="Project template (default: basic).",
    )

    init_parser = subcommands.add_parser(
        "init",
        help="Create agents/, tools/, prompts/, and a ready-to-run Streamlit app.",
    )
    init_parser.add_argument(
        "directory",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Project directory (default: current directory).",
    )
    add_parser = subcommands.add_parser(
        "add", help="Create and register an agent or tool in an initialized project."
    )
    components = add_parser.add_subparsers(dest="component", required=True)
    agent_parser = components.add_parser("agent", help="Add an agent and its prompt.")
    tool_parser = components.add_parser(
        "tool", help="Add a tool and attach it to an agent."
    )
    for component_parser in (agent_parser, tool_parser):
        component_parser.add_argument(
            "name", help="Python name, for example billing or lookup_invoice."
        )
        component_parser.add_argument(
            "--description", help="Describe what this component does."
        )
        component_parser.add_argument(
            "--project",
            type=Path,
            default=None,
            help="Project directory (default: current directory).",
        )
    tool_parser.add_argument(
        "--agent", required=True, help="Agent that will use this tool."
    )

    run_parser = subcommands.add_parser(
        "run", help="Run your generated project, or the built-in mock chat."
    )
    run_parser.add_argument(
        "--ui", action="store_true", help="Open this project's Streamlit application."
    )
    run_parser.add_argument(
        "--port", type=int, default=8501, help="Streamlit port (default: 8501)."
    )
    run_parser.add_argument(
        "--headless", action="store_true", help="Do not open a browser automatically."
    )
    demo_parser = subcommands.add_parser(
        "demo", help="Open a bundled Streamlit demo; no clone needed."
    )
    demo_parser.add_argument(
        "name", choices=DEMO_CHOICES, nargs="?", default="customer-rescue"
    )
    demo_parser.add_argument("--provider", choices=PROVIDER_CHOICES)
    demo_parser.add_argument(
        "--export",
        dest="export_path",
        type=Path,
        metavar="DIRECTORY",
        help="Copy the complete editable demo into a new directory without launching it.",
    )
    demo_parser.add_argument("--port", type=int, default=8501)
    demo_parser.add_argument(
        "--headless", action="store_true", help="Do not open a browser automatically."
    )
    configure_parser = subcommands.add_parser(
        "configure",
        help="Create provider configuration and a secret-free example; preserve existing files.",
    )
    configure_parser.add_argument("--provider", choices=PROVIDER_CHOICES, required=True)
    configure_parser.add_argument("--output", type=Path, default=Path(".env"))
    doctor_parser = subcommands.add_parser(
        "doctor", help="Check local configuration and provider SDK without API calls."
    )
    doctor_parser.add_argument("--provider", choices=PROVIDER_CHOICES)
    subcommands.add_parser("eval", help="Run the offline routing eval.")
    subcommands.add_parser("bench", help="Run a tiny offline latency benchmark.")

    args = parser.parse_args()
    if args.command == "demo" and args.export_path is not None:
        try:
            root = export_demo(args.name, args.export_path)
        except (ValueError, OSError, ConfigurationError) as exc:
            parser.exit(1, f"gentis demo: {exc}\n")
        print(f"Exported {args.name} to {root}")
        print(f'Next:\n  cd "{root}"\n  gentis run')
        print(
            "Edit app.py for the UI and demo_app/ for agents, prompts, tools, and telemetry."
        )
        return
    if args.command in {"demo", "configure", "doctor"}:
        try:
            if args.command == "demo":
                raise SystemExit(
                    launch_demo(
                        args.name,
                        provider=args.provider,
                        port=args.port,
                        headless=args.headless,
                    )
                )
            if args.command == "configure":
                path = configure(args.provider, args.output)
                if path == args.output:
                    print(
                        f"Created {path}. Keep this file private and out of version control."
                    )
                else:
                    print(
                        f"Kept existing {args.output}. No configuration values were changed."
                    )
                print(
                    f"Example: {args.output.with_name(args.output.name + '.example')}"
                )
                print("Next: gentis doctor, then gentis demo (from this directory).")
                if args.output != Path(".env"):
                    print(
                        "Custom output paths are not auto-loaded. Place the file at .env in your project before running."
                    )
            else:
                doctor(args.provider)
        except (ConfigurationError, ImportError) as exc:
            parser.exit(1, f"gentis {args.command}: {exc}\n")
        except OSError:
            parser.exit(
                1,
                f"gentis {args.command}: Could not access the required file or start the process. Check the path and permissions.\n",
            )
        except (EOFError, KeyboardInterrupt):
            parser.exit(1, f"gentis {args.command}: Cancelled.\n")
        return
    if args.command in {"init", "add"}:
        try:
            if args.command == "init":
                root = init_project(args.directory)
                print(f"Created project structure in {root}")
                _print_project_steps(root)
            elif args.component == "agent":
                path = add_agent(
                    args.name, root=args.project, description=args.description
                )
                print(f"Added agent {args.name}: {path}")
                print(
                    "The agent is registered in gentis.json. Edit its prompt in prompts/."
                )
                print("Restart gentis run or gentis run --ui to load your changes.")
            else:
                path = add_tool(
                    args.name,
                    agent=args.agent,
                    root=args.project,
                    description=args.description,
                )
                print(f"Added tool {args.name} for {args.agent}: {path}")
                print(
                    "Edit the tool function, then restart gentis run or gentis run --ui."
                )
        except (ValueError, OSError) as exc:
            parser.exit(1, f"gentis {args.command}: {exc}\n")
    elif args.command == "new":
        try:
            root = create_project(args.name, template=args.template)
        except (ValueError, OSError) as exc:
            parser.exit(1, f"gentis new: {exc}\n")
        print(f"Created {root}")
        if args.template == "streamlit":
            _print_project_steps(root)
        elif args.template in {"support", "azure-support", "gemini-support"}:
            print("Next:")
            print(f"  cd {root}")
            if args.template == "gemini-support":
                print("  Set GOOGLE_API_KEY in this shell")
            print("  gentis run")
            if args.template == "support":
                print(
                    "  Edit app.py to customize experts; gentis configure --provider azure enables a real provider."
                )
    elif args.command == "run":
        try:
            if run_local_project(ui=args.ui, port=args.port, headless=args.headless):
                return
        except ProjectRunError as exc:
            parser.exit(exc.exit_code, f"gentis run: {exc}\n")
        except KeyboardInterrupt:
            parser.exit(130, "gentis run: Stopped.\n")
        run_mock_chat()
    elif args.command == "eval":
        run_eval()
    elif args.command == "bench":
        run_bench()


def _print_project_steps(root: Path) -> None:
    print("Next:")
    print(f'  cd "{root}"')
    print('  gentis add agent billing --description "Handles invoices and refunds"')
    print("  gentis add tool lookup_invoice --agent billing")
    print("  gentis run --ui")
    print(
        'Install the UI dependency if needed: python -m pip install "gentis-ai[demo]"'
    )
    print(
        "Use gentis run for terminal chat. Edit agents/, tools/, and prompts/ to customize."
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
        print(
            json.dumps(
                {"query": query, "expected": expected, "got": response.agent_name}
            )
        )
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
                "p95_ms": sorted_samples[
                    min(len(sorted_samples) - 1, int(len(sorted_samples) * 0.95))
                ],
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


if __name__ == "__main__":
    main()
