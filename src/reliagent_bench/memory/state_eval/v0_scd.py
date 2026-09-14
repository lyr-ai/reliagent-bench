"""V0-scd — bitemporal baseline: what a data engineer would build.

A slowly-changing-dimension (type 2) table with two time axes per row:
*valid time* (``valid_from``/``valid_to``, when the content holds) and
*transaction time* (``observed_at``, when the row was written). Writing a new
row to a slot closes the open row whose validity it supersedes; a query
"as of T" returns the row valid at T with the latest ``valid_from``, ties
broken by transaction time. A row with no declared ``valid_from`` is taken to
hold from its observation, the same fallback every variant uses.

It has no notion of source authority, no confidence guard, and one rule for
every type. It exists so that the temporal category has a baseline that gets
temporal semantics *right*; on that category it is predicted to tie the
system under test (plan §15, §24). Where the system under test still wins
is the claim.

Independent of the system under test at source and import level, like v0.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .schema import MemoryWrite, Query, Scenario, TransitionKind


@dataclass
class _Row:
    content: str
    valid_from: datetime
    valid_to: datetime | None      # None = open
    observed_at: datetime          # transaction time
    seq: int                       # insertion order, for deterministic ties

    def valid_at(self, t: datetime) -> bool:
        return self.valid_from <= t and (self.valid_to is None or t < self.valid_to)


class V0SCDBaseline:
    name = "v0_scd"

    def __init__(self) -> None:
        self._slots: dict[tuple[str, str], list[_Row]] = {}
        self._seq = 0

    def begin(self, scenario: Scenario) -> None:
        self._slots = {}
        self._seq = 0

    def write(self, w: MemoryWrite) -> TransitionKind:
        key = (w.type, w.subject)
        rows = self._slots.setdefault(key, [])
        self._seq += 1
        new = _Row(
            content=w.content,
            valid_from=w.valid_from or w.observed_at,
            valid_to=w.valid_to,
            observed_at=w.observed_at,
            seq=self._seq,
        )
        # SCD-2 close-out: an open row whose validity started before the new
        # row's ends where the new one begins. A row starting later than the
        # new one is untouched — the new row is a historical insert.
        displaced_current = False
        current = self._current(rows)
        for r in rows:
            if r.valid_to is None and r.valid_from < new.valid_from:
                r.valid_to = new.valid_from
                if r is current:
                    displaced_current = True
        # Symmetric: a historical insert ends where the next-later row begins.
        if new.valid_to is None:
            later = [r.valid_from for r in rows if r.valid_from > new.valid_from]
            if later:
                new.valid_to = min(later)
        rows.append(new)
        if not current:
            return "add"
        return "replace" if displaced_current or self._current(rows) is new else "keep"

    def _current(self, rows: list[_Row]) -> _Row | None:
        open_rows = [r for r in rows if r.valid_to is None]
        if not open_rows:
            return None
        return max(open_rows, key=lambda r: (r.valid_from, r.observed_at, r.seq))

    def query(self, q: Query) -> str | None:
        rows = self._slots.get((q.type, q.subject), [])
        if q.as_of is None:
            row = self._current(rows)
            return row.content if row else None
        valid = [r for r in rows if r.valid_at(q.as_of)]
        if not valid:
            return None
        return max(valid, key=lambda r: (r.valid_from, r.observed_at, r.seq)).content
