# Mode B Phase 2 — global policy stress test: analysis

**Scope:** [`docs/mode-b-phase2-global-policy-stress-test.md`](../docs/mode-b-phase2-global-policy-stress-test.md),
executed on the frozen chain `semantics/phase2-types.md` → `tasks/phase2.json`
→ `predictions/phase2.json` → E1 → oracle gate → E2, each committed before the
next existed.
**Depends on:** [`analysis/mode-b-pilot.md`](mode-b-pilot.md) (BRQ2 SUPPORTED on
4 scenarios; F3 — a source ranking suffices for provenance).
**System under test:** TypedMem `main @ 33d989e`, unchanged.
**Status:** frozen. No scenario added or removed after a result was seen; one
wording correction between the oracle gate and the comparison, recorded below.

## 1. The question, as narrowed before any scenario was written

The per-type semantics table found that every core state type shares the
source guard and the types differ on one thing only: whether *confidence*
also guards replacement. So Phase 2 does not ask which of many orderings over
three dimensions is best. It asks one thing:

> For equally authoritative observations, should lower-confidence newer
> evidence replace existing state — and does the answer depend on the kind of
> state being represented?

The table's pre-registered answer: for **epistemic** state (a fact about the
world) confidence is a ranking key and the existing, better-evidenced record
stands; for **declared** state (a deadline, a commitment, an explicit
preference) a valid revision supersedes and confidence is only an admission
floor (0.5). No fixed ordering can satisfy both. Phase 2 exists to falsify
that sentence, first deterministically (E1) and then in agent behaviour (E2).

## 2. Setup

- **Scenarios:** 12 reversal pairs (24) + 12 controls, six domains. Every pair
  holds source class equal, incoming newer, incoming confidence 0.6 vs 0.9,
  and varies only the state class. The lower confidence is earned by the text
  (a hedge from the source; a terse, context-dependent revision) and the
  reason is recorded per scenario. Deadlines move *earlier* so that gold
  differs from "as late as possible"; `nomem_predicted` is pre-registered per
  scenario.
- **E1:** all 6 permutations of (S, C, R) after validity, 3 single-dimension
  policies, b0, b_scd, b_typed. Resolution stage only.
- **E2:** per the pre-registered selection rule, `S>C>R` and `S>R>C` (the
  two S-first orderings, complementary on the pairs, perfect on controls),
  `b_typed`, `oracle`, `nomem`. Same prompt (`mode-b-pilot-0`), model
  (`claude-sonnet-5`), configuration (thinking off, effort low,
  schema-constrained action) and five runs as Phase 1. The agent-stage runner
  resolves through the same `ORDERINGS` registry object E1 measured; a test
  asserts the governing ids are identical.
- **Gate:** oracle alone, 180 calls: overall 0.97, epistemic 0.98, declared
  0.92, controls 1.00 — passes (≥ 0.95; no class < 0.90).
- **One correction between gate and comparison:** P-10-D's incoming record
  began *"Now Tuesday the 24th …"*, which the oracle read as today's date in
  5/5 runs ("Monday the 23rd has already passed"). As worded, no variant could
  have got it right, so it could not detect a wrong governing state. Reworded
  to *"The application deadline is now Tuesday the 24th …"*; gold unchanged;
  oracle re-run on that scenario 5/5 with the intended reasoning. Recorded in
  `predictions/phase2.json`. P-10-F's single wrong oracle run (reason
  `placeholder`) was left alone — see §6.
- **Cost:** 900 scored calls ≈ $0.80; one abandoned comparative run (the
  machine slept mid-run; nothing written) adds an unknown fraction of that.
  E2 wall-clock 24 minutes for 720 calls.

## 3. E1 — every fixed ordering, resolution stage

```text
policy      epistemic   declared    pairs   controls
S>C>R          12/12       0/12    12/24      12/12
S>R>C           0/12      12/12    12/24      12/12
C>S>R          12/12       0/12    12/24       8/12   K-05..08
C>R>S          12/12       0/12    12/24       8/12   K-05..08
R>S>C           0/12      12/12    12/24       7/12   K-05..08, K-09
R>C>S           0/12      12/12    12/24       7/12   K-05..08, K-09
S_only          0/12      12/12    12/24      12/12
C_only         12/12       0/12    12/24       8/12
R_only          0/12      12/12    12/24       7/12
b0 / b_scd      0/12      12/12    12/24       7/12
b_typed        12/12      12/12    24/24      12/12
```

