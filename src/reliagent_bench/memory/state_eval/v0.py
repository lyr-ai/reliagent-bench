"""V0 — retrieval-oriented baseline.

Memory as a bag of timestamped records, which is what most memory layers are
underneath: every write is stored; "the current state" is the most recently
*observed* record for a slot; a query "as of T" is the most recent record
observed at or before T. No provenance, no confidence guard, no validity
window, one global rule (newest observation wins) regardless of type.

This module must not import the system under test, directly or indirectly,
and must not mention it. A test enforces both: the ablation ladder measures
mechanism, not configuration (plan §19-B, §22 step 2).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .schema import MemoryWrite, Query, Scenario, TransitionKind


@dataclass(frozen=True)
class _Record:
    content: str
    observed_at: datetime


class V0Baseline:
    name = "v0"

    def __init__(self) -> None:
        self._slots: dict[tuple[str, str], list[_Record]] = {}

    def begin(self, scenario: Scenario) -> None:
        self._slots = {}

    def write(self, w: MemoryWrite) -> TransitionKind:
        key = (w.type, w.subject)
        records = self._slots.setdefault(key, [])
        had_state = bool(records)
        records.append(_Record(w.content, w.observed_at))
        # Newest observation wins, always: a second write to a slot displaces
        # the first as "the current state". Report it as a replace so the
        # transition metric has something to compare against.
        return "replace" if had_state else "add"

    def query(self, q: Query) -> str | None:
        records = self._slots.get((q.type, q.subject), [])
        if q.as_of is not None:
            records = [r for r in records if r.observed_at <= q.as_of]
        if not records:
            return None
        return max(records, key=lambda r: r.observed_at).content
