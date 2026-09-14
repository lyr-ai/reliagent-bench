"""External validation, benchmark #2: GoodAI LTM selected update tests.

Track E-A: statements are templated, so writes are derived by pattern from the
stored definitions in ``data/goodai-ltm/data/tests/'Benchmark 3 - 32k'`` —
no hand judgement per instance. Three tests run (Colours, NameList, SallyAnne);
Shopping and Restaurant are reported as NOT RUN with the reasons frozen in
``predictions/goodai-ltm.json``.

Timestamps are synthetic: statement k of a script is observed at epoch + k
minutes. That is all the benchmark provides (order), and all the tests need.

Run from the repo root:  .venv/bin/python external/run_goodai_ltm.py
"""

from __future__ import annotations

import glob
import json
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))

from reliagent_bench.memory.state_eval.schema import MemoryWrite, Query, Scenario, TypeSemantics  # noqa: E402
from reliagent_bench.memory.state_eval.typedmem_v4 import TypedMemV4  # noqa: E402
from reliagent_bench.memory.state_eval.v0 import V0Baseline  # noqa: E402
from reliagent_bench.memory.state_eval.v0_scd import V0SCDBaseline  # noqa: E402
from reliagent_bench.memory.state_eval.v0_scd_g import V0SCDGuardedBaseline  # noqa: E402

DEFS = HERE / "data" / "goodai-ltm" / "data" / "tests" / "Benchmark 3 - 32k" / "definitions"
EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


def t(k: int) -> datetime:
    return EPOCH + timedelta(minutes=k)


# ── pattern normalisers (Track E-A) ────────────────────────────────────────
COLOUR_PATTERNS = [
    r"^The name of my favourite colour is (\w+)\.$",
    r"^My favourite colour could be described as (\w+)\.$",
    r"^(\w+) is my favourite colour\.$",
]
NAME_PATTERNS = [
    r"^My name is (\w+)\.$", r"^Refer to me as (\w+)\.$", r"^Start calling me by my name which is (\w+)\.$",
    r"^(\w+) is my name\.$", r"^(\w+) is what I am called\.$", r"^My name has changed to (\w+)\.$",
]


def _match(patterns, s):
    for p in patterns:
        m = re.match(p, s.strip())
        if m:
            return m.group(1).lower()
    return None


def norm_colours(d):
    writes = [(k, _match(COLOUR_PATTERNS, s)) for k, (s, q) in enumerate(zip(d["script"], d["is_question"])) if not q]
    assert all(v for _, v in writes), d["script"]
    gold = d["expected_responses"][0].lower()
    return dict(slot="favourite_colour", writes=writes, kind="current", expected=gold)


def norm_names(d):
    writes = [(k, _match(NAME_PATTERNS, s)) for k, (s, q) in enumerate(zip(d["script"], d["is_question"])) if not q]
    assert all(v for _, v in writes), d["script"]
    gold = [x.lower() for x in d["expected_responses"]]
    return dict(slot="my_name", writes=writes, kind="history", expected=gold)


def norm_sallyanne(d):
    """Writes: the object's location. as_of: the observer's last exit."""
    obj = None; writes = []; exits = {}
    for k, s in enumerate(d["script"]):
        s = s.replace("(On TV)", "").strip()
        m = re.match(r"^The (\w+) (?:is|are) in the (\w+)\.?$", s)
        if m:
            obj = m.group(1); writes.append((k, m.group(2).lower())); continue
        m = re.match(r"^(\w+) moved the (\w+) to the (\w+)\.?$", s)
        if m:
            writes.append((k, m.group(3).lower())); continue
        m = re.match(r"^(\w+) exited the (\w+)\.?$", s)
        if m:
            exits[m.group(1)] = k
    q = d["script"][-1]
    who = re.search(r"Where will (\w+) look", q).group(1)
    as_of_step = exits.get(who, len(d["script"]))   # never exited → sees the final state
    gold = d["expected_responses"][0].lower()
    return dict(slot=f"location_of_{obj}", writes=writes, kind="as_of", as_of=as_of_step, expected=gold, observer=who)


TESTS = {"Colours": norm_colours, "NameList": norm_names, "SallyAnne": norm_sallyanne}
NOT_RUN = {"Shopping": "accumulation over a set-valued slot is not expressible as writes in any variant's protocol",
           "Restaurant": "dynamic script generated at run time; no replay harness in this phase"}


