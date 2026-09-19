# Mode B Phase 2 — R1 stronger-configuration robustness run: analysis

**Scope:** [`docs/mode-b-phase2-r1-robustness.md`](../docs/mode-b-phase2-r1-robustness.md),
configuration frozen at `b1dd5d0` and amendment R1.1 at `ffa1ac5`, both committed
before any R1 output existed.
**Raw:** `results/phase2-1-effort-high-SCR+SRC+b_typed+nomem.{json,txt}`, frozen at `c6fdb45`.
**Baseline:** E2, `results/phase2-0-SCR+SRC+b_typed+nomem.*`, untouched.
**Status:** frozen. Only the two pre-registered questions are read out.

## 1. Integrity

720 of 720 expected calls completed. 144 (variant, scenario) cells, 5 runs each,
none short. No empty response, no invalid JSON, no unparseable action. The
artifact's `request_config` records `effort: high`, `thinking: disabled`,
confirming the intended configuration actually reached the API.

**Independent calls: 720.** Transport-level retries are *not* instrumented — the
SDK default `max_retries = 2` was in force and any retry it performed is
invisible in the artifact. So 720 is the count of logical calls, and the true
number of HTTP attempts is 720 or more. This is a known gap, recorded rather
than estimated.

Wall clock 08:42:00 → 09:04:56 local, **22 min 56 s**, 1.91 s per logical call.

## 2. Q1 — does the degenerate-output mode drop?

Predefined operational detector (R1.1), applied identically to both arms.

```text
variant      E2 effort low   R1 effort high
S>C>R            24 / 180        24 / 180
S>R>C            27 / 180        22 / 180
b_typed          24 / 180        25 / 180
nomem            18 / 180        21 / 180
             ─────────────    ─────────────
TOTAL            93 / 720        92 / 720
                   12.9%           12.8%
```

**No.** One run of 720. The degenerate mode is not a property of the weak
configuration.

Output length barely moved either: mean raw completion 138.3 → 151.7 characters
(+9.7%). Raising effort did not make the model write more; it produced almost
the same text, including the same rate of `"placeholder"` fills.

This retires the hypothesis in `analysis/mode-b-phase2.md` §6 that a stronger
configuration "removes this noise". It does not. Combined with the truncation
check in the R1 design (§1 — 92 of 93 degenerate E2 responses are complete,
schema-valid JSON, longest 88 chars against a 300-token cap), **both candidate
causes registered in advance are now excluded**: it is neither token budget nor
effort level. What remains is the output protocol: the schema constrains
`action` to an enum but leaves `reason` an unconstrained string, so
`"placeholder"` is a fully conforming answer.

## 3. Q2 — does the directional interaction survive?

Original scorer, unmodified, both arms.

```text
governing state                       task success
variant    epist  decl  ctrl   all  │  epist  decl  ctrl   all
─────────────────────────────────── │ ───────────────────────
S>C>R  E2   1.00  0.00  1.00  0.67  │   0.95  0.00  0.98  0.64
       R1   1.00  0.00  1.00  0.67  │   0.98  0.00  1.00  0.66
S>R>C  E2   0.00  1.00  1.00  0.67  │   0.28  1.00  0.98  0.76
       R1   0.00  1.00  1.00  0.67  │   0.32  1.00  0.98  0.77
b_typed E2  1.00  1.00  1.00  1.00  │   0.97  1.00  0.97  0.98
       R1   1.00  1.00  1.00  1.00  │   1.00  1.00  0.98  0.99
nomem  E2   0.00  0.00  0.00  0.00  │   0.52  0.30  0.43  0.42
       R1   0.00  0.00  0.00  0.00  │   0.53  0.32  0.55  0.47
```

**Yes, and it sharpens.** Governing-state resolution is bit-identical — as it
must be, since resolution is deterministic and the model is downstream of it.
In task success every cell moves in the same direction or not at all:

- `b_typed` reaches **1.00 / 1.00**, up from 0.97 / 1.00.
- `S>C>R` holds **0.00** on declared. The unrecoverable error stays unrecoverable
  at higher effort — it is not an artifact of shallow reasoning.
