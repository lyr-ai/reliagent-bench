"""Phase 2 E1 — exhaustive fixed-ordering evaluation, resolution stage only.

    python -m reliagent_bench.memory.mode_b.e1

Deterministic; no model. Reports governing-state accuracy per state class
(epistemic / declared) on the reversal pairs, and on the controls, for every
fixed ordering, the three single-dimension policies, b0, b_scd and b_typed.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .schema import load_scenarios
from .scoring import governing_correct
from .variants.b0 import B0
from .variants.b_scd import BSCD
from .variants.b_typed import BTyped
from .variants.orderings import all_orderings

HERE = Path(__file__).parent
TASKS = HERE / "tasks" / "phase2.json"


def main() -> int:
    raw = json.loads(TASKS.read_text())
    cls = {s["id"]: s["state_class"] for s in raw["scenarios"]}
    S = load_scenarios(TASKS)
    pairs = [s for s in S if s.family == "typed"]
    ctrls = [s for s in S if s.family == "control"]
    variants = all_orderings() + [B0(), BSCD(), BTyped()]

    rows, per, gov = [], {}, {}
    for v in variants:
        res = {s.id: v.resolve(s) for s in S}
        ok = {sid: governing_correct(next(x for x in S if x.id == sid), r) for sid, r in res.items()}
        per[v.name] = ok
        gov[v.name] = {sid: {slot: (m.id if m else None) for slot, m in r.governing.items()} for sid, r in res.items()}
        ep = [ok[s.id] for s in pairs if cls[s.id] == "epistemic"]
        de = [ok[s.id] for s in pairs if cls[s.id] == "declared"]
        ct = [ok[s.id] for s in ctrls]
        rows.append((v.name, sum(ep), len(ep), sum(de), len(de), sum(ep) + sum(de), len(pairs), sum(ct), len(ct)))

    lines = [f"Mode B Phase 2 · E1 exhaustive fixed-ordering evaluation · resolution stage · {raw['version']} · {datetime.now(timezone.utc).date()}",
             "governing-state accuracy on the 12 reversal pairs (24 scenarios) by state class, and on the 12 controls", "",
             f"{'policy':10} {'epistemic':>10} {'declared':>10} {'pairs':>8} {'controls':>10}   fails"]
    lines.append("─" * 78)
    for name, e, en, d, dn, p, pn, c, cn in rows:
        fails = [sid for sid, o in per[name].items() if not o]
        lines.append(f"{name:10} {e:>6}/{en:<3} {d:>6}/{dn:<3} {p:>4}/{pn:<3} {c:>6}/{cn:<3}   {' '.join(fails)}")
    perfect_pairs = [r[0] for r in rows if r[5] == r[6]]
    lines += ["", f"orderings correct on all pairs: {perfect_pairs or 'none'}"]
    text = "\n".join(lines)
    print(text)
    out = HERE / "results"
    (out / "phase2-e1.txt").write_text(text + "\n")
    (out / "phase2-e1.json").write_text(json.dumps({"version": raw["version"], "rows": rows, "per_scenario": per, "governing": gov}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
