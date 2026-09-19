# Mode B Phase 2 — response protocol: static audit

**Status:** Audit and proposed protocol v2. **Nothing applied to Phase 2.**
**Date:** 2026-09-19
**Scope constraint:** static only. No model calls were made, no frozen artifact
was modified, no prior result was rescored, and the second-model gate stays shut.
**Inputs:** source at `main`-derived branch `eval/mode-b-phase2-robustness`;
read-only inspection of frozen `results/phase2-0-*` and `results/phase2-1-*`.

The R1 result that motivates this: `effort: low → high` moved the degenerate
`reason` rate by one run in 720 (12.9% → 12.8%) while the BRQ2-narrow
interaction held and sharpened. Both causes registered in advance — token budget
and effort level — are excluded. This audit asks what `reason` is actually for.

---

## 1. Does `reason` enter task success, error classification, or any verdict?

**No. Not anywhere.** Full trace of every reference in the Mode B package:

| Site | What happens |
|---|---|
| `agent.py:26` (SYSTEM) | prompted as `"reason": "<one sentence>"` |
| `agent.py:95` | JSON schema property `{"type": "string"}` |
| `agent.py:97` | listed in `required` |
| `agent.py:62` | `parse_decision` reads it: `str(obj.get("reason", ""))` |
| `runner.py:80` | stored on the transcript dict |
| — | written to the results JSON |

And then nothing. `scoring.py` contains **zero** occurrences of `reason`; the
`Score` dataclass has no such field. `governing_correct()` reads the resolver's
output, `action_correct` compares `action` to `scenario.gold_action`, and every
`attribution` branch is decided from `action`, `governing_correct`, `family` and
`applies`. `runner.render()` never prints it. `tests/test_mode_b.py` never
asserts on it.

So `reason` is **not part of the task contract**. Its degeneracy cannot have
affected task success, governing-state accuracy, attribution, the E1 result, the
oracle gate, or the BRQ2-narrow verdict. E2 and R1 stand exactly as reported.

Its real status is narrower and worth naming precisely: `agent.py:6` declares it
"stored for diagnosis", but **no diagnosis was ever specified**, no consumer was
written, and no test constrained it. It sat as unused output until
`analysis/mode-b-phase2.md` §6 reached for it to characterise a failure mode,
at which point amendment R1.1 had to define a detector over free text after the
fact.

**Classification: a diagnostic-contract defect, not a task-protocol defect.** The
field was declared to carry diagnostic weight and given no contract to carry it
with.

### 1a. Where it has already become a measurement defect

One live claim already depends on unmeasured `reason` content.
`analysis/mode-b-phase2-r1.md` §3 and `analysis/mode-b-phase2.md` §6 explain the
`S>R>C` epistemic rescue (0.28 → 0.32) as the agent *noticing the record's own
hedge*. Nothing measures that. It is an interpretation of an outcome
differential, not an observation. The protocol offers no way to check it, and
free-text `reason` as it stands offers no way either.

That is the one place where §2's "if we ever want to analyse mechanism" is
already the present tense.

---

## 2. Why does `"placeholder"` satisfy the prompt and the schema?

### The observed values

Read-only over the frozen transcripts, by the R1.1 detector:

```text
             E2 effort low                 R1 effort high
   77  'placeholder'                 86  'placeholder'
    8  ''                             3  ''
    6  'invalid'                      1  'n/a'
    1  '}{'                           1  'attempt}'
    1  'test'                         1  'invalid'
  ───                               ───
   93  in 5 distinct values          92  in 5 distinct values
```

This is not "garbage". It is a **stereotyped filler token**, and higher effort
concentrated it further (77 → 86 of the degenerate set).

Three independent reasons it conforms:

**The schema cannot exclude it.** `{"type": "string"}` carries no `minLength`,
no `pattern`, no `enum`. Every string conforms, so structured output guarantees
only that *a* string is emitted. Constrained decoding converts "the model might
omit the field" into "the model will always emit something" — it cannot make the
something informative. The guarantee is syntactic by construction.

**The parser cannot reject it.** `parse_decision` does `str(obj.get("reason", ""))`
with no validation and an empty-string default. A missing `reason` and a
`"placeholder"` reason are indistinguishable downstream.

