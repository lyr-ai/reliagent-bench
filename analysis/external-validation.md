# External validation — analysis

**Scope:** [`docs/typedmem-external-validation.md`](../docs/typedmem-external-validation.md),
executed on the two benchmarks selected and frozen in
[`external/triage/candidates.md`](../external/triage/candidates.md).
**Depends on:** [`analysis/mode-a-pilot.md`](mode-a-pilot.md).
**Status:** frozen. Nothing in TypedMem was changed during this phase.

## 1. What was asked

Do the three Mode A findings survive on tasks that were not designed around
TypedMem? Search covered four benchmarks and 129 inspected examples under
rules frozen before each inspection; two were selected. The full
knowledge-update category of LongMemEval (78 questions) and the update tests
of the GoodAI LTM Benchmark (5 tests, 15 stored instances) were manifested
and frozen before any adapter existed; subset-level predictions were written
before the adapters, in `external/predictions/`.

## 2. Verdict per finding

| Mode A finding | verdict | on |
|---|---|---|
| 1 — bitemporal representation is sufficient for temporal state | **SURVIVED** | LongMemEval KU (65 usable questions), GoodAI (9 run instances) |
| 2 — confidence and provenance authority are not substitutes | **NOT TESTABLE** | no benchmark inspected contains a source-dependent conflict (0 of 129 examples; LoCoMo has attribution, not conflict) |
| 3 — a universal guard helps some types and hurts others | **NOT TESTABLE** | no benchmark inspected contains structurally similar updates that resolve differently by type (PerLTQA's types route retrieval; they never govern a merge) |

No fourth category. The history-preservation limitation below is reported as
an external failure of a TypedMem contract, separately from Finding 1's
verdict.

## 3. Results

### LongMemEval knowledge-update (oracle-candidate, hand-normalised writes)

```text
variant          current   historical   both   delta   accum   abstention   all usable
v0                 53/53         6/6      2/2     3/3     1/1         6/6        65/65
v0_scd             53/53         6/6      2/2     3/3     1/1         6/6        65/65
v0_scd_g           53/53         6/6      2/2     3/3     1/1         6/6        65/65
v4_replace         53/53         0/6      0/2     0/3     1/1         6/6        54/65
v4_keep_both       53/53         6/6      2/2     3/3     1/1         6/6        65/65
v4_default         53/53         5/6      2/2     3/3     1/1         6/6        64/65
```

Every `v4_replace` failure — all eleven — is attributed
`unsupported_semantics:history_under_replace`: the query asked for a value
the slot held before its last write, and under `replace` that value no longer
exists outside the event log. `v4_default` (TypedMem's shipped policies:
`fact → keep_both`, `preference/goal → replace`) loses exactly the one
history question whose slot is a goal (`9bbe84a2`). No variant fails a
current-state or abstention question. `results/longmemeval-ku.txt`.

### GoodAI LTM (Track E-A, pattern-normalised)

```text
variant          Colours   NameList   SallyAnne   all run
v0                  3/3        3/3         3/3       9/9
v0_scd              3/3        3/3         3/3       9/9
v0_scd_g            3/3        3/3         3/3       9/9
v4_replace          3/3        0/3         1/3       4/9
v4_keep_both        3/3        3/3         3/3       9/9
v4_default          3/3        3/3         3/3       9/9
```

Not run, as pre-registered: Shopping (accumulation is not expressible as
writes in any variant's protocol) and Restaurant (dynamic script; no replay
harness). `results/goodai-ltm.txt`.

## 4. What the results say

**Current state does not separate anyone.** Predicted, and observed: on 53
current-state questions and 3 Colours instances, all six variants are
identical. In both benchmarks observed order equals valid order and no
statement carries confidence or a validity date, so every variant reduces to
"latest write wins". This is the precise sense in which Finding 1 survives:
on externally designed temporal-state tasks, a bitemporal table is
sufficient, and TypedMem's temporal machinery adds nothing and loses nothing.

**History is where the contract shows.** 11 LongMemEval questions and 5
GoodAI instances need a value the slot no longer holds. Every
history-retaining variant — the two tables, `v4_keep_both`, `v4_default` on
fact-typed slots — answers all of them. `v4_replace` answers none, and the
one SallyAnne instance it gets right is the one where the observer is the
mover, so the current state *is* the answer. This is the Mode A known gap
(`history_under_replace`, G-01..03, G-06) reproduced on data that predates
TypedMem: LongMemEval's paired initial/current questions and GoodAI's
"all the names you have given me" and "where will X look" were written to
test memory systems in general.

**TypedMem can express history — as a different policy.** `v4_keep_both`
ties the tables everywhere. What the runs pin down is not that TypedMem
lacks history but that its contract makes *one governing value* and *a
queryable past* mutually exclusive per slot: `replace` gives the first,
`keep_both` the second, and there is no policy that gives both. Under the
shipped defaults a *fact* keeps history and a *goal* or *preference* does
not — which is why `v4_default` drops the Apex-level goal question and
nothing else. That is a design statement to carry forward, not a bug to fix
in this phase.

**The guard was inert, as predicted.** `v0_scd_g` equals `v0_scd` on every
question because hand-normalised writes carry no confidence structure. This
is not a result about the guard; it is confirmation that these benchmarks
contain nothing for a confidence guard to act on — the same absence that
makes Findings 2 and 3 not testable.

## 5. Corrections and limitations, recorded

- **One adapter correction before the committed LongMemEval run.** The
  first run placed "after write *k*" queries one day after write *k*, which
  landed *on* write *k+1* when it fell the next day or the same day
  (`c6853660`, `dfde3500`). Every variant failed both identically, which is
  the signature of an adapter error, not a mechanism. `as_of` is now write
  *k* + 1 s. Recorded in the runner's output header.
- **One prediction was off in magnitude, not direction.** SallyAnne under
  `v4_replace` was predicted 0/3 and observed 1/3, because one instance's
  observer is the mover. The pre-registered reading is unchanged.
- **Track E-B normalisation was by hand.** The benchmark's `has_answer`
  flags identify the turns; the slot and value on each turn were read by one
  annotator before the run and frozen in
  `external/normalized/longmemeval_ku_table.py`, with `norm: derived` on
  the eleven that required a judgement ("half of 10" → 5, "misplaced" →
  no). A second annotator has not checked them. The accumulation question
  (`69fee5aa`) had its delta resolved by the normaliser and is reported
  separately for that reason.
- **Oracle candidates, not retrieval.** Nothing here measures whether any
  system finds the right turns in a 115K-token history. That is the
  benchmark's headline difficulty and is out of scope for a state-semantics
  claim (contract §11).
- **Small, and mostly one-shaped.** 65 + 9 usable items; every update is
  the same speaker restating a value later. The finding that survives is
  correspondingly narrow: *latest valid value, with history retained where
  asked*.
- **Two GoodAI tests could not be run** without the adapter doing the
  test's work (Shopping) or a replay harness (Restaurant).

## 6. Decision

Finding 1 `SURVIVED`; Findings 2 and 3 `NOT TESTABLE` in existing
benchmarks after a targeted four-benchmark search. The replace-in-place
history limitation is now externally reproduced and is filed as an
evaluation-discovered limitation of the TypedMem contract, with this
document as its motivation.

The observation the search licenses, stated only now that the search is
done: **existing long-term-memory benchmarks test whether an agent remembers
state that changes over time; they do not test whether heterogeneous,
provenance-dependent observations should become governing state under
different resolution semantics.** The first half is supported by these runs.
The second half is not a finding — it is the gap that Mode B has to fill,
by constructing and validating the case.

Next: Mode B, designed around Findings 2 and 3 and an end-task metric
(repeated failure rate), with LoCoMo's speaker-swapped questions as an
externally motivated attribution probe. No TypedMem change precedes it.
