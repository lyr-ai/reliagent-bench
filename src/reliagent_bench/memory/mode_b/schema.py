"""Mode B scenario schema (design §10).

A scenario separates the task (what the agent is asked, with a closed set of
actions), the memory observations (what the memory system receives, with
provenance), the declared state semantics per state type, the gold governing
state and gold action, a mechanism label, and whether it is a control.
Variants see the task and the memories; never the gold.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

Family = Literal["provenance", "typed", "repeated_failure", "control"]

# Source kinds, and the FROZEN global source-priority used by B-SCD-G (design §7).
# Higher wins. Declared here, before any run, so the baseline cannot be tuned.
SOURCE_PRIORITY: dict[str, int] = {
    "verified_result": 3,      # a test run, a CI status, an observed outcome
    "explicit_user": 3,        # the user said it
    "document": 2,             # a doc, ticket, or record
    "observed_behavior": 1,    # inferred from what the user did
    "model_inference": 0,      # the model's own guess
}


def _ts(s: str) -> datetime:
    d = datetime.fromisoformat(s)
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


@dataclass(frozen=True)
class Memory:
    id: str
    content: str
    state_type: str
    subject: str
    source_type: str
    authority: float
    confidence: float
    observed_at: datetime
    valid_from: datetime | None = None
    valid_to: datetime | None = None


@dataclass(frozen=True)
class Task:
    instruction: str
    context: str
    choices: tuple[str, ...]


@dataclass(frozen=True)
class TypeSemantics:
    name: str
    conflict: Literal["replace", "keep_both"] = "replace"
    resolve_by: tuple[str, ...] | None = None


@dataclass(frozen=True)
class Scenario:
    id: str
    family: Family
    description: str
    task: Task
    memories: tuple[Memory, ...]
    types: dict[str, TypeSemantics]
    gold_governing: dict[str, str]        # (state_type/subject) slot key → memory id that should govern ("" = none)
    gold_action: str
    mechanism: str
    negative_control: bool = False
    failing_action: str | None = None     # repeated_failure: the action that repeats the known failure
    applies: bool | None = None           # repeated_failure: whether the remembered failure applies here

    def slot(self, m: Memory) -> str:
        return f"{m.state_type}/{m.subject}"


DEFAULT_TASKS = Path(__file__).parent / "tasks" / "pilot.json"


def load_scenarios(path: str | Path = DEFAULT_TASKS) -> list[Scenario]:
    raw = json.loads(Path(path).read_text())
    out = []
    for s in raw["scenarios"]:
        mems = tuple(Memory(
            id=m["id"], content=m["content"], state_type=m["state_type"], subject=m.get("subject", "user"),
            source_type=m["source_type"], authority=float(m["authority"]), confidence=float(m.get("confidence", 1.0)),
            observed_at=_ts(m["observed_at"]),
            valid_from=_ts(m["valid_from"]) if m.get("valid_from") else None,
            valid_to=_ts(m["valid_to"]) if m.get("valid_to") else None,
        ) for m in s["memories"])
        for m in mems:
            if m.source_type not in SOURCE_PRIORITY:
                raise ValueError(f"{s['id']}: unknown source_type {m.source_type!r}")
        types = {t["name"]: TypeSemantics(t["name"], t.get("conflict", "replace"),
                                          tuple(t["resolve_by"]) if t.get("resolve_by") is not None else None)
                 for t in s.get("types", [])}
        out.append(Scenario(
            id=s["id"], family=s["family"], description=s.get("description", ""),
            task=Task(s["task"]["instruction"], s["task"].get("context", ""), tuple(s["task"]["choices"])),
            memories=mems, types=types, gold_governing=s["gold"]["governing"], gold_action=s["gold"]["action"],
            mechanism=s["mechanism"], negative_control=bool(s.get("negative_control", False)),
            failing_action=s.get("failing_action"), applies=s.get("applies"),
        ))
    ids = [s.id for s in out]
    assert len(ids) == len(set(ids)), "duplicate scenario ids"
    return out
