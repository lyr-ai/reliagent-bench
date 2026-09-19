# TypedMem Phase 2 — narrative skeleton

**Status:** Skeleton for review. **Not a draft.** Claim hierarchy first; prose later.
**Date:** 2026-09-19
**Evidence frozen in:** `analysis/mode-b-phase2.md` (E1, oracle gate, E2),
`analysis/mode-b-phase2-r1.md` (R1), `docs/mode-b-phase2-response-protocol-audit.md` (protocol).

Each section states **one** claim, the evidence for it, the wording permitted,
the boundary that must not be crossed, and its figure or table.

---

## Title and claim hierarchy — settled 2026-09-19

**Title:**

> **One Order Is Not Enough: Typed Resolution for Declared and Epistemic Memory**

The earlier headline was rejected in review: scoping `reasoning` to `reasoning
effort` fixed the accuracy problem but left R1 — a single-model, single-axis
robustness check — sitting in the title as if it were the contribution. The
strongest evidence is E1's structural result, and the title now says that.

R1 appears as the abstract's closing sentence instead:

> The interaction persists when agent reasoning effort is increased from low to
> high.

**Claim hierarchy, fixed:**

| # | Status | Claim |
|---|---|---|
| 1 | **Primary** | No fixed global ordering resolves both declared and epistemic memory semantics. |
| 2 | **Primary** | Typed resolution resolves both, and prevents the deterministic conflict from propagating downstream. |
| 3 | **Robustness** | The downstream interaction persists under increased reasoning effort. |
| 4 | **Secondary observation** | Resolution errors exhibit asymmetric downstream recoverability. |
| 5 | **Hypothesis only** | Visible uncertainty cues may explain partial epistemic recovery. |

**Venue: workshop / short paper.** The shape is complete as it stands. Reopening
the stimulus branch to chase a full conference would introduce a new response
protocol, a new stimulus condition, explicit hedge manipulation, probably a
second model, a new pre-registration and an independent confirmation — and the
new experiment would not be poolable with E2 or R1. That is future work, named
in the paper, not an addition to this draft.

**§4 is a secondary *observed* finding.** It stays in Results with Figure 2, and
is written in three layers: result, candidate explanation, boundary. Not demoted
to discussion — that would bury the most novel observation. Not promoted to a
contribution — that would licence a reviewer to demand the mechanism experiment
this paper does not have.

## 1. Problem

**Claim.** Memory records carrying different confidence semantics cannot always
be resolved by one global precedence order.

**Evidence.** Conceptual; the per-type semantics table, argued and frozen before
any scenario was written. Recency, declared revision and epistemic evidence do
not mean the same thing, and collapsing them into one ordering produces
systematic — not random — error.

**Permitted.** "cannot always be resolved by a single global ordering";
"systematic error"; "the tested state classes".

**Forbidden.** "every memory type needs its own policy" (Phase 1 showed a fixed
source ranking suffices for provenance); "TypedMem is necessary".

**Asset.** Table 1 — the semantics table: state class × does confidence guard
replacement.

---

## 2. Deterministic mechanism — E1

**Claim.** The conflict is structural at the resolver, before any model runs.

**Evidence.** All six permutations of (S, C, R), three single-dimension
policies, B0 and B-SCD, on 12 reversal pairs (24 scenarios) + 12 controls.

```text
S>C>R    epistemic 12/12   declared  0/12   controls 12/12
S>R>C    epistemic  0/12   declared 12/12   controls 12/12
b_typed  epistemic 12/12   declared 12/12   controls 12/12
```

**Every one of the eleven fixed policies scores exactly 12/24 on the pairs.**
`S>C>R` and `S>R>C` are the only two that also keep 12/12 on controls — they are
the strongest fixed orderings available, not a convenient pair.

**Permitted.** "deterministic"; "exhaustive over the tested orderings"; "no
fixed ordering satisfies both classes".

**Forbidden.** Any claim about model reasoning — no model is in this loop. Any
claim of exhaustiveness beyond the three dimensions actually enumerated.

**Asset.** Table 2 — the full E1 matrix, all 12 policies, verbatim from
`results/phase2-e1.txt`.

---

## 3. Downstream consequence — E2

**Claim.** The deterministic resolution split propagated into downstream agent
task performance.

**Evidence.** 36 scenarios × 4 variants × 5 runs = 720 calls, one model, one
prompt, one scorer. Oracle gate passed first (0.97 overall; 0.98 / 0.92 / 1.00;
1.00 on declared after the P-10-D correction).

```text
                governing state          task success
variant      epist  decl  ctrl  │   epist  decl  ctrl   all
S>C>R         1.00  0.00  1.00  │    0.95  0.00  0.98  0.64
S>R>C         0.00  1.00  1.00  │    0.28  1.00  0.98  0.76
b_typed       1.00  1.00  1.00  │    0.97  1.00  0.97  0.98
nomem         0.00  0.00  0.00  │    0.52  0.30  0.43  0.42
```

`wrong_governing_state` accounts for 207 of 217 failures.
`correct_state_wrong_agent_decision` is 9 of 217 — inside the pre-registered
0.10 second-guessing stop condition, which did not trigger.

**Permitted.** "propagated into"; "the resolver error reaches the action".

**Forbidden.** "the agent independently rediscovered the mechanism";
"replicated". **The agent never saw the conflict.** Resolution happens upstream
and deterministically; the agent is handed the winning record as bare content,
with no ids and no sight of the loser. It cannot rediscover what it was never
shown.

**Asset.** Figure 1 — the variant × state-class interaction, the paper's central
visual. Table 3 — the full E2 matrix with attribution counts.

---

## 4. Asymmetric recoverability

**Claim.** Resolution errors are directionally asymmetric in their downstream
recoverability.

