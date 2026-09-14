# TypedMem Mode B — End-to-End Agent Utility Evaluation

**Status:** Design — contract for Phase 1
**Phase:** Mode A diagnostic complete → external validation complete → end-task utility
**Depends on:** [`analysis/mode-a-pilot.md`](../analysis/mode-a-pilot.md) · [`analysis/external-validation.md`](../analysis/external-validation.md) · [`docs/typedmem-external-validation.md`](typedmem-external-validation.md)
**System under test:** TypedMem · **Harness:** ReliAgent Bench
**Implementation:** `src/reliagent_bench/memory/mode_b/`

## 1. Motivation

Mode A established mechanism-level findings under controlled writes. External
validation then established that conventional bitemporal state is sufficient
for the temporal-update cases in existing benchmarks; that TypedMem's
`replace` loses queryable history on externally designed history-dependent
tasks; and that existing benchmarks do not meaningfully test
provenance-dependent state transitions or type-dependent resolution. Those two
untested dimensions are the reason for Mode B.

Mode B asks a different question from Mode A:

> **Do provenance-aware and type-dependent memory semantics improve what an
> agent actually does?**

Not retrieval accuracy, not memory QA accuracy — downstream behaviour: does
the agent follow the correct current constraint; avoid repeating an observed
failure; act on an explicit instruction over a newer inference; treat a
deadline update differently from an uncertain biographical inference; need
fewer corrective iterations.

## 2. Research questions

- **BRQ1 — Does provenance-aware resolution reduce downstream decision
  errors?** With conflicting memories from sources of different authority,
  does provenance-aware state resolution reduce incorrect decisions compared
  with recency-only, bitemporal, and bitemporal-plus-one-global-guard state?
  The outcome is not whether the store holds the right record; it is whether
  the agent made the right decision *because the correct observation governed
  state*.
- **BRQ2 — Do type-dependent update semantics improve task behaviour over one
  global merge rule?** For structurally similar updates on different state
  types — deadline / commitment, explicit preference, inferred trait,
  verified failure lesson, current fact — does one global policy fail
  systematically, and does that change task success?
- **BRQ3 — Does memory of prior failure reduce repeated failure?** For tasks
  where the agent previously failed through a known strategy, does a memory
  of that failure reduce recurrence on a related, non-identical task?
  Primary metric: **Repeated Failure Rate** = known failure patterns repeated
  ÷ opportunities to repeat them. Externally motivated by practitioner
  memories of the form *"Do not do X under condition C. Do Y instead."*

## 3. Non-goals

Mode B does not attempt to show that TypedMem is a universal memory
architecture; that temporal validity is novel; that source-priority systems
are unique to agent memory; that all tasks require typed resolution; or that
more memory always helps. It does not evaluate compaction, policy migration,
replay, storage, retrieval latency, extraction quality in general, or every
TypedMem type. **No TypedMem feature is added during the frozen experiment.**

## 4. Experimental principle

```text
observation → memory extraction / normalisation → state resolution → agent decision / action
```

Mode B is about the last two stages. Extraction is controlled, not studied:
every variant receives the same normalised candidate memories; model, prompt,
tools, task and retrieved evidence are fixed; only state-resolution semantics
vary. An extraction-mediated run may be added later.

## 5. Two tracks

**Track B1 — controlled decision tasks (primary).** Writes are constructed
deterministically; the agent receives the *resolved* memory state and must act.
The memory system determines governing state; the agent determines the action.

**Track B2 — repeated-failure tasks (secondary).** The agent fails a task via
a known strategy; the outcome becomes a memory; a related, non-identical task
follows. Measured: does the agent repeat the strategy?

## 6. Variant ladder

| variant | semantics |
|---|---|
| **B0** | latest observation wins |
| **B-SCD** | bitemporal history, no authority, one global merge rule |
| **B-SCD-G** | bitemporal history + one global source-priority / confidence guard |
| **B-Typed** | provenance-aware, type-dependent resolution (TypedMem) |
| **B-Oracle** | governing state supplied by hand; the upper bound of downstream performance, not a competing system |

