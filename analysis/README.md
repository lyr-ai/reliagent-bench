# Analysis

Versioned benchmark history and failure analysis — the artifacts that make the
benchmark, not intuition, the source of engineering decisions.

```text
analysis/
    benchmark_history/   run records: benchmark/dataset/typedmem versions,
                         commit hashes, config, seed, overall metrics, failures
    category_reports/    per-category baseline→target improvement tables
    failure_reports/     every target-system failure, classified with a fix
    router_reports/      router experiment matrix (variants A-F + Oracle)
    validation_reports/  Oracle gap + failure distribution + stability + decision
    comparison_reports/  cross-system leaderboard + failure heatmap + environment
    plots/               (reserved)
    mode-a-pilot.md      state-level diagnostic (Mode A), pilots 0–3: questions,
                         design, results, three findings, the known-gap row, decision
    external-validation.md  the three findings against LongMemEval KU and GoodAI:
                         Finding 1 survived, 2 and 3 not testable, the history
                         limitation reproduced externally
```

Regenerate (writes a record keyed by version + config; new versions are kept,
same config overwrites its own record):

```bash
python -m reliagent_bench.memory --k 5 --seed 0 --save-analysis
```

## Failure taxonomy

Each failure of the target system is traced through the public TypedMem stages
and labeled: `router` (type filter dropped the relevant memory), `embedding`
(never a vector candidate), `temporal` (resolver removed the current memory),
`entity` (wrong entity on top), `ranking` (retrieved but ranked too low),
`unknown`.

## Current top-line finding (ReliAgent Bench v1.0 · dataset 1.0 · typedmem 0.8.0 @ 14f54b5)

104 tasks, k=5, seed=0. TypedMem current-state accuracy **0.77** vs. vector
**0.38**; stale-rate **0.00** vs. **0.36**. Of TypedMem's **24** failures,
**21 are `router`** (88%), 2 `ranking`, 1 `entity` — zero embedding/temporal.
Validation across three versions (42 → 82 → 104 tasks) shows **Rule + Global
Fallback ≈ Oracle** (current-state gap **+0.00** on the held-out eval set)
throughout: routing is effectively solved by the fallback, so an LLM router is
**not** justified (decision **Case A** — freeze routing, move to external
baselines).
