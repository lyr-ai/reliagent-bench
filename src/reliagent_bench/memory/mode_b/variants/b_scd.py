"""B-SCD — bitemporal table, one global rule: the row valid now with the
latest validity start governs; ties by observation time. No authority, no
confidence. History is retained (not needed by the decision tasks)."""
from __future__ import annotations

from datetime import datetime, timezone

from ..schema import Scenario
from .base import Resolved


def _eff(m):
    return m.valid_from or m.observed_at


class BSCD:
    name = "b_scd"

    def resolve(self, scenario: Scenario) -> Resolved:
        now = datetime(2100, 1, 1, tzinfo=timezone.utc)   # "now" is after every observation
        r = Resolved()
        by_slot: dict[str, list] = {}
        for m in scenario.memories:
            by_slot.setdefault(scenario.slot(m), []).append(m)
        for s, ms in by_slot.items():
            valid = [m for m in ms if _eff(m) <= now and (m.valid_to is None or now < m.valid_to)]
            r.governing[s] = max(valid, key=lambda m: (_eff(m), m.observed_at)) if valid else None
        return r
