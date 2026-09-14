"""Scenario schema for Mode A.

A scenario is declarative and system-independent: it says which memory
writes happen, in what order, with what provenance and temporal claims; what
the *intended* semantics of each memory type are (declared here, not inherited
from any implementation — plan §10); and what the resolved state must be for
each query. Gold labels are frozen with the scenario file.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

MECHANISMS = frozenset({
    "authority_veto",
    "effective_from",
    "validity_expired",
    "validity_future",
    "validity_boundary",
    "confidence_guard",
    "type_specific_resolution",
    "none",            # negative control: no mechanism should be needed
    "history_under_replace",   # known gap: replace keeps no queryable history
    "authority_under_keep_both",  # known gap: the provenance guard fires only under replace
})

TransitionKind = Literal["add", "replace", "ignore", "keep"]


def _ts(s: str) -> datetime:
    d = datetime.fromisoformat(s)
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


@dataclass(frozen=True)
class TypeSemantics:
    """The scenario's declared contract for one memory type.

    ``conflict`` — ``replace``: one live state per slot, the newer-and-not-weaker
    write overwrites it; ``keep_both``: every write is retained with its own
    validity window and the current state is whichever is valid latest.
    ``resolve_by`` — which dimensions an incoming write must be no weaker on to
    replace (conjunctive guard). ``None`` = the variant's default.
    """
    name: str
    conflict: Literal["replace", "keep_both"] = "replace"
    resolve_by: tuple[str, ...] | None = None


@dataclass(frozen=True)
class MemoryWrite:
    id: str
    type: str
    subject: str
    content: str
    observed_at: datetime
    source_type: str = "explicit_user"
    authority: float | None = None      # None = this write makes no authority claim
    confidence: float = 1.0
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    expected_transition: TransitionKind | None = None


@dataclass(frozen=True)
class Query:
    id: str
    type: str
    subject: str
    as_of: datetime | None            # None = current state
    expected: str | None              # None = no valid state at that time
    mechanism: str


@dataclass(frozen=True)
class Scenario:
    id: str
    category: Literal["authority", "temporal", "typed", "control", "mixed", "known_gap"]
    description: str
    types: dict[str, TypeSemantics]
    writes: tuple[MemoryWrite, ...]
    queries: tuple[Query, ...]
    negative_control: bool = False

    def semantics_for(self, type_name: str) -> TypeSemantics:
        return self.types.get(type_name, TypeSemantics(type_name))


DEFAULT_SCENARIOS = Path(__file__).parent / "scenarios" / "pilot.json"


def load_scenarios(path: str | Path = DEFAULT_SCENARIOS) -> list[Scenario]:
    raw = json.loads(Path(path).read_text())
    out: list[Scenario] = []
    for s in raw["scenarios"]:
        types = {
            t["name"]: TypeSemantics(
                name=t["name"],
                conflict=t.get("conflict", "replace"),
                resolve_by=tuple(t["resolve_by"]) if t.get("resolve_by") is not None else None,
            )
            for t in s.get("types", [])
        }
        writes = tuple(
            MemoryWrite(
                id=w["id"], type=w["type"], subject=w["subject"], content=w["content"],
                observed_at=_ts(w["observed_at"]),
                source_type=w.get("source_type", "explicit_user"),
                authority=w.get("authority"),
                confidence=w.get("confidence", 1.0),
                valid_from=_ts(w["valid_from"]) if w.get("valid_from") else None,
                valid_to=_ts(w["valid_to"]) if w.get("valid_to") else None,
                expected_transition=w.get("expected_transition"),
            )
            for w in s["writes"]
        )
        queries = tuple(
            Query(
                id=q["id"], type=q["type"], subject=q["subject"],
                as_of=_ts(q["as_of"]) if q.get("as_of") else None,
                expected=q.get("expected"),
                mechanism=q["mechanism"],
            )
            for q in s["queries"]
        )
        for q in queries:
            if q.mechanism not in MECHANISMS:
                raise ValueError(f"{s['id']}/{q.id}: unknown mechanism {q.mechanism!r}")
        out.append(Scenario(
            id=s["id"], category=s["category"], description=s.get("description", ""),
            types=types, writes=writes, queries=queries,
            negative_control=bool(s.get("negative_control", False)),
        ))
    ids = [s.id for s in out]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate scenario ids")
    return out
