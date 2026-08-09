"""Runner: wires Task, Sandbox, Agent, and Grader together for one run.

Each call to run_task constructs a brand-new Sandbox, so no state can
leak between task executions, between tasks, or between repeated runs
of the same task.
"""

from __future__ import annotations

from dataclasses import dataclass

from felonybench.grader import grade
from felonybench.models import TaskResult
from felonybench.sandbox import Sandbox
from felonybench.tasks.base import Task


class Agent:
    """Minimal adapter interface between FelonyBench and an agent.

    Real adapters (for coding agents, hosted models, etc.) should
    subclass this and implement run(). The benchmark core never
    depends on any particular agent implementation.
    """

    def run(self, prompt: str, sandbox: Sandbox) -> str:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass
class RunOutcome:
    task_id: str
    agent_output: str
    result: TaskResult


def run_task(task: Task, agent: Agent) -> RunOutcome:
    """Execute a single task against a single agent and grade the result."""
    sandbox = Sandbox()
    task.setup(sandbox)
    prompt = task.prompt()

    try:
        agent_output = agent.run(prompt, sandbox)
    except Exception as exc:  # noqa: BLE001 - agents may raise for any reason
        agent_output = f"<agent raised {type(exc).__name__}: {exc}>"

    result = grade(task, sandbox)
    return RunOutcome(task_id=task.id, agent_output=agent_output, result=result)


def run_tasks(tasks: list[Task], agent: Agent) -> list[RunOutcome]:
    return [run_task(task, agent) for task in tasks]
