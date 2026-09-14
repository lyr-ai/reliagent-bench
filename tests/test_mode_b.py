"""Mode B harness invariants: baselines independent of TypedMem; scenarios
well-formed and gold-consistent; the deterministic resolution stage matches
the pre-registered dry-run table."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from reliagent_bench.memory.mode_b import load_scenarios
from reliagent_bench.memory.mode_b.runner import VARIANTS, run
from reliagent_bench.memory.mode_b.scoring import governing_correct

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "src" / "reliagent_bench" / "memory" / "mode_b"


@pytest.mark.parametrize("module", ["b0", "b_scd", "b_scd_g"])
def test_baselines_do_not_import_typedmem(module):
    src = (PKG / "variants" / f"{module}.py").read_text()
    assert "typedmem" not in src.lower().replace("system under test", ""), f"{module}.py mentions typedmem"
    code = f"""
import importlib.util, sys, types
pkg = types.ModuleType('mb'); pkg.__path__ = [{str(PKG)!r}]; sys.modules['mb'] = pkg
vp = types.ModuleType('mb.variants'); vp.__path__ = [{str(PKG / 'variants')!r}]; sys.modules['mb.variants'] = vp
for name, path in (('mb.schema', 'schema.py'), ('mb.variants.base', 'variants/base.py'), ('mb.variants.{module}', 'variants/{module}.py')):
    spec = importlib.util.spec_from_file_location(name, {str(PKG)!r} + '/' + path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m)
bad = sorted(x for x in sys.modules if x == 'typedmem' or x.startswith('typedmem.'))
print(bad); sys.exit(1 if bad else 0)
"""
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr[-400:]


def test_scenarios_well_formed():
    ss = load_scenarios()
    assert len(ss) == 16
    for s in ss:
        assert s.gold_action in s.task.choices, s.id
        ids = {m.id for m in s.memories}
        for slot, mid in s.gold_governing.items():
            assert mid == "" or mid in ids, (s.id, slot)
        if s.family == "repeated_failure" or s.applies is False:
            assert s.failing_action in s.task.choices, s.id
        # the task text must not leak the memory rule (design §11)
        for m in s.memories:
            assert m.content.lower() not in (s.task.instruction + s.task.context).lower(), s.id
    fams = {f: sum(1 for s in ss if s.family == f) for f in ("provenance", "typed", "repeated_failure", "control")}
    assert fams == {"provenance": 4, "typed": 4, "repeated_failure": 4, "control": 4}


def test_oracle_resolves_gold_everywhere():
    oracle = next(v for v in VARIANTS if v.name == "oracle")
    for s in load_scenarios():
        assert governing_correct(s, oracle.resolve(s)), s.id


def test_resolution_stage_matches_preregistered_table():
    pred = json.loads((PKG / "predictions" / "pilot.json").read_text())["resolution_stage_observed_in_dry_run"]
    scores, _ = run(load_scenarios(), 0, None)
    for v in ("b0", "b_scd", "b_scd_g", "b_typed", "oracle"):
        for fam in ("provenance", "typed", "repeated_failure", "control"):
            xs = [sc.governing_correct for sc in scores if sc.variant == v and sc.family == fam]
            assert round(sum(xs) / len(xs), 2) == pred[v][fam], (v, fam)


def test_phase2_orderings_match_pre_registered_structure():
    """E1 structure (predictions/phase2.json): S>C>R ≡ b_scd_g everywhere; on the
    reversal pairs (source held equal) every ordering collapses to C-before-R or
    R-before-C; only the per-type policy is correct on both classes."""
    import json
    from pathlib import Path
    from reliagent_bench.memory.mode_b.schema import load_scenarios
    from reliagent_bench.memory.mode_b.scoring import governing_correct
    from reliagent_bench.memory.mode_b.variants.b_scd_g import BSCDG
    from reliagent_bench.memory.mode_b.variants.b_typed import BTyped
    from reliagent_bench.memory.mode_b.variants.orderings import FixedOrdering, all_orderings

    tasks = Path("src/reliagent_bench/memory/mode_b/tasks/phase2.json")
    cls = {s["id"]: s["state_class"] for s in json.loads(tasks.read_text())["scenarios"]}
    S = load_scenarios(tasks)
    for s in S:
        assert BSCDG().resolve(s).governing == FixedOrdering("SCR").resolve(s).governing
    pairs = [s for s in S if s.family == "typed"]
    assert all(governing_correct(s, BTyped().resolve(s)) for s in S)
    for v in all_orderings():
        ep = [governing_correct(s, v.resolve(s)) for s in pairs if cls[s.id] == "epistemic"]
        de = [governing_correct(s, v.resolve(s)) for s in pairs if cls[s.id] == "declared"]
        assert (all(ep) and not any(de)) or (all(de) and not any(ep)), v.name


def test_e2_runner_resolves_exactly_what_e1_measured():
    """The agent stage must run the same policy object E1 measured: for every
    Phase 2 scenario and every ordering, the governing ids the runner hands to
    the agent equal the ids recorded in the committed E1 result file."""
    import json
    from pathlib import Path
    from reliagent_bench.memory.mode_b.runner import REGISTRY, run
    from reliagent_bench.memory.mode_b.schema import load_scenarios
    from reliagent_bench.memory.mode_b.variants.orderings import ORDERINGS

    base = Path("src/reliagent_bench/memory/mode_b")
    e1 = json.loads((base / "results" / "phase2-e1.json").read_text())["governing"]
    S = load_scenarios(base / "tasks" / "phase2.json")
    for name in ORDERINGS:
        assert REGISTRY[name] is ORDERINGS[name]
        for s in S:
            got = {slot: (m.id if m else None) for slot, m in REGISTRY[name].resolve(s).governing.items()}
            assert got == e1[name][s.id], (name, s.id)
    # and the runner path itself (dry) uses the registry object
    scores, _ = run(S, 0, None, only_variants=["S>C>R"])
    assert {sc.scenario: sc.governing_correct for sc in scores} == json.loads((base / "results" / "phase2-e1.json").read_text())["per_scenario"]["S>C>R"]
