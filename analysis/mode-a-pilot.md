# Mode A pilot — analysis

**Scope:** the state-level diagnostic in `src/reliagent_bench/memory/state_eval/`,
pilots 0–3. **Status:** frozen at pilot-3; no further scenarios, no change to
the system under test. **Plan:** TypedMem `docs/evaluation-plan.md`, §5–§19, §24.

## 1. Questions

- **RQ1** — Does provenance-aware conflict resolution prevent state
  corruption: when an explicit statement conflicts with a newer, more
  confident, lower-authority inference, does the correct state survive?
- **RQ2** — Does explicit temporal validity — observation time separated from
  validity time — resolve retroactive, expired, future and historical
  queries that a single timestamp cannot?
- **RQ3** — Do type-specific replacement rules outperform one universal rule:
  is there a memory type for which any single guard is wrong?

A fourth question was added as a discipline rather than a hypothesis:
where does the system under test fail, and can that be pre-registered?

## 2. Experimental design

**Mode A** constructs memory writes directly — content, subject, provenance
authority, confidence, observation time, validity window — applies them in
order to a system variant, and compares the resolved state at each query,
and the transition each write caused, against gold labels frozen with the
scenario file. No LLM, no extraction, no retrieval: the question is whether
the *state-management layer* resolves correct writes correctly. Deterministic;
every run is byte-identical.

**Type semantics are declared per scenario** (`replace` with a conjunctive
`resolve_by` guard, or `keep_both` with validity windows) before any variant
sees them, so the gold does not encode what the system under test happens to
do.

**42 scenarios, 73 queries, 104 scored transitions**, grown over four runs:
11 authority · 10 temporal · 11 typed resolution · 3 control/mixed · 7
known-gap. Nine scenarios are negative controls on which no mechanism should
fire. **Predictions for every query and every variant were written by hand
from each variant's rule before the run that introduced it** (`pilot_predictions.json`);
a test fails if observation and prediction disagree. All 73 matched.

**Variants**, each isolating one thing:

| variant | rule | isolates |
|---|---|---|
| `v0` | timestamped records; newest observation wins | the failure rate of memory-as-records |
| `v0_scd` | bitemporal SCD-2 table: valid time + transaction time, close-out of the superseded row, `as_of` from valid time | whether temporal semantics alone explain the gap |
| `v0_scd_g` | `v0_scd` plus one global rule: a write that would become current may not be less confident than the row it displaces | whether *having* a guard explains the typed-resolution gap |
| `v4_typedmem` | TypedMem through its supported package API: authority veto, validity, per-type `resolve_by` | the system under test |

The three baselines neither import nor mention TypedMem; a test loads each
from disk outside the package and fails if any `typedmem` module appears.

**Metrics:** state accuracy (per query, per category, per mechanism label);
transition accuracy; temporal accuracy (`as_of` queries); corruption rate —
writes the gold says must be ignored that the variant applied as a
replacement of the current state, over 18 such opportunities.

## 3. Results

Pilot-3, 42 scenarios (`results/pilot-3.txt`):

```text
variant         state  temporal  transit  corrupt │ authority  temporal     typed     mixed   control known_gap
v0               0.55      0.59     0.67     1.00 │      0.50      0.48      0.60      0.00      1.00      0.67
v0_scd           0.84      1.00     0.71     0.67 │      0.67      1.00      0.67      1.00      1.00      0.75
v0_scd_g         0.85      1.00     0.71     0.44 │      0.67      1.00      0.67      1.00      1.00      0.83
v4_typedmem      0.89      0.84     0.96     0.00 │      1.00      1.00      1.00      1.00      1.00      0.33
```

Raw counts: correct queries 40 / 61 / 62 / 65 of 73; corrupted transitions
18 / 12 / 8 / 0 of 18.

By mechanism label (state accuracy):

```text
                authority  confidence  effective  guards_under  history_under  type      validity  validity  validity
                _veto      _guard      _from      _keep_both    _replace       _specific _boundary _expired  _future
v0                0.00       0.00       0.42        0.00          0.80           0.56      0.50      0.33      0.60
v0_scd            0.33       0.00       1.00        0.00          1.00           0.56      1.00      1.00      1.00
v0_scd_g          0.33       1.00       1.00        1.00          1.00           0.44      1.00      1.00      1.00
v4_typedmem       1.00       1.00       1.00        0.00          0.00           1.00      1.00      1.00      1.00
```

Every variant is correct on every negative control.

## 4. Findings

### Finding 1 — Temporal validity is not the novelty (RQ2)

```text
temporal    v0 0.48   <   v0_scd 1.00  =  v0_scd_g 1.00  =  v4 1.00
```

A bitemporal table resolves every temporal scenario tested: retroactive
updates (B-01), half-open boundaries (B-02, B-10), a declared future state
(B-03, B-09), chains of length three and four (B-04, B-07), observation
order decoupled from valid order — the most recent state learned first and
the oldest last, all in one month (B-07), a late-learned middle interval with
and without an explicit end (B-05, B-06), and expiry with no successor
(B-08). The observation-time baseline drops to 0.48 as soon as the two orders
part.

**Bitemporal representation is sufficient for the temporal-state cases we
tested.** This is stated as a positive result about the baseline. It locates
where the database problem ends: TypedMem's validity machinery is correct and
unoriginal, and the paper's claim cannot rest on it.

### Finding 2 — A universal guard trades one type's correctness for another's (RQ3)

```text
typed       v0_scd 0.67   =   v0_scd_g 0.67   <   v4 1.00
```

Adding a global confidence guard to the bitemporal table changes the typed
column by nothing in aggregate, and by a great deal underneath:

