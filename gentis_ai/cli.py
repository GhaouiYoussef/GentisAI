from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from gentis_ai import Expert, Flow, Router
from gentis_ai.llm import MockLLM
from gentis_ai.project_runner import ProjectRunError, run_local_project
from gentis_ai.scaffolding import TEMPLATE_CHOICES, create_project
from gentis_ai.demo import DEMO_CHOICES, launch_demo
from gentis_ai.onboarding import configure, doctor
from gentis_ai.providers import ConfigurationError, PROVIDER_CHOICES


def main() -> None:
    parser = argparse.ArgumentParser(prog="gentis")
    subcommands = parser.add_subparsers(dest="command", required=True)

    new_parser = subcommands.add_parser("new", help="Create a new GentisAI POC.")
    new_parser.add_argument("name")
    new_parser.add_argument(
        "--template",
        choices=TEMPLATE_CHOICES,
        default="basic",
        help="Project template (default: basic).",
    )

    subcommands.add_parser(
        "run", help="Run your generated project, or the built-in mock chat."
    )
    demo_parser = subcommands.add_parser(
        "demo", help="Open a bundled Streamlit demo; no clone needed."
    )
    demo_parser.add_argument(
        "name", choices=DEMO_CHOICES, nargs="?", default="customer-rescue"
    )
    demo_parser.add_argument("--provider", choices=PROVIDER_CHOICES)
    demo_parser.add_argument("--port", type=int, default=8501)
    demo_parser.add_argument(
        "--headless", action="store_true", help="Do not open a browser automatically."
    )
    configure_parser = subcommands.add_parser(
        "configure", help="Create a new provider configuration interactively."
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
                print(
                    f"Created {path}. Keep this file private and out of version control."
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
    if args.command == "new":
        try:
            root = create_project(args.name, template=args.template)
        except (ValueError, OSError) as exc:
            parser.exit(1, f"gentis new: {exc}\n")
        print(f"Created {root}")
        if args.template in {"support", "azure-support", "gemini-support"}:
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
            if run_local_project():
                return
        except ProjectRunError as exc:
            parser.exit(1, f"gentis run: {exc}\n")
        run_mock_chat()
    elif args.command == "eval":
        run_eval()
    elif args.command == "bench":
        run_bench()


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
