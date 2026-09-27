"""V9 — TypedMem 0.9 **states**, through the public package API.

The mapping is frozen in ``external/predictions/states-0.9.3.md`` (committed
before this file existed):

- ``write``   → ``set_state(key=subject, value=content, valid_from=valid_from or
  observed_at, valid_to, source=source_type, authority)``
- ``query``   → ``get_state(subject, as_of)``; ``StateConflict`` → ``None``
- ``history`` → the key's ``state_history``, oldest first, values only

States have one contract, so the scenario's declared ``TypeSemantics``
(replace / keep_both / resolve_by) are deliberately ignored.

The states API is imported lazily: the bench's pinned environment (TypedMem
``ba010a1``, before states) can still import every runner; only running this
variant needs TypedMem >= 0.9.
"""

from __future__ import annotations

from .schema import MemoryWrite, Query, Scenario, TransitionKind


def _api():
    try:
        from typedmem import InMemoryStore, StateConflict
    except ImportError as e:  # pragma: no cover
        raise ImportError("v9_states needs TypedMem >= 0.9 (pip install 'typedmem>=0.9.3')") from e
    if not hasattr(InMemoryStore, "set_state"):  # pragma: no cover
        raise ImportError("v9_states needs TypedMem >= 0.9 (states API)")
    return InMemoryStore, StateConflict


_OUTCOME = {"new": "add", "changed": "replace", "past": "keep", "unchanged": "ignore",
            "conflict": "keep", "scheduled": "keep"}


class TypedMemStates:
    name = "v9_states"

    def __init__(self) -> None:
        self._store = None
        self._conflict = None

    def begin(self, scenario: Scenario) -> None:
        store_cls, self._conflict = _api()
        self._store = store_cls()

    def write(self, w: MemoryWrite) -> TransitionKind:
        r = self._store.set_state(
            w.subject, w.content,
            valid_from=w.valid_from or w.observed_at, valid_to=w.valid_to,
            source=w.source_type, authority=w.authority,
        )
        return _OUTCOME.get(r.outcome, "keep")

    def query(self, q: Query) -> str | None:
        try:
            return self._store.get_state(q.subject, as_of=q.as_of)
        except self._conflict:
            return None

    def history(self, type: str, subject: str) -> list[str]:
        return [e.value for e in reversed(self._store.state_history(subject))]