B-Oracle answers: if resolution were perfect, how often would the agent still
decide wrongly?

## 7. B-SCD-G must be strong

A structured state system may have source, confidence, source priority,
validity and one declared global merge function. B-SCD-G gets one reasonable
global policy, frozen before execution — e.g. *validity first, then source
priority, then confidence, then recency*. The question is not whether
TypedMem beats a naïve table; it is **whether one global merge rule can
express heterogeneous agent-state semantics without helping one class and
hurting another.**

## 8. Scenario families

Target 24–36 base scenarios with controlled perturbations.

**Family A — provenance conflict (8–10).** A1 explicit instruction vs
inferred behaviour ("do not email customers without approval" vs an inference
that approval is unnecessary; task: send an update; correct: request
approval). A2 explicit preference vs behavioural inference (aisle seats vs
recent window bookings; correct: aisle). A3 verified external result vs model
inference (CI says 3.12 failing vs "probably transient"; correct: do not
merge) — introduces `verified_result` as provenance without changing
TypedMem's hierarchy.

**Family B — same update pattern, different state semantics (8–10).** B1
deadline Friday → Monday (newer replaces). B2 explicit "lives in San Jose" →
inferred "probably Seattle" (inference does not override). B3 commitment "I
will not use X" → "I changed my mind — use X" (older high-authority statement
must not dominate). B4 inferred trait with mixed later evidence (retain
uncertainty) — only if gold can be defined independently of TypedMem.

**Family C — repeated failure / superseded strategy (8–12).** Each has a
training episode, a failure, a correction, a memory, and a transfer episode
that changes names and domain but keeps structure. C1 editing a generated
file (edit the source and regenerate). C2 calling a deprecated endpoint (use
the migration wrapper). C3 modifying global state for one test (use a
fixture). C4 deploying code before its migration (migration first). The goal
is transfer beyond string matching, not hard coding tasks.

## 9. Negative controls

At least 20–25% of scenarios: no conflict; newer and older agree; same source
and confidence; memory irrelevant to the task; remembered failure does not
apply in the new context; two types that happen to need the same rule.
TypedMem should not win everywhere; a variant that applies old memories too
aggressively is penalised — *avoiding X is wrong when the condition that made
X fail is absent.*

## 10. Scenario schema

Each scenario separates task, memory observations, state semantics,
agent-visible context, gold action, mechanism label. Variants never see gold.

```yaml
id: authority_task_001
family: provenance_conflict
task: {instruction: "Schedule the production deployment.", choices: [Thursday, Friday]}
memories:
  - {content: "Do not deploy production on Friday.", source_type: explicit_user, authority: high, confidence: 1.0}
  - {content: "Friday deployments appear acceptable.", source_type: model_inference, authority: low, confidence: 0.95}
state_type: operational_constraint
gold: {governing_state: "Do not deploy production on Friday.", action: Thursday}
mechanism: authority_conflict
negative_control: false
```

## 11. Task generation rules

Task wording must not reveal the memory rule. Not *"the user explicitly told
you not to deploy Friday"*; rather *"Thursday and Friday are both available"*.
The relevant state comes from memory. A repeated-failure task must not say
*"remember that editing generated files failed"*.

## 12. Agent model and interface

One primary model, fixed version, low or zero temperature; model is not a
research variable. N ≥ 5 repetitions per scenario × variant if stochastic. The
model receives system task instructions, the resolved memory payload, task
context, and available actions; prompt structure is identical across variants
— only the memory payload changes. Constrained output `{"action", "reason"}`;
score the action.

## 13. Metrics

Primary: **task success rate**; **governing-state decision accuracy**
(decisions consistent with the correct governing state ÷ eligible decisions);
**repeated failure rate** (Family C); **violation rate** (explicit
constraints / preferences); **corrective iterations** (mean and distribution,
never collapsed into success). Secondary where meaningful: tool calls, tokens,
latency, unnecessary clarification, regressions, unsafe attempts.

