"""Mode B runner.

    python -m reliagent_bench.memory.mode_b --dry-run      resolution stage only, no model
    python -m reliagent_bench.memory.mode_b --runs 5       full pilot (needs ANTHROPIC_API_KEY)

The resolution stage is deterministic and is what the design's
governing-state accuracy measures. The agent stage is stochastic and is
repeated ``--runs`` times per scenario × variant; every raw response is kept.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .agent import PROMPT_VERSION, SYSTEM, build_user_message, default_agent, parse_decision
from .schema import SOURCE_PRIORITY, load_scenarios
from .scoring import score
from .variants.b0 import B0
from .variants.b_scd import BSCD
from .variants.b_scd_g import BSCDG
from .variants.b_typed import BTyped
from .variants.oracle import NoMem, Oracle
from .variants.orderings import ORDERINGS

# Default variant set is the pilot's; the E1 orderings are selectable by name
# (--variant "S>C>R") and are the same objects E1 measured.
VARIANTS = [B0(), BSCD(), BSCDG(), BTyped(), Oracle(), NoMem()]
REGISTRY = {v.name: v for v in VARIANTS} | ORDERINGS
FAMILIES = ["provenance", "typed", "repeated_failure", "control"]


def _load_dotenv() -> None:
    """Read KEY=VALUE lines from a gitignored .env at the repo root, if present,
    so a key never has to be typed into a shell history."""
    import os
    for cand in (Path.cwd() / ".env", Path(__file__).resolve().parents[4] / ".env"):
        if cand.exists():
            for line in cand.read_text().splitlines():
                if "=" in line and not line.lstrip().startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"'))
            return


def _rate(xs):
    xs = [x for x in xs if x is not None]
    return None if not xs else sum(xs) / len(xs)


def _fmt(x):
    return "   —  " if x is None else f"{x:5.2f} "


def run(scenarios, runs: int, agent, only_variants=None):
    scores = []
    transcripts = []
    if only_variants:
        unknown = [n for n in only_variants if n not in REGISTRY]
        if unknown:
            raise SystemExit(f"unknown variant(s): {unknown}; known: {list(REGISTRY)}")
    variants = [REGISTRY[n] for n in only_variants] if only_variants else VARIANTS
    for v in variants:
        for s in scenarios:
            resolved = v.resolve(s)
            lines = resolved.payload_lines()
            gov = {slot: (m.id if m else None) for slot, m in resolved.governing.items()}
            if agent is None:
                scores.append(score(s, v.name, 0, resolved, None, agent_ran=False))
                continue
            user = build_user_message(s, lines)
            for r in range(runs):
                raw = agent.complete(SYSTEM, user, s.task.choices)
                d = parse_decision(raw, s.task.choices)
                scores.append(score(s, v.name, r, resolved, d.action, agent_ran=True))
                transcripts.append(dict(scenario=s.id, variant=v.name, run=r, governing=gov, memory=lines, action=d.action, reason=d.reason, raw=raw))
    return scores, transcripts


def render(scores, scenarios, agent_ran: bool, classes: dict[str, str] | None = None) -> str:
    by = defaultdict(list)
    for sc in scores:
        by[sc.variant].append(sc)
    lines = []
    if classes:
        # Phase 2 headline: by state class on the reversal pairs, then controls.
        cols = ["epistemic", "declared", "controls"]
        def cls(sc):
            return "controls" if sc.family == "control" else classes.get(sc.scenario)
        lines.append("Mode B Phase 2 · %d scenarios · %s" % (len(scenarios), "agent runs" if agent_ran else "resolution stage only"))
        lines.append("")
        for title, attr, runfilter in (("governing-state accuracy (deterministic)", "governing_correct", lambda sc: sc.run == 0),
                                       ("task success (mean over runs)", "action_correct", lambda sc: True)):
            if attr == "action_correct" and not agent_ran:
                continue
            head = f"{'variant':10}" + "".join(f"{c:>12}" for c in cols) + f"{'all':>10}"
            lines += [title, head, "─" * len(head)]
            for v, scs in by.items():
                per = {c: _rate([getattr(sc, attr) for sc in scs if runfilter(sc) and cls(sc) == c]) for c in cols}
                lines.append(f"{v:10}" + "".join(f"{_fmt(per[c]):>12}" for c in cols) + f"{_fmt(_rate([getattr(sc, attr) for sc in scs if runfilter(sc)])):>10}")
            lines.append("")
        if agent_ran:
            lines += ["per scenario, correct runs (variant columns in run order)"]
            vs = list(by)
            lines.append(f"{'':8}" + "".join(f"{v:>9}" for v in vs))
            for sid in [s.id for s in scenarios]:
                row = []
                for v in vs:
                    n = sum(1 for sc in by[v] if sc.scenario == sid and sc.action_correct)
                    t = sum(1 for sc in by[v] if sc.scenario == sid)
                    row.append(f"{n}/{t}")
                lines.append(f"{sid:8}" + "".join(f"{x:>9}" for x in row))
            lines += ["", "attribution of failed runs"]
            for v, scs in by.items():
                lines.append(f"{v:10} " + json.dumps(dict(Counter(sc.attribution for sc in scs if sc.attribution))))
        lines.append("")
        lines.append("— pilot-format tables follow —")
        lines.append("")
    lines.append("Mode B pilot · %d scenarios · %s" % (len(scenarios), "agent runs" if agent_ran else "resolution stage only (dry run)"))
    lines.append("")
    lines.append("governing-state accuracy (deterministic; one row per variant)")
    head = f"{'variant':10}" + "".join(f"{f[:16]:>18}" for f in FAMILIES) + f"{'all':>10}"
    lines += [head, "─" * len(head)]
    for v, scs in by.items():
        per = {f: _rate([sc.governing_correct for sc in scs if sc.family == f and sc.run == 0]) for f in FAMILIES}
        lines.append(f"{v:10}" + "".join(f"{_fmt(per[f]):>18}" for f in FAMILIES) + f"{_fmt(_rate([sc.governing_correct for sc in scs if sc.run == 0])):>10}")
    if agent_ran:
        lines += ["", "task success (agent action == gold action; mean over runs)"]
        lines += [head, "─" * len(head)]
        for v, scs in by.items():
            per = {f: _rate([sc.action_correct for sc in scs if sc.family == f]) for f in FAMILIES}
            lines.append(f"{v:10}" + "".join(f"{_fmt(per[f]):>18}" for f in FAMILIES) + f"{_fmt(_rate([sc.action_correct for sc in scs])):>10}")
        lines += ["", "family rates: violation (provenance) · repeated failure (repeated_failure) · false avoidance (controls with applies=false)"]
        for v, scs in by.items():
            lines.append(f"{v:10} violation {_fmt(_rate([sc.violation for sc in scs]))} repeated {_fmt(_rate([sc.repeated_failure for sc in scs]))} false-avoid {_fmt(_rate([sc.false_avoidance for sc in scs]))}")
        lines += ["", "attribution of failed runs"]
        for v, scs in by.items():
            lines.append(f"{v:10} " + json.dumps(dict(Counter(sc.attribution for sc in scs if sc.attribution))))
    lines += ["", "resolution failures (scenario, variant, slot: got → gold)"]
    for v, scs in by.items():
        for sc in scs:
            if sc.run == 0 and not sc.governing_correct:
                lines.append(f"  {sc.scenario:6} {v:10}")
    return "\n".join(lines)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="reliagent-bench-mode-b")
    p.add_argument("--dry-run", action="store_true", help="resolution stage only; no model calls")
    p.add_argument("--runs", type=int, default=5)
    p.add_argument("--model", default=None)
    p.add_argument("--effort", default="low", choices=["low", "high"],
                   help="output_config effort; 'low' is the frozen E2 configuration")
    p.add_argument("--tasks", default=None)
    p.add_argument("--out", default="pilot-0")
    p.add_argument("--variant", action="append", default=None, help="run only these variants (repeatable); default: all")
    p.add_argument("--scenario", action="append", default=None, help="run only these scenario ids (repeatable)")
    p.add_argument("--list-models", action="store_true", help="print the model ids the API account can call, then exit")
    args = p.parse_args(argv)

    _load_dotenv()
    if args.list_models:
        import anthropic
        for m in anthropic.Anthropic().models.list():
            print(m.id)
        return 0

    scenarios = load_scenarios(args.tasks) if args.tasks else load_scenarios()
    if args.scenario:
        scenarios = [s for s in scenarios if s.id in set(args.scenario)]
    agent = None if args.dry_run else default_agent(effort=args.effort)
    if not args.dry_run and agent is None:
        print("no agent available (set ANTHROPIC_API_KEY) — use --dry-run for the resolution stage")
        return 2
    if agent is not None and args.model:
        agent.model = args.model

    classes = None
    if args.tasks:
        raw = json.loads(Path(args.tasks).read_text())
        if all("state_class" in x for x in raw["scenarios"]):
            classes = {x["id"]: x["state_class"] for x in raw["scenarios"]}
    scores, transcripts = run(scenarios, args.runs, agent, only_variants=args.variant)
    text = render(scores, scenarios, agent is not None, classes)
    print(text)
    out = Path(__file__).parent / "results"
    out.mkdir(exist_ok=True)
    stem = args.out + ("-dry" if agent is None else "") + ("-" + "+".join(v.replace(">", "") for v in args.variant) if args.variant else "") + ("-" + "+".join(args.scenario) if args.scenario else "")
    (out / f"{stem}.txt").write_text(text + "\n")
    (out / f"{stem}.json").write_text(json.dumps({
        "generated": datetime.now(timezone.utc).isoformat(),
        "prompt_version": PROMPT_VERSION, "model": getattr(agent, "model", None), "runs": args.runs if agent else 0,
        "request_config": getattr(agent, "request_config", None),
        "source_priority": SOURCE_PRIORITY,
        "scores": [asdict(s) for s in scores], "transcripts": transcripts,
    }, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
