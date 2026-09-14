"""B-Oracle — the gold governing state, supplied by hand. Not a memory system:
it bounds how often the agent decides wrongly even with perfect resolution."""
from __future__ import annotations

from ..schema import Scenario
from .base import Resolved


class Oracle:
    name = "oracle"

    def resolve(self, scenario: Scenario) -> Resolved:
        r = Resolved()
        by_id = {m.id: m for m in scenario.memories}
        for slot, mid in scenario.gold_governing.items():
            r.governing[slot] = by_id[mid] if mid else None
        return r


class NoMem:
    """Reference row for repeated-failure tasks and controls: the agent gets
    no memory at all."""
    name = "nomem"

    def resolve(self, scenario: Scenario) -> Resolved:
        return Resolved()
