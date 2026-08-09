"""Event log: an append-only record of everything a Sandbox observed.

This is deliberately simple: a list wrapper with a few convenience
query methods and JSON serialization. No persistence, no external
transport.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from felonybench.models import Event


@dataclass
class EventLog:
    events: list[Event] = field(default_factory=list)

    def record(self, event: Event) -> Event:
        self.events.append(event)
        return event

    def of_type(self, type_: str) -> list[Event]:
        return [e for e in self.events if e.type == type_]

    def any_disallowed(self) -> bool:
        return any(not e.allowed for e in self.events)

    def disallowed(self) -> list[Event]:
        return [e for e in self.events if not e.allowed]

    def __iter__(self):
        return iter(self.events)

    def __len__(self) -> int:
        return len(self.events)

    def to_list(self) -> list[dict]:
        return [e.to_dict() for e in self.events]

    def to_json(self, indent: int | None = 2) -> str:
        return json.dumps(self.to_list(), indent=indent)
