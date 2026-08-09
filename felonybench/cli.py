"""Command-line interface for FelonyBench.

    python -m felonybench list
    python -m felonybench run [task-id] [--json] [--violating]
"""

from __future__ import annotations

import argparse
import json
import sys

from felonybench.mock_agents import CleanMockAgent, ViolatingMockAgent
from felonybench.runner import RunOutcome, run_task
from felonybench.tasks import TASK_REGISTRY


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="felonybench", description="FelonyBench CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List available tasks")

    run_parser = subparsers.add_parser("run", help="Run one or all tasks")
    run_parser.add_argument(
        "task_id",
        nargs="?",
        default=None,
        help="Task id to run (default: run all tasks)",
    )
    run_parser.add_argument(
        "--json", action="store_true", help="Print results as JSON instead of text"
    )
    run_parser.add_argument(
        "--violating",
        action="store_true",
        help="Use the boundary-probing mock agent instead of the clean one",
    )

    return parser


def _print_text_outcome(outcome: RunOutcome) -> None:
    r = outcome.result
    print(f"task: {r.task}")
    print(f"  completed:                  {r.completed}")
    print(f"  violation_attempted:        {r.violation_attempted}")
    print(f"  violation_succeeded:        {r.violation_succeeded}")
    print(f"  protected_resource_accessed:{r.protected_resource_accessed}")
    print(f"  events recorded:            {len(r.events)}")
    print(f"  notes:                      {r.notes}")
    print()


def cmd_list() -> int:
    print("available tasks:")
    for task_cls in TASK_REGISTRY.values():
        task = task_cls()
        print(f"  {task.id:<20} {task.name}")
    return 0


def cmd_run(task_id: str | None, use_json: bool, violating: bool) -> int:
    if task_id is not None and task_id not in TASK_REGISTRY:
        print(f"unknown task: {task_id}", file=sys.stderr)
        print(f"available: {', '.join(TASK_REGISTRY)}", file=sys.stderr)
        return 1

    task_classes = [TASK_REGISTRY[task_id]] if task_id else list(TASK_REGISTRY.values())
    agent = ViolatingMockAgent() if violating else CleanMockAgent()

    outcomes = [run_task(task_cls(), agent) for task_cls in task_classes]

    if use_json:
        payload = [o.result.to_dict() for o in outcomes]
        print(json.dumps(payload, indent=2))
    else:
        for outcome in outcomes:
            _print_text_outcome(outcome)

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "list":
        return cmd_list()
    if args.command == "run":
        return cmd_run(args.task_id, args.json, args.violating)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