This is the most novel finding and the one most exposed to overclaim, so
observation and interpretation are separated explicitly.

**Observation.**

```text
error direction                                 E2      R1
suppress a valid declared revision             0.00    0.00
override better-evidenced epistemic state      0.28    0.32
```

Suppressing a declared revision is unrecoverable in every one of 60 runs, at
both effort levels. Overriding epistemic evidence is partly survivable.

**Permitted.** "directionally asymmetric"; "unrecoverable in the tested
scenarios"; "partly survivable".

**Forbidden.** "the agent recovered because it noticed the hedge." Nothing
measured that. Written as a candidate explanation only:

> One plausible explanation is that linguistic uncertainty cues remained visible
> in the selected payload, but the current protocol did not measure whether the
> agent noticed or used those cues.

**Why this matters to the framing.** The asymmetry is a directional result. The
symmetric statement — "no single ordering satisfies both" — is the kind of
claim adjacent work can absorb. "One of the two errors is recoverable and the
other is not" is harder to absorb and points at a design rule: *a system may
tolerate being wrong about what is true more readily than being wrong about
what was decided.* That sentence is a hypothesis this work generates, not one
it confirms, and must be written as such.

**Asset.** Figure 2 — paired bars, the two error directions at both effort
levels, with the 0.00 floor visible.

---

## 5. Robustness — R1

**Claim.** The E2 interaction is not an artefact of a weak model configuration.

**Evidence.** One axis moved: `effort: low → high`. Same scenarios, variants,
repetitions, scorer, prompt, schema, model, `max_tokens`. Configuration frozen
and committed before any call.

```text
             E2 (low)                 R1 (high)
b_typed      0.97 / 1.00              1.00 / 1.00
S>C>R        0.95 / 0.00              0.98 / 0.00
S>R>C        0.28 / 1.00              0.32 / 1.00
governing state: bit-identical across both arms
```

Also reported, because it did *not* move:

```text
degenerate operational detector    93/720 (12.9%)  →  92/720 (12.8%)
correct_state_wrong_agent_decision   9/217         →   3/200
```

**Permitted.** "single-axis robustness check"; "not a new confirmatory
experiment"; "rules out the weak-configuration explanation".

**Forbidden.** Treating R1 as replication or as added statistical power — it is
the same scenarios and the same model. Treating the flat degenerate rate as a
result about reasoning: the detector is operational only, the field is in no
scoring path, and a degenerate `reason` accompanied a *correct* action in 69/93
and 75/92 runs.

**Asset.** Table 4 — E2 vs R1, side by side, every cell.

---

## 6. What the evidence establishes

The claim ladder, ordered by strength. **This table should appear in the paper**,
not only in the appendix — it is the part most likely to be misread.

| # | Status | Claim |
|---|---|---|
| 1 | **Supported** | No single global ordering handles both confidence semantics correctly. |
| 2 | **Supported** | A typed resolution policy keeps both classes correct on the frozen task set. |
| 3 | **Supported** | Resolver errors propagate to downstream agent task performance. |
| 4 | **Observed** | The two error directions differ in downstream recoverability. |
| 5 | **Not established** | That partial recovery is caused by hedge recognition. |
| 6 | **Not established** | Generalisation to a second model or a wider task distribution. |

**Asset.** Table 5 — this table, verbatim.

---

## 7. Limitations and the protocol lesson

Stated in the paper's own voice, not buried:

- **The second model was not run, by rule.** The pre-registered gate required
  both a drop in the degenerate rate and a surviving interaction; only the
  second occurred. This is compliance with a frozen gate, **not an omission**.
  The paper should also record that the gate's premise is arguably obsolete —
  degeneracy turned out to be stable and harmless — and that acting on that
  without a dated, outcome-independent amendment would be the post-hoc move the
  protocol exists to prevent.
- **`reason` was an unused free-text diagnostic field.** It reaches no scoring
  path; `scoring.py` contains zero references. Its degeneracy cannot have
  affected any result. It is a diagnostic-contract defect, and it is already a
  measurement defect for the §4 explanation.
- **The operational detector measures operationally defined degeneracy**, not
  reasoning quality. Report it as such in both directions.
- **Protocol v2 is a future measurement design, not a result.** It appears in
  the paper only under future work.
- **The asymmetry is a new hypothesis worth testing**, not a confirmed
  mechanism.
- **One model, one prompt, closed choices, counts not statistics.** Same hands
  wrote the semantics table, the tasks and the system; E1's falsifier and the
  oracle gate are the checks, and they are not independent review.

---

## Asset summary

| ID | Kind | Content | Source |
|---|---|---|---|
| Table 1 | table | semantics table: state class × confidence guards replacement | `semantics/phase2-types.md` |
| Table 2 | table | E1, all 12 policies | `results/phase2-e1.txt` |
| **Figure 1** | **figure** | **variant × state-class interaction — the central visual** | E2 |
| Table 3 | table | E2 full matrix + failure attribution | E2 |
| **Figure 2** | **figure** | **asymmetric recoverability, both effort levels** | E2 + R1 |
| Table 4 | table | E2 vs R1 side by side | E2 + R1 |
| Table 5 | table | the claim ladder of §6 | this document |

Two figures, five tables. Figure 1 carries §3, Figure 2 carries §4; everything
else is tabular.

---

## Open questions for review, before any prose is written

1. **Headline (a) or (b)** — scope "reasoning" to "reasoning effort", or lead
   with the asymmetry?
2. **Is §4 a finding or a discussion item?** It is the most novel result and the
   least measured. Promoting it raises the paper's ceiling and its risk.
3. **Venue and length** — the claim ladder has three supported claims and one
   observation; that is a workshop paper's shape, not a full conference paper's,
   unless §4 is developed with its own experiment.
