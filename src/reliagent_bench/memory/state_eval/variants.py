"""The variant protocol every system under test implements.

A variant is constructed fresh per scenario. It sees the scenario's declared
type semantics, receives the writes in order, and answers queries. It must not
see gold labels. What a variant may share with other variants is scenario
parsing, the candidate inputs, scoring and serialisation — nothing about how
state is resolved (plan §22, step 2).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .schema import MemoryWrite, Query, Scenario, TransitionKind


@dataclass
class VariantResult:
    states: dict[str, str | None] = field(default_factory=dict)      # query_id → content
    transitions: dict[str, TransitionKind] = field(default_factory=dict)  # write_id → what happened


class Variant(Protocol):
    name: str

    def begin(self, scenario: Scenario) -> None: ...
    def write(self, w: MemoryWrite) -> TransitionKind: ...
    def query(self, q: Query) -> str | None: ...


def execute(variant: Variant, scenario: Scenario) -> VariantResult:
    """Drive one variant through one scenario. Deterministic: writes in file
    order, then queries in file order."""
    variant.begin(scenario)
    result = VariantResult()
    for w in scenario.writes:
        result.transitions[w.id] = variant.write(w)
    for q in scenario.queries:
        result.states[q.id] = variant.query(q)
    return result
