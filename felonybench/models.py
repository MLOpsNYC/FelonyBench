"""Core data types shared across the benchmark.

Kept intentionally small: a handful of dataclasses, no framework.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Event:
    """A single observable action taken inside a Sandbox.

    Every security-relevant sandbox operation emits one of these. Events
    are the raw material the Grader uses to decide what happened.
    """

    type: str
    action: str
    target: str
    allowed: bool
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "action": self.action,
            "target": self.target,
            "allowed": self.allowed,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class TaskResult:
    """The graded outcome of a single task run."""

    task: str
    completed: bool
    violation_attempted: bool
    violation_succeeded: bool
    protected_resource_accessed: bool
    events: list[Event] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "completed": self.completed,
            "violation_attempted": self.violation_attempted,
            "violation_succeeded": self.violation_succeeded,
            "protected_resource_accessed": self.protected_resource_accessed,
            "notes": self.notes,
            "events": [e.to_dict() for e in self.events],
        }

    def to_json(self, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)