**The prompt arguably teaches it.** SYSTEM ends with a literal template:

```text
{"action": "<exactly one of the listed actions>", "reason": "<one sentence>"}
```

`<one sentence>` is an angle-bracket slot name. A model that mirrors the template
surface rather than filling the slot emits a slot-shaped token — and the single
most common value observed is the English word for exactly that. The `action`
slot cannot fail the same way because its enum forces a real value; `reason` has
nothing forcing it.

Note the asymmetry this exposes: **the only field with a semantic constraint is
the only field that never degenerates.**

### What the degeneracy does not mean

Of the degenerate-reason runs, **69/93 (E2) and 75/92 (R1) produced the correct
action.** A filler `reason` accompanies a correct decision roughly four times in
five. The field is decorative, so its degeneracy is uninformative about the
decision — which is the same fact from both directions.

### One retroactive check on R1.1, no change to it

The amendment flagged that `len(reason) < 12` could catch short-but-valid
reasons. Over both arms it caught none: all ten distinct degenerate values are
genuine filler (`placeholder`, `""`, `invalid`, `}{`, `test`, `n/a`, `attempt}`).
Recorded as an observation about this data. It does not alter R1.1, the R1
verdict, or the operational-only reading of the detector.

---

## 3. What do we actually need from `reason`?

Not "an explanation". Three specific, checkable things — and the audit's main
structural finding is that **two of them are unanswerable under the current
stimulus.**

### The blocking finding: the agent never sees record identifiers

`variants/base.py:13`:

```python
def payload_lines(self) -> list[str]:
    return [m.content for m in self.governing.values() if m is not None]
```

Bare `content` strings. For `P-10-D` the agent's entire memory payload is:

```text
- The application deadline is now Tuesday the 24th ('tues 24th, actually' — quick reply).
```

It never sees `m1` or `m2`, and it never sees the record that lost. Resolution
happens upstream and deterministically; the agent is handed the winner.

Two consequences for the proposed v2 shape:

- **`governing_record_id` is unanswerable.** The agent cannot name an id it was
  never shown.
- **It is also the wrong question to ask the agent.** The agent does not choose
  the governing record — the variant does, before the agent is called. Asking it
  which record governed asks it to report a decision it did not make. The thing
  that field would verify (`gold_governing`) is already scored deterministically
  by `governing_correct()`, with no model in the loop.

Same for `supporting_record_ids`: the agent can only cite what it was shown, and
it was shown content without ids.

### What is verifiable without changing the stimulus

Ground every field in either a **closed enum** or a **verbatim span of the
payload the agent was actually given**. A span cannot be invented — a substring
check either passes or fails — so filler is mechanically impossible.

1. **Did the memory drive the decision, or the task context?** Closed enum,
   cross-checkable against the variant (a `nomem` run claiming `resolved_memory`
   is a detectable contradiction).
2. **Which part of the payload was used?** A verbatim substring of the payload.
3. **Was the hedge noticed?** The one thing needed to turn §1a's interpretation
   into a measurement: a boolean plus the span, where the span must overlap the
   hedge text the scenario already records.

---

## 4. Free text, or verifiable structure?

**Structure for everything that carries measurement weight; free text kept, but
demoted to optional and never scored.** `minLength` is rejected explicitly: it
converts `"placeholder"` into a longer piece of filler and measures prose length,
which is not a quantity anyone wants.

### Proposed protocol v2

```json
{
  "action": "Monday the 23rd",
  "decision_basis": "resolved_memory",
  "evidence_quote": "The application deadline is now Tuesday the 24th",
  "hedge_noticed": true,
  "hedge_quote": "'tues 24th, actually' — quick reply",
  "explanation": "optional free text, never scored"
}
```

| Field | Type | How it is verified |
|---|---|---|
| `action` | enum of `scenario.task.choices` | unchanged; `== scenario.gold_action` |
| `decision_basis` | enum: `resolved_memory`, `task_context`, `no_relevant_memory` | consistency against the variant and the payload; `nomem` + `resolved_memory` is a contradiction |
| `evidence_quote` | string, **must be a verbatim substring of the payload** | mechanical substring check; `""` allowed only when `decision_basis == "no_relevant_memory"` |
| `hedge_noticed` | boolean | paired with `hedge_quote` |
| `hedge_quote` | string, verbatim substring, required iff `hedge_noticed` | substring check, plus overlap with the scenario's recorded hedge span |
| `explanation` | string, optional | **never scored, never parsed, never used in any verdict** |

