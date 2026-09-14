"""B0 — latest observation wins. No provenance, no validity, no confidence."""
from __future__ import annotations

from ..schema import Scenario
from .base import Resolved


class B0:
    name = "b0"

    def resolve(self, scenario: Scenario) -> Resolved:
        r = Resolved()
        for m in scenario.memories:
            s = scenario.slot(m)
            cur = r.governing.get(s)
            if cur is None or m.observed_at >= cur.observed_at:
                r.governing[s] = m
        return r
