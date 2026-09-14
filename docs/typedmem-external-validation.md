# TypedMem External Validation

**Status:** Design
**Phase:** Mode A diagnostic complete → external validation
**Depends on:** [`analysis/mode-a-pilot.md`](../analysis/mode-a-pilot.md)
**System under test:** TypedMem
**Evaluation harness:** ReliAgent Bench
**Candidates and screening:** [`external/triage/candidates.md`](../external/triage/candidates.md)

---

## 1. Motivation

The Mode A diagnostic established that the harness can isolate several
state-management mechanisms under controlled conditions. Across 42 scenarios
and 73 frozen query-level predictions it produced three preliminary findings:

1. **Bitemporal representation was sufficient for the temporal-state cases
   tested.**
2. **A universal confidence guard improved memory types whose semantics
   matched it while degrading types governed by different update semantics.**
3. **Confidence and provenance authority were empirically non-substitutable
   in the tested conflict cases.**

It also exposed cases where a simpler structured baseline outperformed
TypedMem, particularly when the desired semantics were *retain history, but
prevent a weaker observation from becoming the governing current state*.

These are useful diagnostics. They are not external evidence: the scenarios
and TypedMem were designed by the same author. The next question is

> **Do the findings survive on tasks that were not designed around TypedMem's
> abstractions?**

This phase tests external validity before adding TypedMem mechanisms or
beginning a larger end-to-end agent study.

## 2. Goal

Select one or two existing long-term-memory or multi-session benchmarks and
determine whether they contain enough naturally occurring state-change
structure to test the Mode A findings.

The goal is **not** the highest overall score. It is to test whether
externally designed tasks contain evidence consistent or inconsistent with the
diagnostic findings. The external benchmark stays externally defined:

- do not rewrite tasks to make them exercise TypedMem;
- do not change gold labels;
- do not discard inconvenient examples;
- do not tune TypedMem policy per example;
- do not introduce TypedMem functionality during evaluation.

## 3. Research questions

### ERQ1 — Temporal state

On externally designed tasks involving state change over time, does a
structured bitemporal representation perform similarly to TypedMem? Tests
whether *bitemporal representation is sufficient* survives outside the custom
benchmark. Expected: `V0 < V0-SCD ≈ V4` on genuinely temporal state-update
cases. A result where V4 substantially exceeds V0-SCD must be inspected before
being read as a TypedMem contribution — the difference may come from
provenance, confidence, typed semantics, retrieval, or the adapter.

### ERQ2 — Provenance-dependent state updates

Do external tasks contain conflicts where the correctness of a transition
depends on the *source* of the incoming observation rather than its recency
or confidence — explicit statement vs. inferred state, explicit correction
vs. previous inference, authoritative external state vs. behavioural
inference, verified outcome vs. model-generated belief? If so, compare
`V0-SCD-G` vs `V4`. The question is not the aggregate score; it is whether
provenance prevents specific incorrect transitions that validity and
confidence alone do not.

### ERQ3 — Type-dependent update semantics

Do external tasks contain structurally similar updates whose correct
resolution differs by the semantic type of state — durable facts,
preferences, commitments, deadlines, plans, inferred traits? If so, test
whether one global guard can express the required semantics without helping
one class while hurting another. **Evaluated only if the dataset naturally
contains such variation. Do not manufacture type distinctions after seeing
results.**

## 4. Non-goals

Not evaluated in this phase: replay or policy migration; event-log
compaction; materialised-state rebuild; automatic validity-window closing;
retrieval quality as an independent question; long-history performance or
storage; full agent task utility; repeated-failure rate; memory extraction
quality. Those belong to later phases.

> **No TypedMem feature is added to improve an external benchmark result.**
> If an external task exposes a limitation, record it. Do not fix it during
> this phase.

## 5. Benchmark-selection criteria

| criterion | question |
|---|---|
| multi-session | does information evolve across interactions or episodes? |
| state updates | can a previously correct state become outdated? |
| temporal queries | are there current-state or historical / as-of questions? |
| contradictions | can multiple memories disagree? |
| provenance | can the source of information be distinguished? |
| semantic types | are multiple forms of state represented? |
| raw history | can the original sequence of observations be reconstructed? |
| gold answers | are expected outcomes externally supplied? |
| adapter feasibility | can all variants receive equivalent information? |
| licence / reproducibility | can the evaluation be reproduced publicly? |