def build(inst, conflict):
    stype = "fact"
    types = {stype: TypeSemantics(stype, conflict=conflict)}
    writes = tuple(MemoryWrite(id=f"w{k}", type=stype, subject=inst["slot"], content=v, observed_at=t(k),
                               source_type="narrator", authority=None, confidence=1.0) for k, v in inst["writes"])
    if inst["kind"] == "current":
        queries = (Query(id="current", type=stype, subject=inst["slot"], as_of=t(10_000), expected=inst["expected"], mechanism="none"),)
    elif inst["kind"] == "as_of":
        queries = (Query(id="as_of", type=stype, subject=inst["slot"], as_of=t(inst["as_of"]) + timedelta(seconds=1), expected=inst["expected"], mechanism="none"),)
    else:
        queries = ()
    return Scenario(id="x", category="temporal", description="", types=types, writes=writes, queries=queries)


VARIANTS = [
    ("v0",           lambda: V0Baseline(),            "replace"),
    ("v0_scd",       lambda: V0SCDBaseline(),         "replace"),
    ("v0_scd_g",     lambda: V0SCDGuardedBaseline(),  "replace"),
    ("v4_replace",   lambda: TypedMemV4(),            "replace"),
    ("v4_keep_both", lambda: TypedMemV4(),            "keep_both"),
    ("v4_default",   lambda: TypedMemV4(),            "keep_both"),   # fact → keep_both under DEFAULT_POLICIES
]


def main() -> int:
    instances = []
    for test, norm in TESTS.items():
        for f in sorted(glob.glob(str(DEFS / test / "*.json"))):
            inst = norm(json.load(open(f)))
            inst["test"] = test; inst["id"] = f"{test}/{Path(f).name}"
            instances.append(inst)

    results = {}
    for name, make, conflict in VARIANTS:
        rows = []
        for inst in instances:
            scen = build(inst, conflict)
            v = make(); v.begin(scen)
            for w in scen.writes:
                v.write(w)
            if inst["kind"] == "history":
                got = v.history("fact", inst["slot"])
                ok = got == inst["expected"]
                attr = None if ok else ("unsupported_semantics:history_under_replace" if len(got) < len(inst["expected"]) else "temporal_resolution")
            else:
                got = v.query(scen.queries[0])
                ok = got == inst["expected"]
                attr = None if ok else ("unsupported_semantics:history_under_replace" if got is None else "temporal_resolution")
            rows.append(dict(id=inst["id"], test=inst["test"], expected=inst["expected"], actual=got, correct=ok, attribution=attr))
        results[name] = rows

    tests = list(TESTS)
    lines = ["GoodAI LTM selected update tests · Benchmark 3 (32k) stored definitions · Track E-A · instance-level accuracy", ""]
    head = f"{'variant':14}" + "".join(f"{x:>14}" for x in tests + ["all_run"])
    lines += [head, "─" * len(head)]
    table = {}
    for name, rows in results.items():
        table[name] = {tt: (sum(r["correct"] for r in rows if r["test"] == tt), sum(1 for r in rows if r["test"] == tt)) for tt in tests}
        table[name]["all_run"] = (sum(r["correct"] for r in rows), len(rows))
        lines.append(f"{name:14}" + "".join(f"{c:>10}/{n:<3}" for c, n in (table[name][x] for x in tests + ["all_run"])))
    lines += ["", "not run: " + "; ".join(f"{k} — {v}" for k, v in NOT_RUN.items()), "", "failures"]
    for name, rows in results.items():
        for r in rows:
            if not r["correct"]:
                lines.append(f"  {r['id']:24} {name:14} {str(r['expected'])[:40]:40} → {str(r['actual'])[:40]:40} {r['attribution']}")
    attr = {name: dict(Counter(r["attribution"] for r in rows if not r["correct"])) for name, rows in results.items()}
    lines += ["", "failure attribution by variant: " + json.dumps(attr)]
    text = "\n".join(lines); print(text)
    out = HERE / "results"; out.mkdir(exist_ok=True)
    (out / "goodai-ltm.txt").write_text(text + "\n")
    (out / "goodai-ltm.json").write_text(json.dumps({"table": table, "attribution": attr, "not_run": NOT_RUN, "per_instance": results}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