Every row matches `predictions/phase2.json`. With source held equal, the six
permutations collapse into two classes on the pairs — C-before-R and
R-before-C — and each class is perfect on one state class and zero on the
other. **No fixed ordering is correct on both.** The permutations differ only
on the source-conflict controls, where every S-first ordering is right and
every other is wrong; recency-first orderings additionally lose K-09
(inference newer than a verified result). The falsifier — some ordering
24/24 — did not fire.

## 4. E2 — does the split reach behaviour?

Task success, mean of five runs, by state class:

```text
                 governing state              task success
variant     epist  decl  ctrl  │  epist  decl  ctrl   all
S>C>R        1.00  0.00  1.00  │   0.95  0.00  0.98  0.64
S>R>C        0.00  1.00  1.00  │   0.28  1.00  0.98  0.76
b_typed      1.00  1.00  1.00  │   0.97  1.00  0.97  0.98
oracle       1.00  1.00  1.00  │   0.98  0.92* 1.00  0.97
nomem           —     —     —  │   0.52  0.30  0.43  0.42
                                   * before the P-10-D correction; 1.00 after
```

Per scenario (correct runs of five), reversal pairs:

```text
           S>C>R  S>R>C  typed  nomem          S>C>R  S>R>C  typed  nomem
P-01-F       5      0      5      0    P-01-D    0      5      5      0
P-02-F       5      0      5      5    P-02-C    0      5      5      0
P-03-F       5      0      5      5    P-03-P    0      5      5      0
P-04-F       5      0      5      5    P-04-D    0      5      5      0
P-05-F       2      1      3      3    P-05-C    0      5      5      5
P-06-F       5      0      5      1    P-06-P    0      5      5      3
P-07-F       5      5      5      0    P-07-D    0      5      5      0
P-08-F       5      4      5      5    P-08-C    0      5      5      5
P-09-F       5      5      5      0    P-09-P    0      5      5      5
P-10-F       5      2      5      2    P-10-D    0      5      5      0
P-11-F       5      0      5      0    P-11-C    0      5      5      0
P-12-F       5      0      5      5    P-12-P    0      5      5      0
```

Controls: every memory-bearing variant 5/5 on 33 of 36 cells; the three
exceptions (K-01 `S>C>R` 4/5, K-11 `S>R>C` 4/5, K-11 `b_typed` 3/5) are all
degenerate-output runs (§6). No variant is separated on controls.

Attribution of failed runs: `S>C>R` 60 `wrong_governing_state` + 4
`correct_state_wrong_agent_decision`; `S>R>C` 43 + 1; `b_typed` 0 + 4;
`nomem` 104 (no governing state) + 1 unparseable. **All nine
`correct_state_wrong_agent_decision` runs are degenerate-output runs**; with
those excluded the interaction is exact — `S>C>R` 1.00 / 0.00, `S>R>C`
0.22 / 1.00, `b_typed` 1.00 / 1.00, controls 1.00 for all three.

## 5. What the results say

**1. The deterministic split propagates to behaviour, in both directions, on
every pair.** `S>C>R` schedules for the stale deadline, refuses the library
the user has since accepted, books the old seat, keeps state in S3 — 0/60
declared-state runs correct, reasons citing the superseded record verbatim
("The user has stated they will not add lodash"). `S>R>C` ships to the guessed
city and points the deploy at the guessed region — reasons like "the runbook
comment suggests staging may have moved to us-east-1, and lacking other
context, this unresolved note is the best available sign". `b_typed` is at
oracle on both classes. This is the Phase 1 interaction, now on 24 scenarios
across six domains, 5/5 in 44 of the 48 pair × fixed-ordering cells.

