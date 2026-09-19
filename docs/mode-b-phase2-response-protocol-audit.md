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

1. **What does the agent report drove the decision — memory or task context?**
   Closed enum, cross-checkable against the variant (a `nomem` run claiming
   `resolved_memory` is a detectable contradiction).
2. **Which part of the payload does it cite?** A verbatim substring of the
   payload.
3. **Does it report an uncertainty signal, and can it ground the claim?** An
   enum plus a span drawn from the payload.

### What this can and cannot establish

These fields turn §1a's interpretation into an **explicit, partially verifiable
self-report**. They do not make it a measurement of mechanism, and the
distinction has to survive into whatever is written from them.

**Substring validation proves only that a quotation came from the input.** It
does not prove the quoted span supports the action, and it does not prove the
agent used the span in reaching the action. A model may cite a hedge after the
fact, having decided on other grounds; a grounded quote is consistent with that
and cannot distinguish it. `decision_basis` and `uncertainty_signal` are
self-reports about reasoning, not observations of it, and nothing here licenses
treating them as evidence of an internal process.

What they do buy is narrower and real: a claim that is *checkable against the
input* rather than free text that can be anything, and a filler token that can
no longer pass.

If a stronger measurement is wanted later, it should come from a
**deterministic evaluator** asking whether the cited span contains a
pre-defined, task-specific signal recorded with the scenario — not from another
free-text judge, which would reintroduce exactly the unconstrained-text problem
this audit exists to close.

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
  "evidence_quote": "Tuesday the 24th",
  "uncertainty_signal": "explicit_hedge",
  "uncertainty_quote": "actually",
  "explanation": null
}
```

| Field | Type | How it is verified | Status |
|---|---|---|---|
| `action` | enum of `scenario.task.choices` | unchanged; `== scenario.gold_action` | task outcome |
| `decision_basis` | enum: `resolved_memory`, `task_context`, `no_relevant_memory` | consistency against the variant; `nomem` + `resolved_memory` is a contradiction | **self-reported** |
| `evidence_quote` | string | **non-empty verbatim substring of the payload shown** | grounded citation |
| `uncertainty_signal` | enum: `explicit_hedge`, `none` | — | **self-reported** |
| `uncertainty_quote` | string or null | non-empty verbatim substring iff `explicit_hedge`; **must be `null`** when `none` | grounded citation |
| `explanation` | string or null, optional | not parsed | **never scored, never in any verdict** |

`additionalProperties: false`. No `minLength` on any field — length is not a
proxy for semantic quality, and a rule on it would only buy longer filler while
risking the false positives §2 showed did not occur.

The two enum fields are labelled self-reported in the schema documentation
itself, so a later reader cannot mistake them for observations of reasoning.

`governing_record_id` and `supporting_record_ids` are **not adopted**, for the
reason in §3: the agent is not shown ids and does not select the governing
record. If a future protocol wants them, it must first change
`payload_lines()` to emit identifiers — which changes the stimulus, and
therefore the experiment. That is a separate decision, recorded in §6.

### Why this kills the failure mode

`"placeholder"` cannot appear in `decision_basis` or `uncertainty_signal` (not
in the enums) and cannot appear in `evidence_quote` or `uncertainty_quote` (not
a substring of the payload). Every field that carries weight is checkable
against something outside the model's output. The one field that remains free
text carries no weight at all, so its degeneracy is harmless by construction —
the current defect is precisely that a free-text field was quietly loaded with
weight after the fact.

This closes the *filler* failure mode. It does not close the gap between a
grounded citation and a causal account of the decision; see §3.

### Validation rules, and the tests that must ship with v2

Ship red-green with the implementation; none of these touch Phase 2 data.

| # | Rule | Test |
|---|---|---|
| 1 | `action` uses the existing closed enum | off-list action rejected |
| 2 | `decision_basis` is a closed enum, **marked self-reported** | `"placeholder"` rejected; the schema records the self-report label |
| 3 | `evidence_quote` is a non-empty verbatim substring of the payload shown | `"placeholder"` rejected; a real span accepted |
| 4 | `uncertainty_signal` is one of `explicit_hedge`, `none` | anything else rejected |
| 5 | `explicit_hedge` requires `uncertainty_quote` non-empty and in the payload | missing, empty, or ungrounded quote rejected |
| 6 | `none` requires `uncertainty_quote` to be `null` | a non-null quote under `none` rejected |
| 7 | no `minLength` anywhere | a short but genuine quote (`"Tuesday the 24th"`, 16 chars) **accepted** — the R1.1 length false positive cannot recur |
| 8 | `additionalProperties: false` | an unknown key rejected |
| 9 | optional `explanation` empty or `"placeholder"` is legal | accepted, and asserted to appear in no verdict path |
| 10 | v1 behaviour and the frozen artifacts are unchanged | v1 `parse_decision` round-trips its own fixtures; a v2 object is not silently coerced by v1 |

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
frozen scenarios under the new protocol → only then decide whether §1a's claim
can be restated as a grounded self-report. It does not become a mechanism
measurement at any point in that sequence.

**None of that is started here.** This document is the audit and the proposal.
