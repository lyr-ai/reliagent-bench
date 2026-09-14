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
| scenarios | 33 — 11 authority · 3 temporal · 11 typed resolution · 3 control/mixed · **5 known-gap** |
| variants | `v0` (timestamped records, newest observation wins) · `v0_scd` (bitemporal SCD-2 table) · `v4_typedmem` (full typed resolution) |
| gold | `scenarios/pilot.json`, frozen 2026-09-13 |
| predictions | `scenarios/pilot_predictions.json`, written **before** each run |
| committed runs | `results/pilot-0.*` (12, V0 vs V4) · `results/pilot-1.*` (16, three variants) · `results/pilot-2.*` (33, A and C expanded) |

The scope is deliberately narrow: the extremes of the ablation ladder plus
one hard non-agent baseline, on thirty-three cases. V1–V3 are not implemented until
there is a reason to attribute a difference between V0-scd and V4 to a
particular mechanism (plan §17–§18).

### Type semantics are declared by the scenario

Each scenario declares what its memory types *mean* — `replace` with a
conjunctive `resolve_by` guard, or `keep_both` with validity windows — before
any variant sees it. That is what stops the gold labels from encoding
whatever TypedMem happens to do (plan §10).

### The baselines share nothing with TypedMem

`v0.py` and `v0_scd.py` must not import, and may not mention, the system
under test. `tests/test_state_eval.py` loads each from disk outside the
package and fails if any `typedmem` module appears. Without that, the ladder
would measure configuration rather than mechanism (plan §19-B).

`v0_scd` is the baseline that matters: valid time and transaction time,
SCD-2 close-out of the superseded row, `as_of` from valid time — what a data
engineer would build — and no authority, confidence, or typed rules. It is
*predicted* to tie TypedMem on every temporal scenario (plan §15, §24).

### Known-gap scenarios are pre-registered TypedMem failures

Category `known_gap` holds cases where the declared semantics and the current
TypedMem contract are expected to disagree, and the prediction file says so
before the run. A test asserts every known-gap scenario predicts at least one
V4 failure. Two gaps are exercised, one of them twice:

- **`history_under_replace`** (G-01..03): under `replace`, TypedMem overwrites
  in place and keeps history only in the event log, so a historical `as_of`
  on a replaced slot has nothing to resolve against. A bitemporal table
  answers it.
- **`authority_under_keep_both`** (G-04): the provenance guard exists only
  under `replace`. Declare a type that keeps history *and* must not let a
  low-authority inference become current, and TypedMem inserts the inference
  and makes it current. No baseline gets this right either — it is a gap in
  the contract, not a place where a simpler system wins. G-05 shows the same
  for the confidence guard (`guards_under_keep_both`): every `resolve_by`
  guard is `replace`-only today.

## Reproduce

```bash
pip install -e '.[dev,state-eval]'          # pins TypedMem to the semantics commit
python -m reliagent_bench.memory.state_eval  # table
python -m reliagent_bench.memory.state_eval --json
pytest tests/test_state_eval.py             # invariants + predictions vs observed
```

Deterministic; no seeds, no randomness.

**TypedMem for the committed runs:** `main` @ `33d989e` (semantics through
`ba010a1`; package version still reports 0.8.0).

## Pilot-2 result

```text
variant         state  temporal  transit  corrupt │ authority  temporal     typed     mixed   control known_gap
v0               0.58      0.64     0.75     1.00 │      0.50      0.57      0.60      0.00      1.00      0.62
v0_scd           0.76      1.00     0.73     0.62 │      0.67      1.00      0.67      1.00      1.00      0.75
v4_typedmem      0.89      0.73     0.97     0.00 │      1.00      1.00      1.00      1.00      1.00      0.38
```

All 45 query-level predictions matched observation (pilot-1's 24 unchanged,
21 new); corruption-rate predictions (1.00 / 0.62 / 0.00 over 16
opportunities) matched; every variant is correct on every negative control,
including the in-category controls added to A and C. Full table, per-mechanism
breakdown and every failure in `results/pilot-2.txt`; pilot-1 in
`results/pilot-1.txt`.

### What the table says

**The headline gap opened as A and C grew, for the predicted reason.** At 16
scenarios V0-scd and TypedMem tied at 0.83 on disjoint failure sets; at 33,
with authority and typed resolution carrying more of the weight, it is 0.76
against 0.89 — and the temporal and known-gap columns did not move. The
pattern locates the claim:

```text
temporal    v0  <  v0_scd  =  v4        validity windows are not the novelty
authority   v0  ≈  v0_scd  <  v4        provenance-aware resolution is
typed       v0  =  v0_scd  <  v4        per-type guards are
known_gap   v4  <  v0  <  v0_scd        and replace-in-place costs history
```

V0-scd's authority "wins" (A-02, A-08) are not authority at all: the incoming
write describes an older state, and a bitemporal table files it as history.
The mechanism label says `effective_from`, and that is what fired. Its
`type_specific_resolution` score (0.56, equal to V0's) comes from the cases
where the declared rule happens to coincide with "latest valid state"; C-09
and C-10's scratch-note slot are where an always-replace type defeats it and
V0's newest-observation rule gets lucky.

**Corruption rate is where TypedMem's contribution over a bitemporal table
is most legible**: 0.62 → 0.00 over sixteen opportunities. A data warehouse has no concept of a write
that is *not entitled* to displace the current row; that concept is the
whole of Category A.

**The known-gap column is the diagnostic value.** Two contract gaps, both
now measured rather than suspected:

1. `replace` should close the previous validity window at the transition
   and retain it, so that historical `as_of` works without replaying the
   event log. V0-scd already does this; it is the obvious next TypedMem
   change — and it is *not* made in this phase (plan §3, §23). It is
   recorded as a measured gap with a number attached.
2. The authority veto should apply under `keep_both` as well, or the
   contract should say explicitly that history retention and provenance
   protection are mutually exclusive. Right now it says neither.

### How not to read this

Same hands designed scenarios and system; a prediction match is the expected
output of a working harness. Thirty-three cases support no statistics. What the
pilot establishes is narrower and more useful: the harness separates
mechanisms in the predicted places, the strong baseline behaves as
predicted, the system under test fails where it was predicted to fail, and
the two remaining claims — provenance and typed resolution — are the ones a
bitemporal table cannot make.

### What the pilot decides (plan §18)

Separation from the ablation: yes, and from the hard baseline: yes, in the
predicted categories only. Negative controls flat: yes. Failures explained
mechanistically: yes — every failure in `results/pilot-1.txt` carries the
mechanism that should have fired and did not.

Next: Category B toward ~15 with supersession chains (plan §24, bitemporal
feedback), a `V0-scd` variant that also carries confidence — to see whether
the typed column survives a baseline with a guard but no *types* — and then
Phase 2A. Mode B stays out of scope. No TypedMem change is made on the
strength of thirty-three cases.
