# Mode A — state-level diagnostic (pilot)

**Question:** if the memory *writes* are correct, does the state-management
layer resolve them into the correct *state*?

This is the Mode A harness from TypedMem's
[`docs/evaluation-plan.md`](https://github.com/lyr-ai/typedmem/blob/main/docs/evaluation-plan.md)
(§5, §6, §12–§17). It is not a retrieval benchmark — that is the track one
directory up — and it never involves an LLM. Scenarios construct memory writes
directly, with declared provenance and temporal claims; a variant applies them
in order and answers queries; the resolved state and the transition each write
caused are scored against gold labels frozen with the scenario file.

## What is in the pilot

| | |
|---|---|
| scenarios | 12 — 3 authority · 3 temporal · 3 typed resolution · 3 control/mixed |
| variants | `v0` (retrieval-oriented baseline) and `v4_typedmem` (full typed resolution) |
| gold | `scenarios/pilot.json`, frozen 2026-09-13 |
| predictions | `scenarios/pilot_predictions.json`, written **before** the first run |
| committed run | `results/pilot-0.{txt,json}` |

The scope is deliberately narrow: the two extremes of the ablation ladder, on
a dozen cases. V1–V3 and the bitemporal `V0-scd` baseline are not implemented
until this shows the separation it predicts (plan §17–§18).

### Type semantics are declared by the scenario

Each scenario declares what its memory types *mean* — `replace` with a
conjunctive `resolve_by` guard, or `keep_both` with validity windows — before
any variant sees it. That is what stops the gold labels from encoding
whatever TypedMem happens to do (plan §10).

### V0 shares nothing with TypedMem

`v0.py` is a bag of timestamped records with one rule: newest observation
wins. It must not import, and may not mention, the system under test.
`tests/test_state_eval.py` loads it from disk outside the package and fails
if any `typedmem` module appears. Without that test, the ablation ladder
would measure configuration rather than mechanism (plan §19-B).

## Reproduce

```bash
pip install -e '.[dev,state-eval]'          # pins TypedMem to the semantics commit
python -m reliagent_bench.memory.state_eval  # table
python -m reliagent_bench.memory.state_eval --json
pytest tests/test_state_eval.py             # invariants + predictions vs observed
```

Deterministic; no seeds, no randomness.

**TypedMem for the committed run:** `main` @ `33d989e` (semantics through
`ba010a1`; package version still reports 0.8.0).

## Pilot-0 result

```text
variant         state  temporal  transit  corrupt │ authority  temporal     typed     mixed   control
v0               0.53      0.57     0.68     1.00 │      0.33      0.57      0.50      0.00      1.00
v4_typedmem      1.00      1.00     1.00     0.00 │      1.00      1.00      1.00      1.00      1.00
```

All 17 query-level predictions matched observation on the first run; the
corruption-rate prediction (V0 = 1.00, V4 = 0.00) matched; both variants are
correct on every negative control.

### How to read this, and how not to

This says the harness works and that the mechanisms do what they claim on
cases designed to exercise them. It does **not** say TypedMem makes agents
more reliable, for three reasons that the plan already names:

1. **Self-confirmation.** The scenarios and the system were designed by the
   same hands. A perfect prediction match is the *expected* outcome of a
   working harness, not evidence about the world (plan §16).
2. **No hard baseline yet.** `V0-scd` — a bitemporal table — is predicted to
   tie V4 on every temporal scenario (plan §15, §24). Until it exists, the
   temporal column measures V0's lack of validity windows, not TypedMem's
   contribution over what a data engineer would build.
3. **V4 has no failures.** A diagnostic with a 1.00 column is not yet
   diagnosing anything about the system under test. The next scenarios
   should be the ones where the declared semantics and TypedMem's contract
   are expected to disagree — the automatic-close-of-previous-window gap
   under `replace` with historical `as_of` queries is the first candidate.

### What the pilot decides (plan §18)

Separation from the ablation: yes. Concentrated in the expected categories:
yes — V0's failures are exactly the `authority_veto`, `confidence_guard`,
`validity_*` and `effective_from` queries. Negative controls flat: yes.
Failures explained mechanistically: yes, each V0 failure is "newest
observation wins" applied where the gold says it should not.

So the pilot passes its own criteria, and the criteria were the cheap part.
Next, in order: `V0-scd`, then the scenarios where V4 is expected to fail,
then expansion to ~55 (plan §20, Phase 2A). Mode B stays out of scope.
