# Mode B Phase 2 — Global Policy Stress Test

**Status:** Design (draft for review; no scenarios written, nothing run)
**Depends on:** [`analysis/mode-b-pilot.md`](../analysis/mode-b-pilot.md) — BRQ2 SUPPORTED on 4 typed scenarios; BRQ1 matched by a source ranking; BRQ3 inconclusive
**System under test:** TypedMem, frozen at `main @ 33d989e`. No TypedMem change in this phase.

## 1. The one question

Phase 1 showed, on four hand-built scenarios, that the global merge policy
`validity → source → confidence → recency` is right for two state types and
wrong for two, that the recency-only policy is the mirror image, and that the
agent acts on whichever governing state it is handed. The obvious objection:

> *You chose one unfavourable global ordering. Another ordering would have
> passed.*

Phase 2 answers it by measurement rather than argument:

> **Does any single fixed global merge policy dominate across heterogeneous
> state types — and does the variant × state-type interaction hold under
> systematic perturbation, across domains, and through agent behaviour?**

Nothing else is added. BRQ1 is closed for this phase (a source ranking
suffices; that is the paper's statement). BRQ3 is deferred (Family C needs
execution-grounded tasks; separate design).

## 2. Two experiments

### E1 — Exhaustive fixed-ordering evaluation (resolution stage, no model)

Enumerate every fixed global ordering over the three comparable dimensions
plus validity-first as a constant prefix:

```text
dimensions      source priority (S) · confidence (C) · recency (R)
orderings       all 6 permutations of (S, C, R), each preceded by validity
                + 3 single-dimension policies (S only, C only, R only)
                + newest-wins (b0) and bitemporal-latest-valid (b_scd) as before
```

Run each ordering as a resolution variant over the full Phase 2 scenario set
and report governing-state accuracy **per state type**. The claim is
supported if:

> no ordering is correct on every state type, while the per-type policy is.

If some ordering *is* correct everywhere, the claim is refuted and the paper
says so: heterogeneous semantics on these types are expressible as one
global order. This is cheap (deterministic, seconds) and is run **before**
any agent call.

### E2 — Agent-stage confirmation on the reversal pairs

For the orderings that E1 shows are complementary — the best-performing
global ordering and its mirror — run the agent stage on the scenario set,
five runs each, with `b_typed`, `oracle`, and `nomem`. Success: the same
interaction pattern in task success as in governing-state accuracy, with
`correct_state_wrong_agent_decision` staying near zero.

## 3. Scenario design: balanced matrix, reversal pairs

Not a full factorial. Each scenario is one cell of

```text
state type      fact · preference · deadline · commitment · operational_constraint · verification_status
                (six; the four from Phase 1 plus the two that appeared in the provenance family)
source relation incoming source higher / equal / lower priority than existing
confidence      incoming higher / equal / lower
recency         incoming newer (always — a write that describes an older state is the
                effective_from case and is held out as its own small block)
domain          scheduling · deployment/CI · personal data · procurement · communications
perturbation    entity names, dates, wording, order of memories in the payload
```

**Reversal pairs are the unit.** A pair is two scenarios with the *same*
(source, confidence, recency) pattern and different state types whose
declared semantics disagree about who wins:

```text
pair 1   equal source, lower confidence, newer     fact → existing wins · commitment → incoming wins
pair 2   lower source, higher confidence, newer    fact → existing wins · deadline → incoming wins
pair 3   equal source, equal confidence, newer     preference → incoming · verification_status → ? (declared per case)
```

Every fixed global ordering must lose one side of every pair it faces. The
per-type policy must not. Target: **12 reversal pairs × 2 surface
perturbations = 48 scenarios**, plus 12 controls where the two types agree,
so a variant that "just picks per-type" cannot win by construction.

Declared semantics per type are written down **before** any scenario, in one
table, with the argument for each (a deadline is time-bound state; a fact is
provenance-bound; a commitment is the user's latest explicit position; …).
They are the contract under test and must be defensible without reference to
TypedMem.

## 4. What stays fixed from Phase 1

Prompt `mode-b-pilot-0`; model `claude-sonnet-5`, thinking off, effort low,
five runs; schema-constrained action; the oracle gate (≥ 0.95 overall, no
family < 0.90) on the new set before any comparison; attribution rules;
pre-registered predictions per ordering and per state type, committed before
E1 runs.

## 5. Two corrections to carry from Phase 1

- **Gold must not coincide with the model's default.** Every scenario's
  no-memory action is predicted in advance; a scenario whose gold equals the
  predicted default is redesigned or labelled `default-aligned` and reported
  separately. Phase 1's provenance family failed this.
- **Task context must not solve the task.** Same rule as design §11; Phase 1's
  Family C failed it. A `nomem` run on the new set is the check: nomem
  success above chance on a scenario means the context leaks, and the
  scenario is flagged before the comparative run.

## 6. Deliverables

```text
docs/mode-b-phase2-global-policy-stress-test.md      this document
mode_b/semantics/phase2-types.md                      the per-type contract, argued
mode_b/tasks/phase2.json                              48 + 12 scenarios
mode_b/predictions/phase2.json                        per ordering × state type, before E1
mode_b/results/phase2-e1.*                            exhaustive orderings, resolution stage
mode_b/results/phase2-e2.*                            agent stage on the complementary pair
analysis/mode-b-phase2.md                             one verdict: does any fixed ordering dominate?
```

## 7. Stop conditions

Stop and report if E1 finds a dominating fixed ordering; if the oracle gate
fails on the new set; if `nomem` solves more than a quarter of non-control
scenarios; or if E2's `correct_state_wrong_agent_decision` exceeds 10% of
failures (the agent has started second-guessing the payload, and the
resolution stage no longer explains behaviour). None of these is answered by
adding mechanisms.
