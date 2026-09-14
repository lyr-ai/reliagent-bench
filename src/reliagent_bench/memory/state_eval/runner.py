"""Deterministic Mode A runner: every variant × every scenario, scored against
frozen gold, reported per category and per mechanism.

Metrics (plan §14): state accuracy (primary), transition accuracy, temporal
accuracy (queries with ``as_of``), corruption rate (a correct state
overwritten by a write the gold says should have been ignored).
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .schema import Scenario, load_scenarios
from .variants import Variant, VariantResult, execute


@dataclass
class QueryOutcome:
    scenario: str
    category: str
    query: str
    mechanism: str
    temporal: bool
    expected: str | None
    actual: str | None

    @property
    def correct(self) -> bool:
        return self.expected == self.actual


@dataclass
class TransitionOutcome:
    scenario: str
    write: str
    expected: str
    actual: str

    @property
    def correct(self) -> bool:
        return self.expected == self.actual

    @property
    def corrupted(self) -> bool:
        """Gold said this write must be ignored; the variant let it displace the
        current state. A historical insert (``keep``) pollutes history but does
        not corrupt the current state, and is not counted here."""
        return self.expected == "ignore" and self.actual == "replace"


@dataclass
class VariantReport:
    variant: str
    queries: list[QueryOutcome] = field(default_factory=list)
    transitions: list[TransitionOutcome] = field(default_factory=list)

    # ── metrics ─────────────────────────────────────────────────────────
    def state_accuracy(self, *, category: str | None = None, mechanism: str | None = None) -> float | None:
        qs = [q for q in self.queries
              if (category is None or q.category == category)
              and (mechanism is None or q.mechanism == mechanism)]
        return _rate([q.correct for q in qs])

    def temporal_accuracy(self) -> float | None:
        return _rate([q.correct for q in self.queries if q.temporal])

    def transition_accuracy(self) -> float | None:
        return _rate([t.correct for t in self.transitions])

    def corruption_rate(self) -> float | None:
        opportunities = [t for t in self.transitions if t.expected == "ignore"]
        return _rate([t.corrupted for t in opportunities])

    def failures(self) -> list[QueryOutcome]:
        return [q for q in self.queries if not q.correct]


@dataclass
class RunReport:
    scenarios: int
    variants: list[VariantReport]
    typedmem_version: str | None = None

    def to_json(self) -> str:
        return json.dumps({
            "scenarios": self.scenarios,
            "typedmem_version": self.typedmem_version,
            "variants": [
                {
                    "variant": v.variant,
                    "state_accuracy": v.state_accuracy(),
                    "temporal_accuracy": v.temporal_accuracy(),
                    "transition_accuracy": v.transition_accuracy(),
                    "corruption_rate": v.corruption_rate(),
                    "queries": [asdict(q) | {"correct": q.correct} for q in v.queries],
                    "transitions": [asdict(t) | {"correct": t.correct} for t in v.transitions],
                }
                for v in self.variants
            ],
        }, indent=2, default=str)


def _rate(flags: list[bool]) -> float | None:
    return None if not flags else sum(flags) / len(flags)


def score(variant_name: str, scenario: Scenario, result: VariantResult) -> tuple[list[QueryOutcome], list[TransitionOutcome]]:
    qs = [
        QueryOutcome(
            scenario=scenario.id, category=scenario.category, query=q.id,
            mechanism=q.mechanism, temporal=q.as_of is not None,
            expected=q.expected, actual=result.states.get(q.id),
        )
        for q in scenario.queries
    ]
    ts = [
        TransitionOutcome(
            scenario=scenario.id, write=w.id,
            expected=w.expected_transition, actual=result.transitions.get(w.id, "?"),
        )
        for w in scenario.writes if w.expected_transition is not None
    ]
    return qs, ts


def run(variants: list[Variant], scenarios: list[Scenario] | None = None) -> RunReport:
    scenarios = scenarios if scenarios is not None else load_scenarios()
    reports = []
    for v in variants:
        rep = VariantReport(variant=v.name)
        for s in scenarios:
            qs, ts = score(v.name, s, execute(v, s))
            rep.queries.extend(qs)
            rep.transitions.extend(ts)
        reports.append(rep)
    try:
        import typedmem
        version = getattr(typedmem, "__version__", None)
    except ImportError:
        version = None
    return RunReport(scenarios=len(scenarios), variants=reports, typedmem_version=version)


# ── text report ─────────────────────────────────────────────────────────

def _fmt(x: float | None) -> str:
    return "  —  " if x is None else f"{x:5.2f}"


def render(report: RunReport, scenarios: list[Scenario]) -> str:
    order = ["authority", "temporal", "typed", "mixed", "control", "known_gap"]
    categories = sorted({s.category for s in scenarios}, key=order.index)
    mechanisms = sorted({q.mechanism for s in scenarios for q in s.queries})
    lines = []
    lines.append(f"Mode A pilot · {report.scenarios} scenarios · typedmem {report.typedmem_version}")
    lines.append("")
    head = f"{'variant':14} {'state':>6} {'temporal':>9} {'transit':>8} {'corrupt':>8} │ " + " ".join(f"{c:>9}" for c in categories)
    lines.append(head)
    lines.append("─" * len(head))
    for v in report.variants:
        row = (f"{v.variant:14} {_fmt(v.state_accuracy()):>6} {_fmt(v.temporal_accuracy()):>9} "
               f"{_fmt(v.transition_accuracy()):>8} {_fmt(v.corruption_rate()):>8} │ "
               + " ".join(f"{_fmt(v.state_accuracy(category=c)):>9}" for c in categories))
        lines.append(row)
    lines.append("")
    lines.append("state accuracy by mechanism")
    head2 = f"{'variant':14} │ " + " ".join(f"{m[:12]:>12}" for m in mechanisms)
    lines.append(head2)
    lines.append("─" * len(head2))
    for v in report.variants:
        lines.append(f"{v.variant:14} │ " + " ".join(f"{_fmt(v.state_accuracy(mechanism=m)):>12}" for m in mechanisms))
    lines.append("")
    lines.append("failures")
    lines.append(f"{'scenario':10} {'variant':14} {'query':10} {'expected':22} {'actual':22} mechanism")
    for v in report.variants:
        for q in v.failures():
            lines.append(f"{q.scenario:10} {v.variant:14} {q.query:10} {str(q.expected):22} {str(q.actual):22} {q.mechanism}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse
    from .typedmem_v4 import TypedMemV4
    from .v0 import V0Baseline
    from .v0_scd import V0SCDBaseline

    p = argparse.ArgumentParser(prog="reliagent-bench-state-eval")
    p.add_argument("--scenarios", default=None, help="scenario JSON (default: pilot.json)")
    p.add_argument("--json", action="store_true", help="emit the full JSON report instead of the table")
    args = p.parse_args(argv)

    scenarios = load_scenarios(args.scenarios) if args.scenarios else load_scenarios()
    report = run([V0Baseline(), V0SCDBaseline(), TypedMemV4()], scenarios)
    print(report.to_json() if args.json else render(report, scenarios))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
