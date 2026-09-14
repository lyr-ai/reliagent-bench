"""E1 — every fixed global ordering over (source priority, confidence,
recency), each preceded by validity, plus the three single-dimension policies.

A `FixedOrdering` is B-SCD-G with the dimension order as a parameter: the
governing memory per slot is the maximum under the lexicographic key. Ties on
a listed dimension fall through to the next; a full tie is broken by
`observed_at` (recency) — declared in predictions/phase2.json before any run.
`S>C>R` is identical to `b_scd_g`."""
from __future__ import annotations

from datetime import datetime, timezone
from itertools import permutations

from ..schema import SOURCE_PRIORITY, Scenario
from .base import Resolved

_DIM = {
    "S": lambda m: SOURCE_PRIORITY[m.source_type],
    "C": lambda m: m.confidence,
    "R": lambda m: m.valid_from or m.observed_at,     # effective_from, as in b_scd_g
}


def _eff(m):
    return m.valid_from or m.observed_at


class FixedOrdering:
    def __init__(self, order: str):
        self.order = order                      # e.g. "SCR", "S", "C"
        self.name = ">".join(order) if len(order) > 1 else f"{order}_only"

    def resolve(self, scenario: Scenario) -> Resolved:
        now = datetime(2100, 1, 1, tzinfo=timezone.utc)
        r = Resolved()
        by_slot: dict[str, list] = {}
        for m in scenario.memories:
            by_slot.setdefault(scenario.slot(m), []).append(m)
        for s, ms in by_slot.items():
            valid = [m for m in ms if _eff(m) <= now and (m.valid_to is None or now < m.valid_to)]
            key = lambda m: tuple(_DIM[d](m) for d in self.order) + (m.observed_at,)
            r.governing[s] = max(valid, key=key) if valid else None
        return r


def all_orderings() -> list[FixedOrdering]:
    return [FixedOrdering("".join(p)) for p in permutations("SCR")] + [FixedOrdering(d) for d in "SCR"]
