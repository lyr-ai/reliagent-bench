"""B-SCD-G — the bitemporal table plus ONE global merge policy, frozen before
any run (design §7):

    validity first  →  source priority  →  confidence  →  recency

applied identically to every state type. This is the strong baseline: it has
provenance (a fixed source ranking), confidence and validity — everything
except *per-type* semantics. Where it loses to the typed variant, the loss is
attributable to type dependence alone; where it ties, typed resolution bought
nothing."""
from __future__ import annotations

from datetime import datetime, timezone

from ..schema import SOURCE_PRIORITY, Scenario
from .base import Resolved


def _eff(m):
    return m.valid_from or m.observed_at


class BSCDG:
    name = "b_scd_g"

    def resolve(self, scenario: Scenario) -> Resolved:
        now = datetime(2100, 1, 1, tzinfo=timezone.utc)
        r = Resolved()
        by_slot: dict[str, list] = {}
        for m in scenario.memories:
            by_slot.setdefault(scenario.slot(m), []).append(m)
        for s, ms in by_slot.items():
            valid = [m for m in ms if _eff(m) <= now and (m.valid_to is None or now < m.valid_to)]
            r.governing[s] = max(valid, key=lambda m: (SOURCE_PRIORITY[m.source_type], m.confidence, _eff(m), m.observed_at)) if valid else None
        return r
