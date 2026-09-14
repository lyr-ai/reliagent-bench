# Mode B Phase 2 — Global Policy Stress Test

**Status:** Design (draft for review; semantics table frozen; no scenarios written, nothing run)
**Depends on:** [`analysis/mode-b-pilot.md`](../analysis/mode-b-pilot.md) — BRQ2 SUPPORTED on 4 typed scenarios; BRQ1 matched by a source ranking; BRQ3 inconclusive
**System under test:** TypedMem, frozen at `main @ 33d989e`. No TypedMem change in this phase.

## 1. The one question

Phase 1 showed, on four hand-built scenarios, that the global merge policy
`validity → source → confidence → recency` is right for two state types and
wrong for two, that the recency-only policy is the mirror image, and that the
agent acts on whichever governing state it is handed. The obvious objection:

> *You chose one unfavourable global ordering. Another ordering would have
> passed.*

Phase 2 answers it by measurement rather than argument. The per-type
semantics table
([`mode_b/semantics/phase2-types.md`](../src/reliagent_bench/memory/mode_b/semantics/phase2-types.md),
frozen before this section was rewritten) narrowed the question: every core
type shares the source guard, and the types differ only on whether
*confidence* also guards. So the question is not "which of many orderings
over three dimensions", but one axis:

> **For equally authoritative observations, should lower-confidence newer
> evidence replace existing state — and does the answer depend on the kind
> of state being represented?**

The table's answer, pre-registered: yes for *epistemic* state (a fact about
the world — confidence ranks, evidence is compared) and no for *declared*
state (a deadline, a commitment, an explicit preference — a valid revision
supersedes; confidence is an admission floor, not a rank). No fixed ordering
can satisfy both. Phase 2 exists to falsify that sentence.

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
and report governing-state accuracy **per state type and per state class**
(epistemic / declared). The informative contrast is `S→C→R` against
`S→R→C`; the other four permutations and the three single-dimension policies
are run anyway, so that "maybe another ordering works" is answered by
enumeration at zero cost. Single-dimension policies go to a secondary
table. The claim is supported if:

> no fixed ordering is correct on both state classes, while the per-type
> policy is; and the orderings that come closest split exactly on
> epistemic vs. declared state.

If some ordering *is* correct on both classes, the claim is refuted and the
paper says so. This is deterministic, takes seconds, and runs **before** any
agent call.

### E2 — Agent-stage confirmation on the reversal pairs

For the orderings that E1 shows are complementary — the best-performing
global ordering and its mirror — run the agent stage on the scenario set,
five runs each, with `b_typed`, `oracle`, and `nomem`. Success: the same
interaction pattern in task success as in governing-state accuracy, with
`correct_state_wrong_agent_decision` staying near zero.

## 3. Scenario design: balanced matrix, reversal pairs

Not a full factorial. Each scenario is one cell of

```text
state type      factual state · deadline · commitment · explicit preference / constraint   (core, from the table)
                verified operational result (consistency cases only) · inferred trait (exploratory only)
source relation equal (main experiment) · higher / lower (consistency cases)
confidence      incoming lower, ≥ 0.5 (main) · equal / higher (controls)
recency         incoming newer (always — a write that describes an older state is the
                effective_from case and is held out as its own small block)
domain          scheduling · deployment/CI · personal data · procurement · communications
perturbation    entity names, dates, wording, order of memories in the payload
```

**Reversal pairs are the unit.** The main experiment holds the pattern
constant and varies only the state semantics:

```text
held fixed      source(incoming) = source(existing)
                incoming newer
                incoming confidence lower, but ≥ 0.5 (the admission floor, table §3.1)
varied          state class: epistemic (fact · verified result) vs declared (deadline · commitment · explicit preference)
```

```text
FACT        earlier, .9  "The service currently uses PostgreSQL."
            later,   .6  "Looks like it might be MySQL now."              → PostgreSQL stands
DEADLINE    earlier, .9  "Review deadline is Friday the 18th."
            later,   .6  "Monday, actually."  (in the same thread)         → Monday
```

The lower confidence on the revision must be *earned by the text* — terse,
elliptical, context-dependent phrasing — never stipulated by a number alone.
That is the reviewer's first attack and it is closed at scenario-writing
time, per pair.

Source-only conflicts (incoming lower or higher priority) are kept as
consistency cases: every type resolves them the same way, so they cannot
form reversal pairs, and they re-confirm BRQ1/F3 that a source ranking
suffices. The `effective_from` case is a small held-out block for the same
reason.

Declared semantics per type are frozen in the table, with the argument for
each, before any scenario. They are the contract under test and are argued
without reference to TypedMem. Reversal pairs are derived from the table's
rows, not the other way round.

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
