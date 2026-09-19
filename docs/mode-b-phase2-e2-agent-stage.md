# Mode B Phase 2 — E2 Agent-Stage Validation

**Status:** Execution design — **executed 2026-09-19**
**Date:** 2026-09-19
**Depends on:** Phase 2 semantics table, frozen scenarios, E1 exhaustive global-policy result
**System under test:** TypedMem / ReliAgent Bench
**TypedMem changes during experiment:** None
**Results:** [`analysis/mode-b-phase2.md`](../analysis/mode-b-phase2.md) — raw responses frozen at `20011c4`, analysis at `3f9560e`

> This is the execution design that was followed, filed as written. The
> prediction tables keep their `?` placeholders on purpose: replacing them with
> the observed numbers would erase the record of what was registered before the
> run. The observed values live in the analysis.

---

## 1. Question

E1 established a deterministic resolution result:

> No fixed global ordering over source, confidence, and recency correctly
> resolves both epistemic and declared state across the frozen reversal pairs.

The informative contrast was:

```text
S > C > R
```

versus:

```text
S > R > C
```

with source held equal inside the core reversal pairs.

`S>C>R` resolves all epistemic cases correctly and all declared cases
incorrectly. `S>R>C` produces the complementary result. Typed per-state
semantics resolve both.

E2 asks one question:

> **Does this deterministic governing-state trade-off propagate into downstream
> agent behavior?**

E2 does not test whether TypedMem stores more information, retrieves better, or
has a better API. It tests whether choosing the wrong governing state causes the
agent to take the wrong action.

---

## 2. Prior evidence

### Phase 1

Mode B Phase 1 showed that governing-state errors can propagate directly to
agent decisions. Across memory-bearing variants, all observed failures were
attributed to `wrong_governing_state` and none to
`correct_state_wrong_agent_decision`.

Phase 1 also showed that a strong global source-priority baseline matched
TypedMem on the provenance family. **Provenance / source priority is therefore
not the Phase 2 contribution.**

### Phase 2 E1

The frozen 36-scenario set contains 24 reversal scenarios and 12 controls; 12
epistemic cases and 12 declared-state cases; six domains.

E1 exhaustively evaluated all six permutations of source, confidence and
recency, three single-dimension policies, B0, B-SCD and B-Typed. Every fixed
ordering split on epistemic versus declared semantics.

| Policy | Epistemic | Declared | Controls |
|---|---:|---:|---:|
| S>C>R | 12/12 | 0/12 | 12/12 |
| S>R>C | 0/12 | 12/12 | 12/12 |
| B-Typed | 12/12 | 12/12 | 12/12 |

No alternative global ordering dominated these two. This licenses E2.

---

## 3. Semantic distinction under test

Phase 2 does not claim that every memory type requires an arbitrary custom
policy. The narrower distinction is:

### Epistemic state

> What is currently true?

Multiple records provide evidence about the same standing question. For admitted
records of equal source authority, confidence may legitimately rank competing
observations. A newer but less faithfully captured observation does not
automatically replace stronger existing evidence.

### Declared state

> What has the actor decided, committed to, requested, or revised?

A valid later declaration changes the governing state. Once a revision has been
admitted as a valid record of the actor's act, the confidence associated with
the old record cannot permanently prevent the new declaration from governing.

Examples: deadline revision; commitment revision; explicit preference or
constraint revision.

The Phase 2 hypothesis is narrower than *every state type needs its own
resolver*. It is:

> **A single confidence-versus-recency ordering may be insufficient across
> epistemic and declared state.**

---

## 4. Confidence semantics

`confidence` has one meaning throughout Phase 2:

> The recorder's certainty that the memory record faithfully captures what its
> source conveyed.

It covers the correct slot, the correct value, the correct contextual binding,
and source hedging carried into the record.

It does **not** mean the system's posterior probability that the state is true,
source authority, or aggregated evidence strength. Those may be resolver outputs
or separate signals.

A lower-confidence explicit revision is permitted only when the scenario text
explains why the record is less certain:

```text
Existing:
    "The review deadline is Friday the 18th."
    confidence = 0.9

Incoming:
    "Monday, actually."
    confidence = 0.6
```

The uncertainty is in contextual recording and binding, not in whether the actor
performed a revision. All Phase 2 incoming records remain above the frozen
admission floor, `confidence >= 0.5`.

---

## 5. Frozen scenario structure

Core reversal pairs hold constant:

```text
source(existing) = source(incoming)
incoming is newer
confidence(existing) = 0.9
confidence(incoming) = 0.6
```

Only the state semantics change.

```text
epistemic  lower-confidence newer evidence  →  existing state governs
declared   admitted newer revision          →  incoming state governs
```

The 24 reversal scenarios span infrastructure/configuration, scheduling,
coding/project policy, travel, team workflow and personal profile. Pair types:
factual state ↔ deadline; factual state ↔ commitment; factual state ↔ explicit
preference/constraint. The remaining 12 scenarios are controls.

---

## 6. E2 variants

Only five variants are evaluated.

