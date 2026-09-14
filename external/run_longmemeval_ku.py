"""External validation, benchmark #1: LongMemEval knowledge-update.

Oracle-candidate, Track E-B. The hand-normalised writes in
``normalized/longmemeval_ku_table.py`` are fed, identically, to six variants;
each question's queries are answered from the resolved state; answers are
scored against the normalised gold; every failure is attributed by the rules
frozen in ``predictions/longmemeval-ku.json``.

Run from the repo root:  .venv/bin/python external/run_longmemeval_ku.py
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE / "normalized"))

from longmemeval_ku_table import T  # noqa: E402
from reliagent_bench.memory.state_eval.schema import MemoryWrite, Query, Scenario, TypeSemantics  # noqa: E402
from reliagent_bench.memory.state_eval.typedmem_v4 import TypedMemV4  # noqa: E402
from reliagent_bench.memory.state_eval.v0 import V0Baseline  # noqa: E402
from reliagent_bench.memory.state_eval.v0_scd import V0SCDBaseline  # noqa: E402
from reliagent_bench.memory.state_eval.v0_scd_g import V0SCDGuardedBaseline  # noqa: E402

MANIFEST = json.loads((HERE / "triage" / "longmemeval-ku-manifest.json").read_text())
GROUP = {q["question_id"]: q["group"] for q in MANIFEST["questions"]}
STATE_TYPE = {q["question_id"]: q["state_type"] for q in MANIFEST["questions"]}
QDATE = {q["question_id"]: q["question_date"] for q in MANIFEST["questions"]}

# TypedMem's shipped DEFAULT_POLICIES, by the manifest's state_type
DEFAULT_CONFLICT = {"preference": "replace", "goal": "replace"}   # everything else → fact → keep_both


def _d(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def _qdate(s: str) -> datetime:
    return datetime.strptime(s[:10], "%Y/%m/%d").replace(tzinfo=timezone.utc)


def build_scenario(qid: str, conflict_mode: str) -> tuple[Scenario, list[tuple[str, str | None]]]:
    """conflict_mode ∈ {replace, keep_both, default}. Returns the scenario and
    the (query_id, expected) list; 'direction' queries are expanded into two
    as-of lookups the caller compares."""
    row = T[qid]
    stype = row.get("state_type", STATE_TYPE.get(qid, "fact"))
    if conflict_mode == "default":
        conflict = DEFAULT_CONFLICT.get(stype, "keep_both")
    else:
        conflict = conflict_mode
    types = {stype: TypeSemantics(stype, conflict=conflict)}
    writes = tuple(
        MemoryWrite(id=f"w{i}", type=stype, subject=row["slot"], content=v, observed_at=_d(d),
                    source_type="explicit_user", authority=None, confidence=1.0)
        for i, (d, v) in enumerate(row["writes"])
    )
    queries: list[Query] = []
    expected: list[tuple[str, str | None]] = []
    for q in row["queries"]:
        if q[0] == "current":
            queries.append(Query(id="current", type=stype, subject=row["slot"], as_of=_qdate(QDATE[qid]), expected=q[1], mechanism="none"))
            expected.append(("current", q[1]))
        elif q[0] == "after":
            k, exp = q[1], q[2]
            # "after write k" = one second after write k's observation instant,
            # which is always before write k+1 (writes on one date are spaced
            # ten seconds apart by the ordering pass in main()).
            as_of = _d(row["writes"][k][0]) + timedelta(seconds=10 * k + 1)
            queries.append(Query(id=f"after{k}", type=stype, subject=row["slot"], as_of=as_of, expected=exp, mechanism="none"))
            expected.append((f"after{k}", exp))
        elif q[0] == "direction":
            queries.append(Query(id="after0", type=stype, subject=row["slot"], as_of=_d(row["writes"][0][0]) + timedelta(seconds=1), expected=None, mechanism="none"))
            queries.append(Query(id="current", type=stype, subject=row["slot"], as_of=_qdate(QDATE[qid]), expected=None, mechanism="none"))
            expected.append(("direction", q[1]))
    return Scenario(id=qid, category="temporal", description="", types=types, writes=writes, queries=tuple(queries)), expected


def _num(v: str | None) -> float | None:
    if v is None:
        return None
    m = re.search(r"-?\d+(?:\.\d+)?", v.replace(",", ""))
    return float(m.group()) if m else None


def run_variant(name: str, make, conflict_mode: str):
    per_q = []
    for qid in T:
        scen, expected = build_scenario(qid, conflict_mode)
        v = make()
        v.begin(scen)
        for w in scen.writes:
            # same-day writes: nudge the second by one second so order is total
            v.write(w)
        answers = {q.id: v.query(q) for q in scen.queries}
        for kind, exp in expected:
            if kind == "direction":
                a, b = _num(answers.get("after0")), _num(answers.get("current"))
                got = None if a is None or b is None else ("up" if b > a else "down" if b < a else "same")
                ok = got == exp
                per_q.append(dict(question_id=qid, group=GROUP[qid], query="direction", expected=exp, actual=got, correct=ok,
                                  attribution=None if ok else ("unsupported_semantics:history_under_replace" if answers.get("after0") is None else "temporal_resolution")))
            else:
                got = answers.get(kind)
                ok = (got == exp)
                if ok:
                    attr = None
                elif exp is None and got is not None:
                    attr = "temporal_resolution:phantom_state"
                elif got is None and kind.startswith("after"):
                    attr = "unsupported_semantics:history_under_replace"
                elif exp is not None and exp not in [w.content for w in scen.writes]:
                    attr = "normalization"
                else:
                    attr = "temporal_resolution"
                per_q.append(dict(question_id=qid, group=GROUP[qid], query=kind, expected=exp, actual=got, correct=ok, attribution=attr))
    return per_q


VARIANTS = [
    ("v0",           lambda: V0Baseline(),            "replace"),
    ("v0_scd",       lambda: V0SCDBaseline(),         "replace"),
    ("v0_scd_g",     lambda: V0SCDGuardedBaseline(),  "replace"),
    ("v4_replace",   lambda: TypedMemV4(),            "replace"),
    ("v4_keep_both", lambda: TypedMemV4(),            "keep_both"),
    ("v4_default",   lambda: TypedMemV4(),            "default"),
]


def main() -> int:
    # same-day write ordering: give successive writes on one date increasing seconds
    for row in T.values():
        seen = Counter()
        fixed = []
        for d, v in row["writes"]:
            seen[d] += 1
            fixed.append((d, v, seen[d] - 1))
        row["_writes3"] = fixed
    # patch _d usage for seconds offsets via a wrapper on build_scenario's writes
    global build_scenario
    _orig = build_scenario

    def build_scenario_ordered(qid, mode):
        scen, expected = _orig(qid, mode)
        row = T[qid]
        ws = []
        for w, (_, _, off) in zip(scen.writes, row["_writes3"]):
            ws.append(MemoryWrite(**{**w.__dict__, "observed_at": w.observed_at + timedelta(seconds=10 * off)}))
        return Scenario(**{**scen.__dict__, "writes": tuple(ws)}), expected
    build_scenario = build_scenario_ordered

    results = {}
    for name, make, mode in VARIANTS:
        results[name] = run_variant(name, make, mode)

    groups = ["current_state", "historical_state", "both_states", "delta_direction", "accumulation", "abstention"]
    table = {}
    for name, rows in results.items():
        # question-level correctness: every query of the question correct
        byq = defaultdict(list)
        for r in rows:
            byq[r["question_id"]].append(r["correct"])
        qcorrect = {q: all(v) for q, v in byq.items()}
        table[name] = {g: (sum(qcorrect[q] for q in qcorrect if GROUP[q] == g), sum(1 for q in qcorrect if GROUP[q] == g)) for g in groups}
        table[name]["all_usable"] = (sum(qcorrect[q] for q in qcorrect if GROUP[q] not in ("abstention",)), sum(1 for q in qcorrect if GROUP[q] != "abstention"))

    lines = ["LongMemEval knowledge-update · oracle-candidate · hand-normalised writes · question-level accuracy",
             "adapter correction before this committed run: the first run placed 'after write k' queries one day after write k, which",
             "landed ON write k+1 when it fell the next day or the same day (c6853660, dfde3500) — every variant failed both identically.",
             "as_of is now write k + 1 s. An adapter boundary error, attributed to the adapter, not to any variant.", ""]
    head = f"{'variant':14}" + "".join(f"{g[:16]:>18}" for g in groups + ["all_usable"])
    lines += [head, "─" * len(head)]
    for name in results:
        lines.append(f"{name:14}" + "".join(f"{c:>13}/{n:<4}" for c, n in (table[name][g] for g in groups + ["all_usable"])))
    lines += ["", "failures (question, variant, query, expected → actual, attribution)"]
    for name, rows in results.items():
        for r in rows:
            if not r["correct"]:
                lines.append(f"  {r['question_id']:14} {name:14} {r['query']:9} {str(r['expected'])!s:28} → {str(r['actual'])!s:28} {r['attribution']}")
    attr = {name: dict(Counter(r["attribution"] for r in rows if not r["correct"])) for name, rows in results.items()}
    lines += ["", "failure attribution by variant: " + json.dumps(attr)]
    text = "\n".join(lines)
    print(text)
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    (out / "longmemeval-ku.txt").write_text(text + "\n")
    (out / "longmemeval-ku.json").write_text(json.dumps({"table": table, "attribution": attr, "per_query": results}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