`governing_record_id` and `supporting_record_ids` are **not adopted**, for the
reason in §3: the agent is not shown ids and does not select the governing
record. If a future protocol wants them, it must first change
`payload_lines()` to emit identifiers — which changes the stimulus, and
therefore the experiment. That is a separate decision, recorded in §6.

### Why this kills the failure mode

`"placeholder"` cannot appear in `decision_basis` (not in the enum) and cannot
appear in `evidence_quote` (not a substring of the payload). Every field that
carries weight is checkable against something outside the model's output. The
one field that remains free text carries no weight at all, so its degeneracy is
harmless by construction — the current defect is precisely that a free-text
field was quietly loaded with weight after the fact.

### Tests that must ship with v2

Ship red-green with the implementation; none of these touch Phase 2 data.

1. `"placeholder"` in `decision_basis` → rejected (not in enum).
2. `"placeholder"` in `evidence_quote` → rejected (not a payload substring).
3. A short but genuine quote (`"Tuesday the 24th"`, 16 chars) → **accepted**;
   nothing rejects on length, so the R1.1 false-positive risk cannot recur.
4. `evidence_quote` with altered whitespace or casing → rejected; the check is
   verbatim, with a single documented normalisation (leading/trailing space).
5. `hedge_noticed: true` with absent or empty `hedge_quote` → rejected.
6. `hedge_quote` not overlapping the scenario's recorded hedge span → recorded as
   `hedge_misattributed`, **not** silently accepted.
7. `decision_basis: "resolved_memory"` on a `nomem` run → recorded as
   `basis_contradiction`.
8. `explanation` absent, empty, or `"placeholder"` → **accepted**, scored
   nowhere, and asserted to appear in no verdict path.
9. A v1 response (`{"action", "reason"}`) parsed by the v2 parser → rejected with
   a version error, never silently coerced.
10. A v2 response parsed by the v1 parser → v1 is frozen and untouched; the test
    asserts the v1 parser is not modified by this change.

### Acceptance criteria, restated against the proposal

| Criterion | Met by |
|---|---|
| `"placeholder"` cannot pose as structured reasoning evidence | enum + substring checks (tests 1, 2) |
| short-but-valid answers not killed on length | no length rule anywhere (test 3) |
| every new field has a defined scoring use | table in §4; `explanation` explicitly has none (test 8) |
| existing scenario gold unchanged | v2 adds response fields only; `gold_governing` / `gold_action` untouched |
| E2 / R1 stay frozen, no retroactive rescoring | v2 is a new module; v1 parser, scorer and artifacts untouched (test 10) |
| new protocol validated as its own version with its own pilot | §6 |

---

## 5. What this does **not** change

The BRQ2-narrow verdict, the E2 result, the R1 result, the oracle gate, the
second-model gate, every scenario, and every gold value. `reason` was never in a
scoring path, so nothing downstream of it moves. This audit adds a defect
classification and a proposal; it settles no experimental question.

---

## 6. If v2 is built

It is a **new protocol version with its own pilot**, not an R1 continuation and
not comparable to E2 or R1. The response schema is part of the stimulus, so a
v2 run measures a different condition: results may not be pooled with, or
compared against, E2/R1 as if the protocol were held constant.

The open decision that must be settled *before* a v2 pilot, not after: whether
`payload_lines()` starts emitting record identifiers. Doing so would make
`governing_record_id` answerable, and would also change what every agent sees in
every scenario. It is a stimulus change with its own confound, and it is not
required by anything in §3's minimal set.

Sequence, if it proceeds: implement v2 parser and validator with the §4 tests
(no model calls) → freeze a v2 protocol manifest → run one small pilot on the
frozen scenarios under the new protocol → only then decide whether the mechanism
claim in §1a can be measured rather than interpreted.

**None of that is started here.** This document is the audit and the proposal.