```text
confidence_guard            0.00 → 1.00      C-02, C-03 (fact), C-07 — the guard matches the declared rule
type_specific_resolution    0.56 → 0.44      C-01, C-03 (deadline), C-04 — the guard contradicts it
```

The cases that move are the ones where the declared semantics differ from a
generic guard: a *deadline* whose rule is "newest effective state wins,
confidence is irrelevant" is blocked by the same rule that correctly protects
a *biographical fact*. C-10 controls the surface structure — one numeric
pattern (newer, less confident, older effective) applied to three slots of
three types — and the global guard gets the fact right, the deadline wrong,
and the always-replace scratch note wrong.

**A universal guard can improve the memory types whose semantics match it
while simultaneously degrading types governed by different update
semantics.** TypedMem's 1.00 in this column is therefore not attributable to
having a guard; it is attributable to the guard being the type's. This is
the hypothesis RQ3 stated, with its first supporting number.

### Finding 3 — Confidence and authority are not substitutes (RQ1)

```text
authority   v0 0.50   <   v0_scd 0.67  =  v0_scd_g 0.67   <   v4 1.00
authority_veto            0.00          0.33          0.33            1.00
```

The global confidence guard does not help the authority category at all. The
two bitemporal "wins" in that category (A-02, A-08) are not authority: the
incoming write describes an older effective state and a bitemporal table
files it as history — the mechanism label says `effective_from`, and that is
what fired. On the cases where the only thing wrong with the incoming write
is *who said it* (A-01, A-04, A-06, A-10, M-01), every baseline takes it.

**Confidence and provenance authority are empirically non-substitutable in
the tested conflict cases.**

The corruption rate reads as an interpretable ablation pattern:

```text
v0 1.00  →  v0_scd 0.67  →  v0_scd_g 0.44  →  v4 0.00        (18 opportunities)
```

Validity removes the older-effective writes; the guard removes the weaker
ones; what remains — a newer, stronger write from a source not entitled to
make it — only authority removes. The variants are nested in mechanism but
not strictly in implementation (the tables and TypedMem share no code), so
this is read as a pattern, not as a causal decomposition of each step.

## 5. Failures and limitations

### The system under test loses every pre-registered known gap

```text
known_gap   v4 0.33   <   v0 0.67   <   v0_scd 0.75   <   v0_scd_g 0.83
```

This is the most important row in the table, and it is reported first. Seven
scenarios were written where the declared semantics and TypedMem's current
contract were expected to disagree; a test requires every one to predict at
least one TypedMem failure; all predictions held. Two contract limitations,
not implementation bugs:

- **`history_under_replace`** (G-01, G-02, G-03, G-06). Under `replace`
  TypedMem overwrites in place and keeps history only in the event log, so a
  historical `as_of` on a replaced slot resolves to nothing. Both tables
  answer it; more history (G-06, four steps) does not help.
- **`authority_under_keep_both` / `guards_under_keep_both`** (G-04, G-05,
  G-07). Every guard — the authority veto and every `resolve_by` key — exists
  only under `replace`. A type that keeps history *and* must not let a
  weaker or lower-authority write become current cannot be declared. On G-05
  the guarded table scores 1.00 and TypedMem 0.00: a structured table with
  one guard expresses "retain history, but a weaker observation does not
  become the governing state", and TypedMem's contract does not.

Neither is changed. If either is addressed after this analysis is frozen, it
is filed as an evaluation-discovered limitation with this row as its
motivation — not as an abstraction that seemed like it should exist.

### Limitations of the evidence

- **Self-designed diagnostic.** The scenarios and the system under test were
  designed by the same hands. Pre-registered predictions, in-category
  controls, and baselines that share no code limit the damage; they do not
  remove it. A perfect prediction match is what a working harness is
  supposed to produce.
- **Small N.** Forty-two scenarios and seventy-three queries support no
  statistics. Every number above is a count, reported as a count.
- **Mode A only.** Writes are constructed, not extracted; queries are exact
  state lookups, not generated answers. Extraction noise and generation
  noise — where most end-to-end memory failures live — are absent by design.
- **No external benchmark.** Nothing here has been run on a task someone
  else designed.
- **Two mechanism families are still entangled in `v4`.** No variant has
  authority without types or types without authority (V2/V3 in the plan).
  Findings 2 and 3 separate them by *category*, not by ablation.

### One correction, recorded

One pre-run control was corrected after the harness revealed that it
inadvertently exercised the mechanism it was intended to control for:
C-11's per-slot update had confidence 0.4 and so also exercised the
deadline's newest-wins rule; `v0_scd_g` failed it, as predicted for that
variant, and the negative-control test flagged it. The write's confidence
was raised to 0.9. The gold outcome was unchanged and the correction was
recorded in `pilot_predictions.json` before the committed pilot-3 run.

## 6. Decision

The Mode A diagnostic achieved its purpose. All five conditions set before
pilot-3 hold: the bitemporal baselines tie the system under test on pure
temporal cases; a global confidence guard does not explain the typed
separation; the authority improvement is confined to provenance conflicts;
negative controls are flat for every variant; and the system under test
loses every pre-registered known gap.

**No further scenarios are added to this set. No change is made to TypedMem.**
The benchmark is not optimised further; the remaining threat to the findings
is not mechanism isolation but that every task was designed here.

Next phase, in order of preference: **external validation** — an existing
long-term-memory benchmark with a temporal / update / conflict subset on
which `v0_scd_g` and `v4_typedmem` can be compared on tasks nobody designed
around either — and only if no such subset exists, **Mode B** with an
end-task metric (plan §14, repeated failure rate). Findings 1–3 are the claims
those phases either survive or retract.
