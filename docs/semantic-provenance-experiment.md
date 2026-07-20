# Experiment — Operational vs. Semantic Provenance for Failure Localization

**Track:** C — Semantic provenance
**Status:** Experimental design + preliminary findings (single-annotator, synthetic)
**Plan of record:** [`semantic-provenance-plan.md`](semantic-provenance-plan.md)

This is a concrete run of the Track-C question. It is representation-neutral: a
*semantic provenance representation* is under evaluation, with
[StateGraph](https://github.com/canis-minor/stategraph) as the **reference
implementation** — one candidate, not the benchmark.

---

## Objective

Evaluate whether semantic provenance provides debugging information beyond an
operational execution trace. The goal is **not** to show a semantic representation
catches every failure — it is to identify *which classes* of failure benefit from
semantic representation and which are already adequately explained operationally.

## Research question

Can semantic provenance help a developer localize the root cause of an agent failure
more effectively than an operational trace alone?

## Setup

Each failure is represented twice, over the same underlying run:

- **A — Operational trace.** Execution events only: observations, tool calls, model
  outputs, decisions. (The Track-B / [AgentTrace](https://github.com/canis-minor/agenttrace) baseline.)
- **B — Semantic provenance.** Observations, current state, supporting evidence,
  superseded evidence, decision dependencies, semantic warnings. (Reference
  implementation: StateGraph.)

## Evaluation strategy

For every injected failure, ask three questions — emphasis on **root-cause
localization**, not anomaly detection:

1. Can the operational trace detect something is wrong?
2. Can the operational trace explain *why*?
3. Can the semantic representation explain *why*?

---

## Failure categories

| ID | Failure | Operational trace | Semantic representation |
|---|---|---|---|
| **F1** | **Unsupported state** — a conclusion with no supporting evidence | may show missing retrieval; does not name the unsupported state | active claim with no supporting observation |
| **F3** | **Ignored contradiction** — conflicting evidence, no contradiction represented | shows the conflicting observations; can't say if it was ignored, resolved, or never interpreted | explicit *unregistered* contradiction |
| **F4** | **Stale evidence preferred** — contradiction detected, older evidence stays active | identical to the correct run; resolution policy invisible | older evidence remained active despite newer contradicting evidence |
| **F5** | **State never updated** — contradiction registered, state never transitions | shows conflicting observations; can't reveal whether state updated | decision still depends on a disputed claim |
| **F6** | **Decision on superseded state** — state updated correctly, action correct, but the decision still cites an obsolete claim | **no anomaly** — tool calls and final action match the correct run | decision depends on a superseded semantic state |

*F4 is treated as a semantic **policy** issue, not a structural invariant violation —
a deliberate honesty check on the invariant's reach (the invariant can't catch it; only
inspecting the resolution strategy can).*

These cases are runnable today: StateGraph's `examples/certificate/experiment.py`
(all five) and this repo's SP-001 (the F6 case).

---

## Preliminary findings — three categories

1. **Unsupported state (F1).** Semantic provenance exposes a belief with no grounding.
2. **Incorrect outcome (F3, F4, F5).** The operational trace shows the outcome is wrong
   but not *which* semantic cause — ignored contradiction vs. stale resolution vs.
   un-updated state. These demand *different fixes* despite similar operational
   symptoms; the semantic representation separates them.
3. **Correct outcome (F6).** The strongest separation. Identical execution, identical
   final action — the *only* difference is the justification. Operational tracing cannot
   distinguish the flawed run from the correct one; the semantic representation exposes
   the invalid dependency.

## Interpretation

Operational provenance answers *what happened?*; semantic provenance answers *why is
this decision currently justified?* They overlap but are not identical. Semantic
provenance is most valuable when a developer must inspect **belief evolution** rather
than execution history.

## Limitations (honest)

Evaluates: explicitly-constructed representations, synthetic failures, a single
ontology. Does **not** yet measure: human debugging time, inter-annotator agreement,
automatic extraction, or comparison across alternative semantic representations. SP-001
was annotated by a single annotator — *not* a valid reproducibility measurement. These
are the planned Track-C studies.

## Conclusions

This does **not** argue operational traces are insufficient. It argues the two are
**complementary**: operational traces reveal execution history; semantic provenance
explains belief evolution and decision justification. The strongest evidence appears
where **multiple semantic causes produce similar operational traces** (F3/F4/F5) or
**the output is correct while the justification is invalid** (F6).

## Next experiments

Human debugging studies · ontology reduction · alternative semantic representations ·
larger suites · comparison across multiple semantic-representation systems. The
benchmark stays representation-neutral; StateGraph remains one implementation under
evaluation, not the benchmark.
