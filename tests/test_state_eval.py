"""Mode A state-level diagnostic: harness invariants and the pilot's
pre-registered predictions.

Three things are asserted. (1) V0 shares no resolution code with TypedMem —
importing it must not import typedmem. (2) The runner is deterministic.
(3) Observed outcomes match the predictions frozen in
``scenarios/pilot_predictions.json``; a mismatch fails loudly, because it is
a finding (plan §15) and the fix is an investigation, never an edit to this
file to make it pass.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from reliagent_bench.memory.state_eval import load_scenarios
from reliagent_bench.memory.state_eval.runner import run
from reliagent_bench.memory.state_eval.schema import DEFAULT_SCENARIOS
from reliagent_bench.memory.state_eval.typedmem_v4 import TypedMemV4
from reliagent_bench.memory.state_eval.v0 import V0Baseline

PREDICTIONS = DEFAULT_SCENARIOS.parent / "pilot_predictions.json"


def test_v0_does_not_import_typedmem():
    """V0 must be independent of TypedMem at the source level and at import
    time. The parent ``reliagent_bench.memory`` package imports TypedMem for the
    retrieval track, so the import-time check loads ``v0.py`` (and the schema it
    depends on) directly from disk, outside the package, and asserts that no
    typedmem module appears."""
    v0_src = Path(V0Baseline.__module__.replace(".", "/") + ".py")
    v0_path = Path(__file__).resolve().parents[1] / "src" / v0_src
    assert "typedmem" not in v0_path.read_text(), "v0.py mentions typedmem"

    code = f"""
import importlib.util, sys, types
pkg = types.ModuleType('se'); pkg.__path__ = [{str(v0_path.parent)!r}]; sys.modules['se'] = pkg
for name in ('schema', 'v0'):
    spec = importlib.util.spec_from_file_location('se.' + name, {str(v0_path.parent)!r} + '/' + name + '.py')
    mod = importlib.util.module_from_spec(spec); sys.modules['se.' + name] = mod; spec.loader.exec_module(mod)
bad = sorted(m for m in sys.modules if m == 'typedmem' or m.startswith('typedmem.'))
print(bad); sys.exit(1 if bad else 0)
"""
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert proc.returncode == 0, f"v0 pulled in typedmem modules: {proc.stdout.strip()} {proc.stderr[-400:]}"


def test_scenarios_load_and_are_well_formed():
    scenarios = load_scenarios()
    assert len(scenarios) == 12
    for s in scenarios:
        assert s.writes and s.queries
        for w in s.writes:
            assert w.expected_transition is not None, f"{s.id}/{w.id} has no expected transition"
        declared = set(s.types)
        for w in s.writes:
            assert w.type in declared, f"{s.id}: type {w.type!r} used by {w.id} is not declared"


def test_runner_is_deterministic():
    scenarios = load_scenarios()
    a = run([V0Baseline(), TypedMemV4()], scenarios).to_json()
    b = run([V0Baseline(), TypedMemV4()], scenarios).to_json()
    assert a == b


@pytest.fixture(scope="module")
def report():
    return run([V0Baseline(), TypedMemV4()], load_scenarios())


def test_predictions_match_observed(report):
    predicted = json.loads(PREDICTIONS.read_text())["predictions"]
    mismatches = []
    for v in report.variants:
        for q in v.queries:
            key = f"{q.scenario}/{q.query}"
            assert key in predicted, f"no prediction for {key}"
            if predicted[key][v.variant] != q.correct:
                mismatches.append(
                    f"{key} {v.variant}: predicted {'correct' if predicted[key][v.variant] else 'wrong'}, "
                    f"observed {q.actual!r} (gold {q.expected!r})"
                )
    assert not mismatches, "\n".join(mismatches)


def test_corruption_rate_matches_prediction(report):
    predicted = json.loads(PREDICTIONS.read_text())["corruption_rate"]
    for v in report.variants:
        assert v.corruption_rate() == pytest.approx(predicted[v.variant]), v.variant


def test_negative_controls_do_not_separate(report):
    """Every variant must be correct on every negative-control query."""
    controls = {s.id for s in load_scenarios() if s.negative_control}
    for v in report.variants:
        wrong = [q for q in v.queries if q.scenario in controls and not q.correct]
        assert not wrong, f"{v.variant} failed a negative control: {[(q.scenario, q.query) for q in wrong]}"
