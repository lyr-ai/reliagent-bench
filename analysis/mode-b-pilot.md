# Mode B pilot — analysis

**Scope:** Phase 1 of [`docs/mode-b-design.md`](../docs/mode-b-design.md):
16 scenarios, six variants, one fixed model, five runs. Everything upstream
of the agent stage — scenarios, gold, type semantics, the B-SCD-G policy,
the prompt, the predictions, the verdict rules — was frozen in
`src/reliagent_bench/memory/mode_b/` before the comparative run.
**Status:** frozen. No TypedMem change; no scenario added or removed after a
result was seen.

## 1. Question

Do the state-resolution differences measured in Mode A and reproduced
externally reach *behaviour*: when a memory system puts a different memory
in charge of a slot, does an agent given that resolved state act
differently?

## 2. Setup

- **Model:** `claude-sonnet-5`, the exact id the account's model list
  returns. This model generation has no `temperature` / `top_p` parameters,
  so "temperature 0" is not requestable; the lowest-variance configuration
  was used — thinking disabled, effort low — and run-to-run variance is
  carried by five repetitions and reported as counts. The action is
  constrained to the task's choices by a JSON schema on the response, so no
  off-list action can occur.
- **Prompt:** `mode-b-pilot-0`, identical for every variant; only the
  "Resolved memory" block changes.
- **Gate:** oracle first, alone: 80/80, every family 1.00 (threshold ≥ 0.95
  overall, no family < 0.90).
- **One correction between the gate and the comparative run, recorded in
  `predictions/pilot.json`:** the oracle's stated reason on B-01 showed it
  reading "Tuesday" as the day *after* the Monday deadline, so the original
  choices did not make the two governing states imply different actions —
  the scenario could not have detected a wrong state. Re-specified as
  "before the deadline, as late as possible" with Thursday the 17th /
  Friday the 18th; gold governing state unchanged; oracle re-run 5/5 with
  the intended reasoning. Independent of any variant outcome; no
  comparative run existed yet.
- **Cost:** 560 calls ≈ $0.50. Wall-clock ≈ 55 minutes, sequential.

## 3. Results

Governing-state accuracy (resolution stage, deterministic) and task success
(agent stage, mean of five runs):

```text
                 governing state                       task success
variant     prov   typed   rep-fail   ctrl   all  │  prov   typed   rep-fail   ctrl   all
b0          0.25    0.50      1.00    1.00  0.69  │  0.50    0.50      1.00    1.00  0.75
b_scd       0.25    0.50      1.00    1.00  0.69  │  0.50    0.55      1.00    1.00  0.76
b_scd_g     1.00    0.50      1.00    1.00  0.88  │  1.00    0.50      1.00    1.00  0.88
b_typed     1.00    1.00      1.00    1.00  1.00  │  1.00    1.00      1.00    1.00  1.00
oracle      1.00    1.00      1.00    1.00  1.00  │  1.00    1.00      1.00    1.00  1.00
nomem          —       —         —       —     —  │  0.75    0.85      1.00    0.75  0.84
```

Per scenario, correct runs of five:

```text
            b0   b_scd   b_scd_g   b_typed   nomem
A-01         0       0         5         5       5
A-02         0       0         5         5       5
A-03         5       5         5         5       5
A-04         5       5         5         5       0
B-01         5       5         0         5       5
B-02         0       1         5         5       2
B-03         5       5         0         5       5
B-04         0       0         5         5       5
C-01..C-04   5       5         5         5       5
N-01         5       5         5         5       0
N-02..N-04   5       5         5         5       5
```

Attribution of every failed run: `wrong_governing_state` — b0 20, b_scd 19,
b_scd_g 10, b_typed 0, nomem 13. **`correct_state_wrong_agent_decision`: 0.**
Violation rate (provenance): 0.50 / 0.50 / 0.00 / 0.00 / 0.25. Repeated
failure: 0 everywhere. False avoidance on N-04: 0 everywhere.

## 4. Verdicts

Applied exactly as frozen in `predictions/pilot.json`.

### BRQ1 — provenance-aware resolution reduces decision errors: **SUPPORTED, with a qualification**

Rule: b_typed and b_scd_g exceed b0/b_scd on provenance by ≥ 0.25 with
oracle ≥ 0.9. Observed: 1.00 vs 0.50; oracle 1.00. The wrong governing
state reached behaviour directly — on A-01 and A-02, b0 and b_scd sent the
announcement and booked the window seat in all ten runs.

The qualification is the pre-registered F3, and it is the more important
finding: **b_scd_g matches b_typed exactly.** A bitemporal table with one
frozen source-priority ranking resolves every provenance conflict in the
family. TypedMem's authority mechanism is not uniquely necessary for this
setting; *some* source ranking is.

