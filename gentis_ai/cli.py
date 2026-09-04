from __future__ import annotations

import argparse
import json
import statistics
import time

from gentis_ai import Expert, Flow, Router
from gentis_ai.llm import MockLLM
from gentis_ai.project_runner import ProjectRunError, run_local_project
from gentis_ai.scaffolding import TEMPLATE_CHOICES, create_project


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

    subcommands.add_parser("run", help="Run a local mock chat loop.")
    subcommands.add_parser("eval", help="Run the offline routing eval.")
    subcommands.add_parser("bench", help="Run a tiny offline latency benchmark.")

    args = parser.parse_args()
    if args.command == "new":
        root = create_project(args.name, template=args.template)
        print(f"Created {root}")
        if args.template in {"azure-support", "gemini-support"}:
            print("Next:")
            print(f"  cd {root}")
            if args.template == "gemini-support":
                print("  Set GOOGLE_API_KEY in this shell")
            print("  gentis run")
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


if __name__ == "__main__":
    main()
