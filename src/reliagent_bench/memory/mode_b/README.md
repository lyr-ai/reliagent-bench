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

## Not yet done

The agent stage needs a model key. Everything upstream of it — scenarios,
gold, type semantics, the baseline policy, the prompt, the predictions, the
verdict rules — is frozen in this directory before it runs.