A benchmark with high ordinary-QA coverage but no state transitions is not
useful for this phase.

## 6. Benchmark triage

Before implementing an adapter, inspect candidates manually. For each: read
the paper and documentation; inspect at least 30 examples; classify each as

```text
static_recall · temporal_update · historical_state · provenance_conflict ·
type_dependent_update · contradiction_without_resolution · other
```

and record whether the original data contains enough information to construct
the relevant state **without inventing metadata**. Produce
`external/triage/<benchmark>.json` with counts and representative example
ids. Do not build an adapter until triage shows meaningful overlap.

## 7. Minimum overlap requirement

A benchmark qualifies for the main experiment if the inspected sample
suggests at least **10 temporal / state-update examples** and at least one of
**5 provenance-sensitive** or **5 naturally type-dependent** examples. These
are screening rules, not statistical guarantees.

If no benchmark satisfies them, that is a result: *existing long-term-memory
benchmarks may evaluate recall without sufficiently evaluating
state-transition semantics.* Do not force an unsuitable benchmark into the
paper. Proceed to Mode B.

## 8. Preserve the external task

The benchmark defines conversations / history, query, gold answer, episode
boundaries, ordering. ReliAgent Bench may derive a normalised intermediate
representation, but the original example stays traceable. Every normalised
example stores:

```text
benchmark · original_example_id · original_input_hash · normalization_version
derived_state_writes · query · external_gold
```

Every derived field records whether it was `explicit`,
`deterministically_derived`, or `model_inferred`. Externally absent
authority or validity metadata must not silently become TypedMem-specific
gold.

## 9. Two tracks