Two further things the per-scenario table shows. A-03 does not
discriminate: given "probably a transient flake" as governing state, the
model still held the PR in every run — its own caution did the work. And the
no-memory row gets A-01/A-02/A-03 right on the same caution ("customer
announcements should be reviewed", "hold until checks pass"), which means
the family's gold coincides with the model's conservative default. What the
provenance family therefore measures most cleanly is not that the right
memory helps but that **the wrong memory hurts**: b0/b_scd at 0.50 sit below
no memory at 0.75. A recency-only store actively overrides a sensible
default with a bad inference.

### BRQ2 — type-dependent semantics beat one global rule: **SUPPORTED**

Rule: b_typed exceeds b_scd_g on typed; b_scd_g's losses are B-01/B-03 while
b0/b_scd's are B-02/B-04; oracle ≥ 0.9. Observed exactly that, 5/5 in every
cell:

```text
                    B-01 deadline   B-02 fact   B-03 commitment   B-04 fact (weak restatement)
b0 / b_scd               5/5          0/5 · 1/5        5/5                0/5
b_scd_g                  0/5          5/5              0/5                5/5
b_typed                  5/5          5/5              5/5                5/5
```

The global policy (validity → source → confidence → recency) is right for
the two facts and wrong for the deadline and the commitment, where the
declared semantics put recency first; the recency-only variants are the
mirror image. No single global order gets all four, and the agent acted on
whichever governing state it was handed in every run — b_scd_g scheduled the
review for the stale Friday deadline and refused the library the user had
since accepted, with reasons that cite the memory verbatim. This is the Mode
A interaction, now at the level of actions.

The no-memory row is informative here too: it gets B-01, B-03, B-04 right by
default (the tasks admit a sensible answer without memory) and guesses on
B-02 (2/5). So, as with the provenance family, the sharpest reading is that
**a mis-resolved memory costs more than an absent one** on three of the four
typed scenarios.

### BRQ3 — memory of prior failure reduces repeated failure: **INCONCLUSIVE**

Rule: memory-bearing repeated-failure rate ≤ half of nomem's. Observed: every
variant 0.00, *including nomem*. The B2-lite tasks are solvable from their
own context — a file marked `# GENERATED … do not edit`, an endpoint named
`legacy` beside one named `v2`, a fixture beside a process-wide global. The
model takes the right strategy without the lesson in 20/20 runs, so there is
no base rate for a memory to reduce. This is not evidence for or against
BRQ3; it is evidence that closed-choice transfer tasks with descriptive
context cannot test it. F4 (over-generalisation) did not occur: N-04 false
avoidance is zero for every variant.

## 5. What the pilot establishes

1. **F1 is ruled out.** In 480 runs across five memory-bearing variants,
   there is not one failure attributed to the agent ignoring a correct
   governing state. Every failure is a resolution failure. Under this prompt
   and model, the agent does what the resolved memory says — which is what
   makes the resolution stage's differences matter.
2. **The typed-resolution interaction reaches behaviour.** The strong
   baseline and the recency baselines fail complementary halves of the typed
   family, 5/5 each way, and TypedMem's per-type guards fail none. This is
   the claim that survived Mode A, was not testable externally, and now has
   behavioural evidence on 4 scenarios.
3. **Source priority is enough for provenance.** TypedMem's authority veto
   adds nothing over a frozen source ranking on this family. The paper's
   provenance claim should be stated as *a source ranking is necessary*, not
   *TypedMem's mechanism is*.
4. **Wrong memory is worse than no memory** — 0.75/0.76 vs 0.84 overall,
   0.50 vs 0.75 on provenance — which is the practical cost a recency-only
   memory imposes.

## 6. Limitations

- **Sixteen scenarios, one model, closed choices.** Counts, not statistics.
- **Same hands** designed scenarios and system; predictions and the oracle
  gate limit, and do not remove, that.
- **No sampling control.** Variance is real (b_scd on B-02: 1/5; no-memory
  on B-02: 2/5) and only bounded by five runs.
- **The provenance family's gold coincides with the model's cautious
  default**, so it under-measures the benefit of correct memory and
  over-measures the cost of wrong memory. A-03 does not discriminate at all.
- **Family C is not a repeated-failure test in this form.** The
  design's Track B2 — the agent fails, the failure becomes a memory, a
  transfer task follows — was not run; B2-lite replaced it and turned out to
  leak the answer through task context.
- **Thinking off, effort low.** Chosen for variance, not for realism; a
  stronger configuration might solve more from context and narrow the
  memory effect.

## 7. Decision

BRQ1 `SUPPORTED` (qualified by F3), BRQ2 `SUPPORTED`, BRQ3 `INCONCLUSIVE`.
Two of the three pilot success criteria that matter — predicted-direction
separation, mechanism-concentrated failures, flat controls, a solvable task
set, effects surviving agent noise — are met for BRQ1 and BRQ2. The pilot
shows downstream signal, which is the condition for expansion (design §20).

Expansion, if pursued, should change three things before adding scenarios:
provenance tasks whose correct action is *not* the model's default; Family C
rebuilt as execution-grounded tasks where the failing strategy is not
signposted by the context; and parallel calls, since wall-clock, not money,
is the cost. No TypedMem change follows from this pilot. The one finding
about TypedMem — that its authority mechanism is matched by a source ranking
— is a scoping statement for the paper, not an issue.
