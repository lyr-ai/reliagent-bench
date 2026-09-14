"""V0-scd-g — the bitemporal table plus one global replacement guard.

Everything ``v0_scd`` has, and one more rule applied identically to every
type: a write whose validity starts no earlier than the current row's may
displace it only if its confidence is no lower. Weaker-and-newer is dropped;
older-effective is filed as history exactly as before. No source authority,
and — the point of this variant — no *per-type* semantics: the guard is the
same for a deadline and a biographical fact.

It exists to answer one question about the typed-resolution category: does
the system under test win there because it *has* a confidence guard, or
because the guard *differs by type*? If this variant closes most of the gap,
the per-type claim is weak (plan §15; README "Pilot-2").

Independent of the system under test at source and import level.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .schema import MemoryWrite, Query, Scenario, TransitionKind


@dataclass
class _Row:
    content: str
    valid_from: datetime
    valid_to: datetime | None
    observed_at: datetime
    confidence: float
    seq: int

    def valid_at(self, t: datetime) -> bool:
        return self.valid_from <= t and (self.valid_to is None or t < self.valid_to)


class V0SCDGuardedBaseline:
    name = "v0_scd_g"

    def __init__(self) -> None:
        self._slots: dict[tuple[str, str], list[_Row]] = {}
        self._seq = 0

    def begin(self, scenario: Scenario) -> None:
        self._slots = {}
        self._seq = 0

    def _current(self, rows: list[_Row]) -> _Row | None:
        open_rows = [r for r in rows if r.valid_to is None]
        if not open_rows:
            return None
        return max(open_rows, key=lambda r: (r.valid_from, r.observed_at, r.seq))

    def write(self, w: MemoryWrite) -> TransitionKind:
        key = (w.type, w.subject)
        rows = self._slots.setdefault(key, [])
        effective = w.valid_from or w.observed_at
        current = self._current(rows)

        # The one global guard: a write that would become current must not be
        # less confident than the row it displaces. Historical inserts are not
        # subject to it — they do not change the current state.
        if current is not None and effective >= current.valid_from and w.confidence < current.confidence:
            return "ignore"

        self._seq += 1
        new = _Row(w.content, effective, w.valid_to, w.observed_at, w.confidence, self._seq)
        displaced_current = False
        for r in rows:
            if r.valid_to is None and r.valid_from < new.valid_from:
                r.valid_to = new.valid_from
                if r is current:
                    displaced_current = True
        if new.valid_to is None:
            later = [r.valid_from for r in rows if r.valid_from > new.valid_from]
            if later:
                new.valid_to = min(later)
        rows.append(new)
        if current is None:
            return "add"
        return "replace" if displaced_current or self._current(rows) is new else "keep"

    def history(self, type: str, subject: str) -> list[str]:
        """Every value the slot has held, in valid-time order."""
        return [r.content for r in sorted(self._slots.get((type, subject), []), key=lambda r: (r.valid_from, r.observed_at, r.seq))]

    def query(self, q: Query) -> str | None:
        rows = self._slots.get((q.type, q.subject), [])
        if q.as_of is None:
            row = self._current(rows)
            return row.content if row else None
        valid = [r for r in rows if r.valid_at(q.as_of)]
        if not valid:
            return None
        return max(valid, key=lambda r: (r.valid_from, r.observed_at, r.seq)).content
