"""V4 — TypedMem, full typed resolution, through the supported package API.

Uses top-level ``typedmem`` exports and the ``typedmem.retrieval`` exports;
no store internals, no private modules.

Each scenario's declared type semantics become a ``DomainProfile``: the
conflict policy and ``resolve_by`` per type. Writes become ``Memory`` objects
with a ``Source`` carrying the declared authority (or no sources when the
write makes no authority claim). Queries use the public temporal resolver.

Transitions are inferred from what ``store.add`` returns — never from
TypedMem internals — so this adapter stays honest about what the public
contract exposes.
"""

from __future__ import annotations

from datetime import datetime, timezone

from typedmem import (
    ConflictPolicy, DomainProfile, InMemoryStore, Memory, PolicyEngine, Source, TypeSpec,
)
from typedmem.retrieval import resolve_temporal   # exported by typedmem.retrieval.__all__

from .schema import MemoryWrite, Query, Scenario, TransitionKind, TypeSemantics

# Fail at import if the installed TypedMem predates the semantics under test,
# so a stale environment cannot silently run the pilot against 0.8.0.
if not hasattr(TypeSpec, "resolve_by") or not hasattr(Memory, "valid_from"):  # pragma: no cover
    raise ImportError(
        "state_eval needs TypedMem with authority/validity/resolve_by semantics "
        "(main after v0.8.0); install with: pip install -e '.[state-eval]'"
    )

_POLICY = {
    "replace": ConflictPolicy.REPLACE,
    "keep_both": ConflictPolicy.KEEP_BOTH,
}


def _spec(sem: TypeSemantics) -> TypeSpec:
    return TypeSpec(
        name=sem.name,
        conflict_policy=_POLICY[sem.conflict],
        resolve_by=sem.resolve_by,          # None → TypedMem's default guard
    )


class TypedMemV4:
    name = "v4_typedmem"

    def __init__(self) -> None:
        self._store: InMemoryStore | None = None
        self._scenario: Scenario | None = None
        self._live: dict[tuple[str, str], str] = {}   # slot → id of the live record (replace types)

    def begin(self, scenario: Scenario) -> None:
        self._scenario = scenario
        # Every type referenced by a write gets a spec, so validation never
        # rejects a write for an undeclared type; undeclared types use the
        # scenario's fallback semantics (replace, default guard).
        names = {w.type for w in scenario.writes} | set(scenario.types)
        profile = DomainProfile(
            name=f"state-eval:{scenario.id}",
            types={n: _spec(scenario.semantics_for(n)) for n in names},
        )
        self._store = InMemoryStore(PolicyEngine.from_profile(profile), profile=profile)
        self._live = {}

    def write(self, w: MemoryWrite) -> TransitionKind:
        assert self._store is not None
        sources = []
        if w.authority is not None:
            sources.append(Source(document_id=f"{w.source_type}:{w.id}", authority=w.authority))
        m = Memory(
            type=w.type, content=w.content, subject=w.subject,
            confidence=w.confidence, timestamp=w.observed_at,
            valid_from=w.valid_from, valid_to=w.valid_to,
            sources=sources,
        )
        key = (w.type, w.subject)
        prior_id = self._live.get(key)
        returned = self._store.add(m)

        if prior_id is None:
            self._live[key] = returned.id
            return "add"
        if returned.id == m.id:
            # a new record was inserted beside the old one (keep_both)
            return "keep"
        if returned.id == prior_id and returned.content == w.content:
            return "replace"
        return "ignore"

    def query(self, q: Query) -> str | None:
        assert self._store is not None
        as_of = q.as_of or datetime.now(timezone.utc)
        candidates = [m for m in self._store.all() if m.type == q.type and m.subject == q.subject]
        resolved = resolve_temporal(candidates, as_of=as_of, collapse_types={q.type})
        if not resolved:
            return None
        # collapse_types leaves exactly one per slot; defensively pick the
        # latest effective_from if the resolver ever returns more
        return max(resolved, key=lambda m: m.effective_from).content
