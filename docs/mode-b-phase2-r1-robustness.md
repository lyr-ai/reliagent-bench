# Mode B Phase 2 — R1 stronger-model robustness run

**Status:** Configuration frozen. Committed before any Phase-2 call under this configuration.
**Date:** 2026-09-19
**Mandate:** `analysis/mode-b-phase2.md` §6 (degenerate-output mode) and §8 (next step).
**This is a robustness check, not a new confirmatory experiment.** It registers no
new hypothesis, changes no verdict rule, and cannot overturn E2. E2 stands as the
committed result whatever R1 shows.

## 1. What changes, and what does not

Exactly one axis moves.

| | E2 (frozen) | R1 |
|---|---|---|
| `output_config.effort` | `low` | **`high`** |
| everything else | | unchanged |

Unchanged: the 36 scenarios (`tasks/phase2.json`), the 4 comparative variants
(`S>C>R`, `S>R>C`, `b_typed`, `nomem`), 5 repetitions, the scorer, the prompt,
the output schema, the model, and `max_tokens`.

`thinking: {type: "enabled"}` was considered and **is not available**: the API
rejects it for this model — `"thinking.type.enabled" is not supported for this
model`. So `effort` is the only stronger axis this model exposes, and the choice
of configuration involved no selection among candidates.

**`max_tokens` is deliberately NOT raised.** The degenerate outputs are not
truncation. Of the 93 degenerate transcripts in the frozen E2 data, 92 end in
`}` and 92 parse as valid JSON; the longest is 88 characters against a 300-token
cap. The model emitted *complete, schema-valid* objects whose `reason` field was
`"placeholder"`, `"invalid"`, or empty. Token budget is therefore already ruled
out as the cause, and changing it would confound attribution for no benefit.

## 2. Frozen configuration

```yaml
provider:            Anthropic Messages API
sdk:                 anthropic 1.5.0
model:               claude-sonnet-5          # id as resolved by the API
temperature:         not a request parameter on this model generation
top_p / top_k:       not a request parameter on this model generation
max_tokens:          300
thinking:            {type: disabled}
output_config:
  effort:            high                    # <-- the only change from E2
  format:            json_schema
    schema:          {action: string(enum = scenario choices),
                      reason: string}
                     required [action, reason], additionalProperties false
prompt_version:      mode-b-pilot-0
system_prompt:       sha256 585d783b9e8ae626a44e049d6582988d105d81ae8c2a03c753726582f38e803d
                     (483 chars, unchanged from E2)
user_prompt:         built by build_user_message() from the frozen
                     tasks/phase2.json; no template change
retry policy:        SDK default, max_retries = 2
timeout:             SDK default, Timeout(connect=5.0, read=600, write=600, pool=600)
scenarios:           36  (tasks/phase2.json, unchanged)
variants:            S>C>R, S>R>C, b_typed, nomem
repetitions:         5
total calls:         720
```

Command:

```sh
python -m reliagent_bench.memory.mode_b \
  --tasks src/reliagent_bench/memory/mode_b/tasks/phase2.json \
  --runs 5 --effort high --out phase2-1-effort-high \
  --variant 'S>C>R' --variant 'S>R>C' --variant b_typed --variant nomem
```

`--effort` defaults to `low`, so an unflagged run still reproduces E2.

## 3. Smoke test

Run on **`tasks/pilot.json` (Phase 1)**, never on Phase-2 scenarios, and scored
only for API validity, schema conformance and token cost — **never for task
accuracy**. No configuration was selected on the basis of pilot correctness.

```text
12 / 12 parseable and schema-valid
output tokens   min 30   max 52   mean 44
latency         ~1.65 s / call
stop_reason     end_turn on every call
```

## 4. Cost

Input measured by `messages.count_tokens` over a stratified 29-cell sample of
the 144 Phase-2 prompt cells: mean **251** tokens (min 219, max 299).

| | tokens | cost @ $3/M in, $15/M out |
|---|---:|---:|
| input, 720 × 251 | 180,720 | $0.54 |
| output, expected, 720 × 44 | 31,680 | $0.48 |
| **expected total** | | **≈ $1.02** |
| output, ceiling, 720 × 300 | 216,000 | $3.24 |
| **worst-case ceiling** | | **≈ $3.78** |

Wall-clock estimate at 1.65 s/call, serial: ~20 minutes.

## 5. The two questions this run answers

Pre-registered here, before the run, and nothing else is read out of R1 first:

1. **Does the degenerate-output mode drop?** E2: 117 of 900 runs (13%) across
   all variants including oracle; within the 720 comparative runs, 93 degenerate
   transcripts, and 9 of 217 failures classified
   `correct_state_wrong_agent_decision` — all of them degenerate-output runs.
2. **Does the directional interaction survive?** E2, degenerates excluded:
   `S>C>R` 1.00 / 0.00, `S>R>C` 0.22 / 1.00, `b_typed` 1.00 / 1.00, controls
   1.00 (epistemic / declared task success).

## 6. Reading rules, fixed in advance

| R1 outcome | Reading |
|---|---|
| degenerate rate drops **and** the interaction holds, `b_typed` near 1.00/1.00 | BRQ2-narrow does not depend on the weak configuration. Proceed to a second model. |
| degenerate rate drops **but** the interaction disappears | The mechanism may depend on model capability. Do not proceed to a second model; re-examine the claim. |
| degenerate rate stays high | Investigate the **output protocol** first — the schema admits any string in `reason`, so `"placeholder"` is a legal answer and the protocol, not the budget, is the suspect. Token budget is already excluded (§1). Do **not** add a second model. |

Only the first outcome unlocks the second-model replication.

## 7. Immutability

R1 writes `results/phase2-1-effort-high.{json,txt}`. It does not touch
`results/phase2-0-*`. E2's raw responses stay frozen at commit `20011c4`.

## 8. Known environment defect, not an experimental result

24 of 64 tests in the repository fail on this machine with `FileNotFoundError`
on:

```text
src/reliagent_bench/memory/datasets/seed.jsonl
```

That file is the frozen v1.0 Mode A dataset. It is matched by `.gitignore:7`
(`*.jsonl`, present since the initial scaffold) and has **never been tracked in
git**, so no branch removed it — it is simply absent from this working copy.
The affected suites are `test_memory_benchmark.py`, `test_memory_crosssystem.py`,
`test_memory_routers.py` and `test_memory_validate.py`, all Mode A.

Mode B is unaffected: `tests/test_mode_b.py` passes 8/8, and Phase 2 reads
`tasks/phase2.json`, which is tracked.

This must not be reported as "full test suite passes". A reviewer has to be able
to tell a missing local fixture from a failing experiment.
`datasets/FROZEN_MANIFEST.json` carries a `content_sha256`, so a recovered copy
can be verified against the freeze.