**Attribution — every failure gets one primary diagnosis:**
`memory_not_retrieved · wrong_governing_state · correct_state_wrong_agent_decision ·
overgeneralized_failure_memory · extraction_error · task_ambiguity · other`.
If B-Typed resolves the correct state and the agent ignores it, that is not
evidence against the semantics.

## 14. Predictions

Committed before comparative runs. Family A: B0 low, B-SCD low/medium,
B-SCD-G medium, B-Typed high — only where source entitlement matters. Family
B: B-SCD-G improves the types matching its rule and regresses the others;
B-Typed improves aggregate without sacrificing subtypes; the critical result
is the **variant × state_type interaction**, not the aggregate. Family C: no
useful memory → repetition common; applicable corrected memory → repetition
falls; typed resolution matters only where superseded strategy memories
conflict — do not claim Family C proves typed resolution unless resolution
semantics are actually varied.

## 15. Phase 1 pilot

```text
4 provenance · 4 type-dependent · 4 repeated-failure · 4 negative controls = 16
variants: B0, B-SCD, B-SCD-G, B-Typed, B-Oracle
stochastic: 5 runs × 16 × 5 = 400 agent runs
```

**Success criteria:** at least one BRQ shows separation in the predicted
direction; failures concentrated in the relevant mechanism; controls flat;
B-Oracle shows the tasks are solvable; resolution improvements survive agent
noise. If B-Oracle is poor, redesign the task before interpreting anything.

## 16. Falsification cases

**F1** agents ignore memory semantics (all variants similar despite different
governing state). **F2** the global policy is enough (B-SCD-G ≈ B-Typed
across types). **F3** authority adds no utility (B-SCD-G with source priority
≈ B-Typed). **F4** failure memory overgeneralises (fewer repeats, more false
avoidance on controls). Each is a meaningful negative result.

## 17. Relationship to external benchmarks and practice

Existing benchmarks test recall, temporal updating, historical state, speaker
attribution; not provenance-dependent governing state or type-dependent
merge. Mode B fills that gap; it does not replace them. LoCoMo's speaker-swap
is external motivation for *attribution* provenance and stays distinct from
*authority* provenance. Practitioner reports — supersession pointers,
different treatment by memory class, hand-recorded failure lessons, links
from invalidated reasoning to corrections — motivate the families and are not
evidence.

## 18. Freeze rules

Before the first comparative run: scenarios, gold actions, state-type
semantics, the B-SCD-G policy, prompts, model version, the prediction file,
tested scoring, identified controls, and the TypedMem commit are all frozen.
After it: **no scenario is removed because TypedMem fails it.** A benchmark
error may be corrected only with a documented reason independent of system
outcome, preserving the previous result.

## 19. Layout and deliverables

```text
src/reliagent_bench/memory/mode_b/   schema.py · runner.py · agent.py · scoring.py
                                     variants/{b0,b_scd,b_scd_g,b_typed,oracle}.py
                                     tasks/{provenance,typed_resolution,repeated_failure,controls}.json
                                     predictions/pilot.json · results/pilot-0.json
analysis/mode-b-pilot.md
```

Shared schema and scoring are fine; shared resolver implementations are not.
The analysis answers BRQ1–3 with exactly one of
`SUPPORTED / NOT SUPPORTED / INCONCLUSIVE`.

## 20. Expansion, TypedMem, paper, stop

Expand beyond 16 only on measurable downstream signal. TypedMem stays frozen;
a reproducible failure with clear downstream cost becomes an issue after the
analysis is frozen (evaluation → analysis → issue → design), never a patch
and rerun. The paper strengthens if Mode A separates mechanisms, external
benchmarks confirm the temporal baseline and expose coverage limits, Mode B
shows at least one semantics changes downstream behaviour, controls stay
flat, and limitations are reported. **Stop** if the pilot shows no downstream
separation, B-Oracle shows the tasks are not solvable, effects come from
prompt or extraction noise, or a global structured baseline matches TypedMem
everywhere. Do not respond by inventing mechanisms. If the answer to *"do the
Mode A differences matter to what an agent does?"* is no, that is the result.
