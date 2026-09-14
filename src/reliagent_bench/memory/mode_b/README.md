# Mode B — end-to-end agent utility (Phase 1 pilot)

Contract: [`docs/mode-b-design.md`](../../../../docs/mode-b-design.md).
Question: **do provenance-aware and type-dependent resolution semantics change
what an agent does?** Two stages, scored separately:

1. **Resolution** — a variant turns a scenario's memories into one governing
   memory per slot. Deterministic. Metric: governing-state accuracy.
2. **Decision** — one fixed model behind one fixed prompt receives the resolved
   payload and picks an action from a closed set. Stochastic; 5 runs. Metric:
   task success, plus violation / repeated-failure / false-avoidance rates and
   one attribution per failure.

```text
variants   b0 · b_scd · b_scd_g (frozen global policy: validity → source priority → confidence → recency)
           · b_typed (TypedMem, supported API) · oracle (gold state; bounds the agent) · nomem (reference)
scenarios  tasks/pilot.json — 4 provenance · 4 typed · 4 repeated-failure (B2-lite) · 4 controls
predictions predictions/pilot.json — written before any agent run
```

## Run

```bash
python -m reliagent_bench.memory.mode_b --dry-run        # resolution stage; no model
ANTHROPIC_API_KEY=… python -m reliagent_bench.memory.mode_b --runs 5   # full pilot
pytest tests/test_mode_b.py
```

## Resolution stage (dry run, committed as `results/pilot-0-dry.txt`)

```text
variant     provenance   typed   repeated_failure   control    all
b0                0.25    0.50               1.00      1.00   0.69
b_scd             0.25    0.50               1.00      1.00   0.69
b_scd_g           1.00    0.50               1.00      1.00   0.88
b_typed           1.00    1.00               1.00      1.00   1.00
oracle            1.00    1.00               1.00      1.00   1.00
```

`b_scd_g` — the strong baseline with source priority — gets every provenance
conflict right and half the typed family wrong: B-01 (deadline) and B-03
(commitment), where its global order ranks confidence above recency and the
declared semantics do not. `b0`/`b_scd` lose the opposite half (B-02, B-04).
This is the Mode A interaction at the resolution stage. **Whether it reaches
behaviour is the agent stage's question, and that has not been run.**

## Agent-stage protocol (decided before running)

1. **Oracle first, alone**: `python -m reliagent_bench.memory.mode_b --variant oracle --runs 5`
   (80 calls). Go/no-go: overall task success ≥ 0.95 and no family < 0.90.
   Below that, the tasks or prompt are the problem and no other variant runs.
2. **Model**: one Sonnet-class model, pinned by the *exact* id the account can
   call (`--list-models` prints them), temperature 0, recorded in the result
   file. Same model for every variant; never changed after a result is seen.
   Sonnet over Opus deliberately: the tasks are meant to be easy given the
   right state; a stronger model may solve them from context alone.
3. Then all memory-bearing variants × 5 runs; freeze; write
   `analysis/mode-b-pilot.md`.
4. No scenario is edited on the strength of oracle raw outputs unless it is a
   documented task ambiguity, in which case the agent-stage predictions are
   re-frozen before the comparative run.

The key is read from `ANTHROPIC_API_KEY` or a gitignored `.env` at the repo root.

## Pilot-0 (agent stage run)

`results/pilot-0-oracle.*` (gate, 80/80) and
`results/pilot-0-b0+b_scd+b_scd_g+b_typed+nomem.*` (400 runs). Task success:

```text
variant     provenance   typed   repeated_failure   control    all
b0                0.50    0.50               1.00      1.00   0.75
b_scd             0.50    0.55               1.00      1.00   0.76
b_scd_g           1.00    0.50               1.00      1.00   0.88
b_typed           1.00    1.00               1.00      1.00   1.00
oracle            1.00    1.00               1.00      1.00   1.00
nomem             0.75    0.85               1.00      0.75   0.84
```

Every failed run is `wrong_governing_state`; none is
`correct_state_wrong_agent_decision`. Verdicts and the reading —
BRQ1 SUPPORTED with the F3 qualification, BRQ2 SUPPORTED, BRQ3 INCONCLUSIVE
— are in [`analysis/mode-b-pilot.md`](../../../../analysis/mode-b-pilot.md).

## Phase 2 — global policy stress test

Design: [`docs/mode-b-phase2-global-policy-stress-test.md`](../../../../docs/mode-b-phase2-global-policy-stress-test.md).
Order of freezing, each committed before the next existed:

1. `semantics/phase2-types.md` — per-type governing-state semantics, argued
   without reference to any implementation; defines `confidence` (recorder's
   certainty of faithful capture; admission floor 0.5) and the epistemic /
   declared split.
2. `tasks/phase2.json` — 12 reversal pairs (24) + 12 controls. Every pair:
   equal source, incoming newer, incoming confidence 0.6 vs 0.9; only the state
   class varies. The lower confidence is earned by the text and the reason is
   recorded per scenario.
3. `predictions/phase2.json` — E1 per-ordering predictions, E2 selection rule,
   verdict rules.
4. `variants/orderings.py` + `e1.py` — the 6 permutations of (S, C, R) and the
   3 single-dimension policies; resolution stage only, no model.

```text
python -m reliagent_bench.memory.mode_b.e1          # E1, deterministic → results/phase2-e1.txt
```

E1 result (`results/phase2-e1.txt`): every ordering with C before R is
12/12 epistemic · 0/12 declared; every ordering with R before C is the mirror;
`b_typed` 24/24. No fixed ordering is correct on both classes. S-first
orderings pass all 12 controls; C-first lose K-05..K-08 (source conflicts);
R-first additionally lose K-09 (inference newer than a verified result).
Matches `predictions/phase2.json` row for row. E2 (agent stage) is not yet run.