| variant | ordering | predicted epistemic | predicted declared | predicted controls |
|---|---|---|---|---|
| Global policy A | `S > C > R` | correct | incorrect | correct |
| Global policy B | `S > R > C` | incorrect | correct | correct |
| B-Typed | per-state, frozen before scenarios were generated | correct | correct | correct |

**Oracle** receives the gold governing state. Its purpose is to measure whether
the downstream decision task is solvable at all. It is not a competing memory
system.

**No-memory** receives no governing-state payload. Its purpose is to estimate
the model's task-context default, detect answer leakage, and test whether wrong
memory can be worse than no memory.

---

## 7. Oracle gate

Before comparative execution, Oracle runs five times per scenario.

Pre-registered gate:

```text
overall task success >= 0.95
AND
no semantic class < 0.90
```

Observed before the comparative run:

| Class | Oracle |
|---|---:|
| Epistemic | 0.98 |
| Declared | 0.92 |
| Controls | 1.00 |
| Overall | 0.97 |

The gate passes.

One genuine task-labeling defect, `P-10-D`, was corrected and re-run. The
correction did not change the intended semantic rule, was documented in
`predictions/phase2.json`, preserved the pre-correction gate result, and
produced 5/5 correct responses afterwards. One isolated `P-10-F` placeholder
response remains recorded as agent noise.

**No further scenario modification is permitted during the comparative run.**

---

## 8. Comparative execution

```text
36 scenarios
× 4 comparative variants
× 5 repetitions
= 720 agent calls
```

Comparative variants: `S>C>R`, `S>R>C`, `B-Typed`, `No-memory`. Oracle results
are carried forward from the gate.

The same model, model version, prompt, reasoning configuration, tool interface,
task text and scoring logic are used for every comparative variant. All raw
responses are retained.

---

## 9. Primary result

Overall accuracy is **not** the primary result. The primary table is:

| Variant | Epistemic | Declared | Controls |
|---|---:|---:|---:|
| S>C>R | ? | ? | ? |
| S>R>C | ? | ? | ? |
| B-Typed | ? | ? | ? |
| Oracle | 0.98 | 0.92 | 1.00 |
| No-memory | ? | ? | ? |

The pre-registered interaction is:

```text
S>C>R      epistemic high   declared low
S>R>C      epistemic low    declared high
B-Typed    epistemic high   declared high
Controls   approximately flat
```

The central evidence is the **variant × state-class interaction**, not
B-Typed's standalone score.

---

## 10. Behavioral propagation

For every run, distinguish the resolver output from the agent action. Every
failure receives one attribution:

```text
wrong_governing_state
correct_state_wrong_agent_decision
task_ambiguity
context_leakage
model_output_failure
other
```

The central propagation question:

> When a global policy selects the wrong governing state, does the downstream
> agent action become incorrect?

A state-resolution result alone is insufficient for E2.

---

## 11. Agent second-guessing stop condition

Phase 1 showed almost perfect propagation from governing state to action. Phase
2 explicitly tests whether that remains true.

If `correct_state_wrong_agent_decision` exceeds **10% of failures**, stop
interpreting E2 as a clean state-resolution experiment. That would indicate that
downstream model behavior has become an independent dominant source of error,
and the analysis must then separate resolution quality from agent compliance
with the resolved state rather than claiming direct behavioral propagation.

---

## 12. No-memory analysis

Phase 1 showed that some provenance scenarios aligned with the model's cautious
no-memory default. Phase 2 corrects for this prospectively: every scenario
carries a frozen `nomem_predicted` label, and only two controls are
intentionally default-aligned. For the core reversal pairs the gold action
should not simply equal the expected no-memory default.

The no-memory run answers two questions.

**Leakage.** Can the model infer the intended action from task context without
memory?

**Harm from wrong memory.** When a global policy produces an incorrect governing
state, is `wrong memory < no memory` in downstream task success? If reproduced,
this becomes a practically important result:

> An incorrect long-term state can be more harmful than having no long-term
> state.

This claim is reported only if Phase 2 data supports it.

---

## 13. Controls

Controls test that typed semantics do not win by construction: same source,
newer and more confident; lower-priority incoming source; verified operational
result; agreement / no-conflict cases.

Expected: `global policies ≈ B-Typed ≈ Oracle` on controls. Unexpected
separation triggers diagnosis before interpretation.

---

## 14. E2 support condition

The Phase 2 behavioral hypothesis is supported if:

1. `S>C>R` materially outperforms `S>R>C` on epistemic state;
2. `S>R>C` materially outperforms `S>C>R` on declared state;
3. B-Typed performs strongly on both;
4. controls remain approximately flat;
5. governing-state errors account for the relevant behavioral failures;
6. no-memory does not explain the interaction.

The claim is:

> **No single fixed confidence-versus-recency ordering was sufficient across the
> tested epistemic and declared state classes, and the resulting governing-state
> errors propagated into downstream agent decisions.**

The claim remains scoped to the tested state classes and tasks.

---

## 15. Refutation and weakening conditions