- `S>R>C` epistemic rescue rises **0.28 → 0.32**, the direction
  `analysis/mode-b-phase2.md` §6 predicted ("may raise `S>R>C`'s epistemic rescue
  rate by reasoning harder about hedges"). Small, and on 60 runs.
- Controls stay flat, 0.97–1.00 across memory-bearing variants.
- `nomem` rises modestly (0.42 → 0.47 overall) and remains far below every
  memory-bearing variant on the classes those variants get right.

The asymmetry of the two errors is unchanged: recency-first on epistemic state
is partly survivable (0.32), confidence-first on declared state is not (0.00).

## 4. Secondary — failure attribution

Reported alongside, never as the degenerate metric (R1.1).

```text
                                      E2 low   R1 high
failures of 720                          217       200
  wrong_governing_state                  207       197
  correct_state_wrong_agent_decision       9         3
  other: unparseable_action                1         0
```

`correct_state_wrong_agent_decision` falls from 9 to 3 (0.015 of failures), well
inside the pre-registered 0.10 second-guessing stop condition, which did not
trigger in either arm.

Note the shape this exposes: the degenerate-output *rate* is flat while the
decisions those runs produce get better. A degenerate `reason` does not imply a
wrong action — which is exactly why the detector is described as operational.

## 5. Cost and latency

The runner does not record `usage`, so output tokens are estimated.

```text
input        720 × 251 tokens (measured pre-run by count_tokens)  = 180,720   $0.54
output       720 × ~44 tokens (usage measured in the smoke test)  =  31,680   $0.48
                                                                    ─────────────
                                                            total          ≈ $1.02
```

Predicted before the run: **≈ $1.02** expected, **$3.78** ceiling. Actual landed
on the expected figure; the ceiling was never approached because completions are
~44 tokens against a 300-token cap.

Latency **1.91 s per call** against 1.65 s measured in the smoke test. At 720
serial calls that is 23 minutes.

**The product reading:** at this task shape, `effort: high` cost essentially
nothing — +9.7% output characters, +16% latency, no meaningful spend increase —
and bought +0.03 on `b_typed` task success. It also bought nothing at all on the
degenerate mode. Neither the case for nor against high effort is strong here;
what the numbers rule out is the idea that the E2 result was purchased by
running the model too cheaply.

## 6. Interpretive boundary

The detector is a **predefined operational detector**. It measures
operationally defined degeneracy — an empty, `"placeholder"`, or very short
`reason` string — and `len(reason) < 12` will catch short but valid reasons. It
is not a measure of reasoning quality or of any cognitive state. No claim about
reasoning is made from it in either direction; the mechanism claims in §3 rest
on the pre-registered task outcomes and their interaction, not on this rate.

## 7. Verdict

Applied exactly as frozen in `docs/mode-b-phase2-r1-robustness.md` §6.

Q1 **did not** drop. Q2 **held**. That is branch 3:

> degenerate rate stays high → investigate the output protocol first; token
> budget is already excluded; do **not** add a second model.

**The second-model replication is not unlocked.**

Two things are established:

1. **BRQ2-narrow does not depend on the weak configuration.** The interaction
   reproduces at higher effort, unchanged in direction and slightly cleaner in
   magnitude. Degenerate outputs never threatened the conclusion — with them
   excluded the E2 interaction was already exact, and R1 reaches 1.00/1.00 on
   `b_typed` with them included.
2. **The degenerate mode is a protocol defect, not a capability defect.** Both
   pre-registered causes are excluded. The remaining suspect is the unconstrained
   `reason` field.

A note for whoever reads this next, so the record is unambiguous: §6 gated the
second model on Q1 *and* Q2, on the assumption that degeneracy was noise
threatening the result. R1 shows degeneracy is stable across configurations and
that the result survives it either way, so an argument could be made that the
gate's premise no longer applies. **That argument is not acted on here.**
Rewriting an unlock rule after seeing the data it was written to judge is the
post-hoc move the whole protocol exists to prevent. The frozen rule says branch
3; branch 3 is what this run returns. Changing it requires a dated amendment
with an outcome-independent justification, and it is not one this analysis can
write for itself.

## 8. Next

Per branch 3, and no further:

- Investigate the output protocol — constrain `reason`, or measure whether
  constraining it changes anything. Not a scenario change, not a model change.
- The second model stays blocked until the gate is either satisfied or amended
  on its own terms.

## 9. Known environment defect

24 of 64 repository tests fail on this machine with `FileNotFoundError` on
`src/reliagent_bench/memory/datasets/seed.jsonl` — the frozen v1.0 Mode A
dataset, matched by `.gitignore:7` (`*.jsonl`, present since the initial
scaffold) and never tracked in git, so no branch removed it. Affected:
`test_memory_{benchmark,crosssystem,routers,validate}.py`, all Mode A. Mode B is
unaffected; `tests/test_mode_b.py` passes 8/8 and Phase 2 reads the tracked
`tasks/phase2.json`. This is a missing local fixture, **not** a failing
experiment, and the suite must not be reported as passing.
