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
| scenarios | 42 — 11 authority · 10 temporal · 11 typed resolution · 3 control/mixed · **7 known-gap** |
| variants | `v0` (timestamped records, newest observation wins) · `v0_scd` (bitemporal SCD-2 table) · `v0_scd_g` (the table plus one global confidence guard, no types) · `v4_typedmem` (full typed resolution) |
| gold | `scenarios/pilot.json`, frozen 2026-09-13 |
| predictions | `scenarios/pilot_predictions.json`, written **before** each run |
| committed runs | `results/pilot-0.*` (12, V0 vs V4) · `results/pilot-1.*` (16, +V0-scd, known gaps) · `results/pilot-2.*` (33, A and C expanded) · `results/pilot-3.*` (42, +V0-scd-g, B chains) |

The scope is deliberately narrow: the extremes of the ablation ladder plus
two hard non-agent baselines, on forty-two cases. V1–V3 are not implemented until
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

`v0_scd_g` is that table plus one rule applied to every type alike: a write
that would become current may not be less confident than the row it
displaces. It answers a single question — does TypedMem win the typed
category because it *has* a guard, or because the guard *differs by type*?

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

## Pilot-3 result

```text
variant         state  temporal  transit  corrupt │ authority  temporal     typed     mixed   control known_gap
v0               0.55      0.59     0.67     1.00 │      0.50      0.48      0.60      0.00      1.00      0.67
v0_scd           0.84      1.00     0.71     0.67 │      0.67      1.00      0.67      1.00      1.00      0.75
v0_scd_g         0.85      1.00     0.71     0.44 │      0.67      1.00      0.67      1.00      1.00      0.83
v4_typedmem      0.89      0.84     0.96     0.00 │      1.00      1.00      1.00      1.00      1.00      0.33
```

All 73 query-level predictions matched observation; corruption-rate
predictions (1.00 / 0.67 / 0.44 / 0.00 over 18 opportunities) matched; every
variant is correct on every negative control. One labelling correction was
made before the committed run and is recorded in
`pilot_predictions.json`: C-11, a per-slot control, had an update at
confidence 0.4 that also exercised the deadline's newest-wins rule;
`v0_scd_g` failed it — as predicted for that variant — and the
negative-control test flagged that a control was exercising a mechanism.
The write's confidence was raised to 0.9; the gold state did not change.
Full tables and every failure in `results/pilot-3.txt`.

### What the table says

**A global confidence guard does not move the typed column.** That is the
result pilot-3 was run for. `v0_scd_g` gains exactly the cases the guard
coincides with the declared rule (`confidence_guard` 0.00 → 1.00: C-02, C-03's
fact, C-07) and loses exactly the cases it contradicts it
(`type_specific_resolution` 0.56 → 0.44: C-01, C-03's deadline, C-04). Net:
0.67 → 0.67. A guard that is right for a biographical fact is wrong for a
deadline, and a single rule can only be one of them. TypedMem's 1.00 in that
column is therefore not "it has a guard"; it is "the guard is the type's".
RQ3 has its first supporting number.

**Authority did not move either** (0.67 → 0.67, `authority_veto` 0.33 → 0.33):
confidence is not authority, measured. The whole pattern:

```text
temporal    v0  <  v0_scd  =  v0_scd_g  =  v4     validity windows are not the novelty
authority   v0  <  v0_scd  =  v0_scd_g  <  v4     provenance-aware resolution is
typed       v0  <  v0_scd  =  v0_scd_g  <  v4     per-type guards are — not "a guard"
corruption  1.00   0.67       0.44         0.00   each mechanism removes some; only authority removes the rest
known_gap   v4  <  v0  <  v0_scd  <  v0_scd_g     and the table with a guard expresses G-05, which TypedMem cannot
```

Temporal held at 1.00 for both tables and TypedMem through chains of length
four, reversed observation order, expiry with no successor, a future state
mid-chain and two explicit boundaries (B-04..B-10). V0 fell to 0.48 — the
observation-time rule has nothing to say once observed order and valid order
part. The temporal machinery is correct and unoriginal at this size too.

The tables' authority "wins" (A-02, A-08) are not authority at all: the
incoming write describes an older state, and a bitemporal table files it as
history. The mechanism label says `effective_from`, and that is what fired.
C-09 and C-10's scratch-note slot are where an always-replace type defeats
both tables and V0's newest-observation rule gets lucky.

**Corruption rate is where the ladder is most legible**: 1.00 → 0.67 → 0.44
→ 0.00 over eighteen opportunities. Validity removes the older-effective
writes; the guard removes the weaker ones; what is left — a newer, stronger
write from a source not entitled to make it — only authority removes. A data warehouse has no concept of a write
that is *not entitled* to displace the current row; that concept is the
whole of Category A.

**The known-gap column is the diagnostic value, and it got sharper.**
`v0_scd_g` scores 0.83 there against TypedMem's 0.33, and one of its wins is
G-05: a table that keeps history *and* has a guard expresses "retain history,
but a weaker write does not become current" — which TypedMem's contract
cannot, because every guard is `replace`-only. Two contract gaps, measured
rather than suspected, and now with a baseline that has neither:

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
output of a working harness. Forty-two cases support no statistics. What the
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

### Where this leaves Mode A

The five conditions for moving from harness validation to research
evaluation (README, pilot-2; plan §18) are all met on forty-two cases: the
bitemporal baselines tie TypedMem on pure temporal; a global confidence guard
does not explain the typed separation; the authority improvement is confined
to provenance conflicts; negative controls are flat for every variant; and
TypedMem loses every pre-registered known gap. Mode A stops here for
analysis. Nothing is added to the scenario set, no TypedMem change is made,
and Mode B stays out of scope until that analysis is written up.