**R1 — One global policy behaves well across both classes.** Contradicts the
expected behavioral interaction even though E1 separated deterministically.
Interpretation: the downstream agent compensates for resolver errors.

**R2 — B-Typed does not outperform the complementary policies where they are
wrong.** The proposed typed semantics provide no measurable behavioral utility.

**R3 — Controls separate substantially.** The benchmark may encode unintended
advantages. Investigate before making the headline claim.

**R4 — No-memory matches or exceeds B-Typed on core scenarios.** The tasks do
not demonstrate useful memory dependence.

**R5 — Agent decision error dominates.** If correct governing states frequently
lead to wrong actions, resolver semantics are no longer the principal
experimental variable.

---

## 16. Analysis outputs

After the run freezes, produce `analysis/mode-b-phase2.md` containing:

**A.** E1 deterministic result — all fixed orderings and their resolution
outcomes.
**B.** E2 behavioral interaction — primary epistemic / declared / control table.
**C.** Pair-level analysis — for each reversal pair: same conflict geometry,
different state semantics, global policy outcome, typed policy outcome, agent
outcome.
**D.** Failure attribution — wrong governing state versus correct state / wrong
decision.
**E.** No-memory comparison, including whether wrong memory is measurably worse
than absent memory.
**F.** Limitations. At minimum: scenarios are controlled and author-designed;
confidence semantics are operationalized rather than universally canonical; the
declared/epistemic taxonomy is an analytical observation, not a TypedMem schema;
one agent model; five repetitions per cell; memory extraction is controlled
rather than end-to-end; the experiment does not establish that every state type
needs a custom policy.

---

## 17. What Phase 2 does not justify

Even if E2 fully supports the prediction, do not claim that all agent memory
requires TypedMem, that global resolution policies never work, that six state
types require six different policies, or that provenance authority is a unique
TypedMem contribution — Phase 1 already showed a strong fixed source ranking
sufficed for the tested provenance conflicts.

The narrower contribution is:

> **Heterogeneous state semantics can create incompatible requirements for a
> single global merge ordering.**

---

## 18. Decision after E2

If E2 supports the interaction: freeze the analysis; merge PR #5; do not
immediately add TypedMem features; decide whether one robustness experiment is
needed before paper drafting.

The next robustness experiment, if justified, should be **one** of: a second
model; additional independently authored scenarios; external scenario review;
controlled perturbation expansion. **Do not do all four automatically.**

If E2 does not support the interaction: preserve the result; do not expand Phase
2; reassess whether typed resolution deserves to remain the primary research
wedge.

---

## 19. Stop condition

The work ends when:

```text
comparative run complete
  → raw responses frozen
  → Phase 2 analysis written
  → result classified
```

No new TypedMem code, memory type, scenario family, or research question is
introduced before that point.

The purpose is not to make TypedMem look stronger. It is to answer one narrow
question:

> **Does the fixed-global-policy trade-off observed at the resolution layer
> survive contact with an actual agent?**

---

## Appendix — outcome of this design

Added after the run froze. The sections above are unedited; this appendix only
says where each registered condition landed. Numbers and their derivation are in
[`analysis/mode-b-phase2.md`](../analysis/mode-b-phase2.md).

**§14 support conditions — all six met.**

| # | Condition | Outcome |
|---|---|---|
| 1 | `S>C>R` > `S>R>C` on epistemic | 0.95 vs 0.28 |
| 2 | `S>R>C` > `S>C>R` on declared | 1.00 vs 0.00 |
| 3 | B-Typed strong on both | 0.97 / 1.00 |
| 4 | Controls approximately flat | 0.98 / 0.98 / 0.97 / 1.00 |
| 5 | Governing-state errors carry the failures | 103 of 112 memory-variant failures are `wrong_governing_state` |
| 6 | No-memory does not explain it | 0.52 / 0.30 / 0.43 |

**§11 stop condition — not triggered.** `correct_state_wrong_agent_decision` is
9 of 217 failures (≤ 0.03 on every class), below the 10% threshold. All nine are
degenerate-output runs; excluding them the interaction is exact — `S>C>R`
1.00/0.00, `S>R>C` 0.22/1.00, `b_typed` 1.00/1.00, controls 1.00.

**§15 refutation conditions — none fired.** R1–R5 all fail to trigger.

**Where the design's prediction and the data differ.** §6 predicts `S>R>C`
epistemic "incorrect". Governing-state resolution is indeed 0.00 — the policy
never selects the right state. But *task success* is 0.28, not 0.00: on roughly
a quarter of epistemic scenarios the agent recovers from a wrong governing
state, because the record's own hedge is visible in the payload and the task
survives acting on the hedge. The mirror error has no such rescue: `S>C>R` on
declared state is 0.00. The two errors are therefore asymmetric, and the
analysis records this rather than the design's symmetric prediction.

**Verdict:** BRQ2-narrow **SUPPORTED**. Per §18, the analysis is frozen and no
TypedMem feature follows. The next step is a single robustness run with a
stronger model configuration — one of the four options in §18, not all four.