**2. The two errors are not symmetric in cost, and the asymmetry is
informative.** `S>C>R` on declared state is a total loss (0.00): a superseded
declaration reads as clean, confident state and the agent acts on it every
time. `S>R>C` on epistemic state is 0.28, not 0.00, and the rescue is
specific: on P-07-F and P-09-F the hedged record carries its own warning
("may now be v3 — unverified", "might be weekly now? — unconfirmed") and the
agent declines to act on it in 10/10 runs, reasoning from the *choices* back
to the "established" value. Where the hedge is softer ("might have moved to
PostgreSQL — the user wasn't sure") the agent follows it. So a hedged
epistemic record partially protects itself through the agent's caution; a
stale declaration cannot, because nothing in its text says it has been
revised. **This is why confidence-ranks-recency is the more dangerous global
choice**, and it is also why the stale-declaration failure is the one a memory
system must fix at resolution time — no downstream prompt can see it.

**3. Wrong memory is worse than no memory, on exactly the class each fixed
policy gets wrong.** `nomem` is 0.30 on declared and 0.52 on epistemic;
`S>C>R` is 0.00 on declared, `S>R>C` 0.28 on epistemic. On the class each
gets right, both are at `b_typed`. A recency-only or confidence-first store
does not merely fail to help on the wrong class — it actively overrides a
better default.

**4. The no-memory row behaves as pre-registered on 18 of 25 predicted
scenarios**, and the seven misses run in both directions (three declared
scenarios where the model's default coincided with gold — P-05-C, P-08-C,
P-09-P; four epistemic ones — P-02-F, P-04-F, P-08-F, P-12-F — predicted
symmetric but resolved 5/5 to gold without memory). Those seven are
`default_aligned` in effect and are the ones where the typed advantage over
no memory is smallest; they do not affect the fixed-ordering contrast, which
is between memory-bearing variants on the same scenario.

**5. The epistemic / declared taxonomy explains every pair result.** No pair
result needed a type-specific story: the 12 declared scenarios behave alike
under every variant, and so do the 12 epistemic ones (modulo the hedge
strength in point 2). This is the observation the table recorded for
analysis; it is stronger than "six types need six policies".

## 6. Limitations and things recorded

- **A degenerate output mode.** 117 of 900 runs (13%) returned a `reason` of
  `placeholder`, empty, or garbage, concentrated on seven scenarios (P-08-F 23,
  P-05-F 21, K-01 17, P-10-F 15, K-11 15, P-11-C 14, P-06-F 12) and spread
  evenly across variants including oracle (24–27 each). The action in these
  runs is often arbitrary — P-05-F `S>C>R` chose "Marco" 3/5 with the memory
  naming Priya and Marco absent from it. This is the cost of thinking-off /
  effort-low; it accounts for every `correct_state_wrong_agent_decision` and
  every non-5/5 control cell. It was not filtered out of the headline numbers.
  A stronger configuration should be run once as a robustness check, with the
  expectation that it removes this noise and may raise `S>R>C`'s epistemic
  rescue rate (point 2) by reasoning harder about hedges.
- **The agent partially compensates for one failure mode.** Point 2 means
  the behavioural gap on epistemic state under-states the resolution gap
  (0.28 vs 0.00) when the hedge is explicit in the record. Stated as a limit
  of the claim: recency-first is less harmful than the resolution stage
  suggests *when records preserve their hedges*; nothing here says how often
  extraction preserves them.
- **One model, one prompt, closed choices, counts not statistics.** As in
  Phase 1.
- **Same hands** wrote the table, the tasks and the system. The table was
  argued without reference to the implementation and frozen first; E1's
  falsifier and the oracle gate are the checks, and they are not independent
  review.
- **The sleep incident.** The first comparative run stalled when the machine
  slept; it wrote nothing and was killed and repeated under `caffeinate`. The
  committed result is the single complete run.

## 7. Verdict

Applied exactly as frozen in `predictions/phase2.json`:

**BRQ2-narrow: SUPPORTED.** E1: no fixed ordering ≥ 24/24 on pairs; `b_typed`
24/24; the best fixed orderings split exactly along epistemic vs declared.
E2: the same split in task success for `S>C>R` (0.95 / 0.00) vs `S>R>C`
(0.28 / 1.00); oracle 0.97 ≥ 0.95; `b_typed` 0.98 within 0.05 of oracle;
`correct_state_wrong_agent_decision` ≤ 0.03 on every class.

The claim the paper can now make, in the words the design fixed before the
run:

> A fixed source ranking is sufficient for source conflicts; the contribution
> is not provenance. **Whether lower-confidence newer evidence should replace
> existing state depends on whether the state is epistemic or declared, no
> fixed global ordering satisfies both, and an agent given the resolved state
> acts on it** — so the trade-off is structural, and it propagates to
> behaviour.

## 8. Decision

No TypedMem change follows. The epistemic / declared split is recorded as an
analysis-level taxonomy, not a schema change. Next, in order: a single
robustness run with a stronger model configuration (to remove the degenerate
mode and test point 2); then a second model. Neither changes the scenarios.