**Track E-A — deterministic normalisation.** When state writes can be derived
from the benchmark without an LLM deciding their meaning (*"I live in San
Jose"* → *"I moved to Seattle last month"*). Closest to Mode A; preferred for
mechanism attribution.

**Track E-B — extraction-mediated normalisation.** Only when E-A is
impossible: `external conversation → fixed extractor → normalised writes →
variant → external query`. The same extracted writes go to every variant;
extraction is frozen before comparative results are inspected; extraction
failures are reported separately and never counted as evidence against a
state resolver.

## 10. Variants

| variant | purpose |
|---|---|
| V0 | weak memory-as-records reference |
| V0-SCD | structured temporal baseline |
| V0-SCD-G | structured temporal + universal confidence guard |
| V4 TypedMem | provenance-aware typed state resolution |

Do not add V1–V3 merely to make a larger table. Add an intermediate variant
only if the external data contains enough examples to answer a specific
attribution question these four cannot.

## 11. Retrieval control

For mechanism-sensitive subsets, hold candidate retrieval constant. If the
benchmark requires retrieval over a long history, report two results
separately and never mix them: **oracle-candidate** (relevant memories
supplied; measures state resolution) and **native-retrieval** (each system
retrieves; measures the combined pipeline). The primary validation for the
current claims is oracle-candidate / state-level.

## 12. External labels

Never replace external gold with TypedMem-derived labels. Add only analysis
annotations — `external_category`, `candidate_mechanism`,
`provenance_available`, `temporal_structure`, `state_type` — which are not
correctness labels. Subset definitions are frozen before variant comparison.

## 13. Metrics

- **External answer accuracy**, overall and by frozen subset.
- **Pairwise delta** per subset: `V4 − V0-SCD`, `V4 − V0-SCD-G`. The delta
  matters more than V4's standalone score.
- **Transition-error attribution** for every incorrect example:
  `retrieval · normalization/extraction · temporal_resolution ·
  authority_resolution · type_resolution · unsupported_semantics ·
  answer_generation · ambiguous_gold`. Required. An aggregate score without
  attribution is insufficient.

## 14. Predictions before execution

`external/predictions/<benchmark>.json`, at subset level, before any
comparative run — e.g. `temporal_update: "V0-SCD approximately matches V4"`,
`provenance_conflict: "V4 > V0-SCD-G"`, `static_recall: "no meaningful
separation"`. If a benchmark has no provenance-sensitive cases, record
`provenance_conflict: "not testable"`. An untestable question is not a
negative result.

## 15. Negative controls

External static-recall cases are natural negative controls. Where there is no
state change, no contradiction, no temporal ambiguity and no provenance
conflict, V4 should show no systematic mechanism-level advantage. Unexpected
separation on static controls triggers adapter inspection before
interpretation.

## 16. Success conditions

External validation succeeds if at least one Mode A finding survives on
externally designed examples without contradicting the others. Strong:
`temporal V0-SCD ≈ V4 · authority V4 > V0-SCD-G · typed V4 > global-rule
baseline · controls flat`. A useful partial outcome: the temporal finding
survives; authority and type are not testable in available benchmarks — which
motivates Mode B specifically around the missing dimensions.

## 17. Failure conditions

- **F1 — a finding does not replicate** (e.g. V0-SCD substantially
  outperforms V4 on temporal cases): investigate; modify neither the
  benchmark nor TypedMem during the phase.
- **F2 — no benchmark tests the mechanism**: document the coverage gap. Not
  evidence for TypedMem; evidence that external validation needs a different
  design.
- **F3 — the adapter dominates**: if normalisation or extraction errors
  explain most failures, the benchmark cannot currently validate state
  semantics. Say so.
- **F4 — all variants similar**: state semantics may not matter on these
  tasks; the tasks may be easy; the benchmark may not exercise transitions;
  or the findings may not generalise. Use failure attribution before
  choosing.

## 18. No benchmark shopping

List candidates; record criteria; triage; select at most two by overlap;
**freeze the selection**. A selected benchmark that produces a negative
result is kept.

## 19. Execution sequence

1. **Search** — 5–8 candidates across long-term conversational memory,
   multi-session memory, temporal memory, memory updates / contradictions,
   personalised agents.
2. **Triage** — ≥ 30 examples from each serious candidate; coverage table.
3. **Select** — at most two; freeze before running variants.
4. **Adapter** — deterministic normalisation first; extraction only where
   unavoidable.
5. **Freeze** — commit normalised examples, subset annotations and the
   prediction file before comparative execution.
6. **Run** — V0, V0-SCD, V0-SCD-G, V4.
7. **Analyse** — overall, subset, pairwise deltas, failure attribution, and
   per Mode A finding: `SURVIVED / CONTRADICTED / NOT TESTABLE`.
8. **Decide** — external evidence sufficient → paper experiment plan;
   coverage incomplete → Mode B targeted evaluation; Mode A contradicted →
   investigate before further development.

## 20. Relationship to Mode B

Mode A asks: given correct observations, does the state system resolve them
correctly? External validation asks: do those findings survive on tasks we
did not design? Mode B asks: does improved memory state improve an agent's
behaviour? Candidate Mode B metrics: task success; **repeated failure rate**;
instruction / preference violations; unnecessary clarification; corrective
iterations; regressions introduced; steps; latency and cost. Mode B begins
only after external validation establishes which mechanism-level claims still
need end-to-end evidence.

## 21. Freeze rule

> **The benchmark may reveal a reason to change TypedMem, but it may not
> cause TypedMem to change until the external result is frozen and written
> down.**

A discovered limitation becomes `result → analysis → issue → later design
decision`, never `failing example → patch → rerun until green`. This is the
external equivalent of preserving the known-gap failures in Mode A.

## 22. Deliverables

```text
docs/typedmem-external-validation.md        this document
external/triage/                             candidates.md, then <benchmark>.json per inspected benchmark
external/normalized/
external/predictions/
external/results/
analysis/external-validation.md
```

The analysis concludes, for each Mode A finding, exactly one of
`SURVIVED`, `CONTRADICTED`, `NOT TESTABLE`. No fourth category is added after
seeing results.

## 23. Stop condition

Stop after at most two selected benchmarks have been evaluated, or when
triage shows that existing benchmarks do not expose the mechanisms. Do not
turn benchmark search into an indefinite attempt to find favourable
evidence. If external data validates the temporal finding but cannot test
provenance or type-dependent resolution, Mode B is designed around those two
questions. If external data contradicts Mode A, investigate before expanding
TypedMem.

The purpose of this phase is not to confirm the project. It is to determine
which of its current claims survive contact with data the project did not
design.
