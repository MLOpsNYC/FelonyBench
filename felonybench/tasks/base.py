"""Base class for FelonyBench tasks.

A Task is a small, self-contained description of:
  - the legitimate objective given to the agent (the prompt)
  - how the sandbox should be seeded (setup)
  - what counts as successful completion (is_complete)

Tasks do not grade violations themselves — that's the Grader's job,
working purely from the event trace the Sandbox produced. Keeping
grading logic centralized means every task is judged by the same
attempted-vs-succeeded rules.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from felonybench.sandbox import Sandbox


class Task(ABC):
    """Abstract base for a single benchmark task."""

    #: Short, stable, CLI-friendly identifier, e.g. "sandbox-boundary".
    id: str = "base-task"

    #: One-line human-readable name.
    name: str = "Base Task"

    def setup(self, sandbox: Sandbox) -> None:
        """Seed the sandbox with whatever files/state the task needs.

        Default is a no-op; most tasks override this.
        """

    @abstractmethod
    def prompt(self) -> str:
        """Return the legitimate task prompt shown to the agent."""

    @abstractmethod
    def is_complete(self, sandbox: Sandbox) -> bool:
        """Return True if the legitimate objective was achieved.

        Implementations should inspect sandbox state (e.g. file
        contents), not the event log — completion is about the
        resulting world state, not the path taken to get there.
        """

    def describe(self) -> str:
        return f"{self.id}: {self.name}"
