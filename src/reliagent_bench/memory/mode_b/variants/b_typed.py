"""B-Typed — TypedMem through its supported API. The scenario's declared type
semantics become a DomainProfile (conflict policy + resolve_by per type);
memories become Memory objects with a Source carrying the declared authority;
the governing memory per slot is what the temporal resolver returns."""
from __future__ import annotations

from datetime import datetime, timezone

from typedmem import ConflictPolicy, DomainProfile, InMemoryStore, Memory as TMemory, PolicyEngine, Source, TypeSpec
from typedmem.retrieval import resolve_temporal

from ..schema import Scenario
from .base import Resolved

_POLICY = {"replace": ConflictPolicy.REPLACE, "keep_both": ConflictPolicy.KEEP_BOTH}


class BTyped:
    name = "b_typed"

    def resolve(self, scenario: Scenario) -> Resolved:
        names = {m.state_type for m in scenario.memories} | set(scenario.types)
        specs = {}
        for n in names:
            sem = scenario.types.get(n)
            specs[n] = TypeSpec(name=n, conflict_policy=_POLICY[sem.conflict] if sem else ConflictPolicy.REPLACE,
                                resolve_by=sem.resolve_by if sem else None)
        profile = DomainProfile(name=f"mode-b:{scenario.id}", types=specs)
        store = InMemoryStore(PolicyEngine.from_profile(profile), profile=profile)
        origin: dict[str, object] = {}   # typedmem memory id → scenario Memory (by content match after resolution)
        for m in scenario.memories:
            tm = TMemory(type=m.state_type, content=m.content, subject=m.subject, confidence=m.confidence,
                         timestamp=m.observed_at, valid_from=m.valid_from, valid_to=m.valid_to,
                         sources=[Source(document_id=f"{m.source_type}:{m.id}", authority=m.authority)])
            store.add(tm)
        r = Resolved()
        now = datetime(2100, 1, 1, tzinfo=timezone.utc)
        for slot in {scenario.slot(m) for m in scenario.memories}:
            stype, subject = slot.split("/", 1)
            cands = [x for x in store.all() if x.type == stype and x.subject == subject]
            res = resolve_temporal(cands, as_of=now, collapse_types={stype})
            if not res:
                r.governing[slot] = None
                continue
            top = max(res, key=lambda x: x.effective_from)
            # map back to the scenario memory by content (contents are unique within a slot by construction)
            r.governing[slot] = next(m for m in scenario.memories if scenario.slot(m) == slot and m.content == top.content)
        return r
