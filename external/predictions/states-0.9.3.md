# Pre-registration: TypedMem 0.9.3 states on the external-validation runs

Written and committed **before** the adapter exists and before any run.
Nothing in the benchmark changes: tasks, normalised writes, gold answers,
query construction, scoring and failure attribution stay as frozen in
`longmemeval-ku.json` / `goodai-ltm.json` and the two runners. The only
addition is one variant row, `v9_states`.

## Why

TypedMem issue #5 recorded this measurement: `v4_replace` answers 0 of 11
LongMemEval knowledge-update history questions, and 0/3 NameList and 1/3
SallyAnne on GoodAI. TypedMem 0.9 added **states**, designed to give one
governing value *and* a queryable past. States have never been run here
(`reliagent-bench` was last updated 2026-09-19; states shipped 2026-09-26).

## Adapter mapping (frozen)

`TypedMemStates` uses only TypedMem's public 0.9.3 API: `InMemoryStore`,
`set_state`, `get_state`, `state_history`, `StateConflict`.

| Harness call | States call |
|---|---|
| `begin(scenario)` | a fresh `InMemoryStore()` |
| `write(w)` | `set_state(key=w.subject, value=w.content, valid_from=w.valid_from or w.observed_at, valid_to=w.valid_to, source=w.source_type, authority=w.authority)` |
| `query(q)` | `get_state(q.subject, as_of=q.as_of)`; `StateConflict` → `None` (no current value) |
| `history(type, subject)` | the key's `state_history`, oldest first, values only |

- The scenario's declared `TypeSemantics` (replace / keep_both /
  `resolve_by`) are **ignored**. States have a single contract, and there is
  no per-type policy to choose. The variant is run once per benchmark.
- `valid_from` falls back to `observed_at` because these writes are
  statements ("I now work at B") that take effect when they are made.

## Predictions

LongMemEval knowledge-update (question-level; 65 usable):

| Group | v4_replace | Prediction for v9_states | Why |
|---|---|---|---|
| current_state | 53/53 | **53/53** | the latest value is current |
| historical_state | 0/6 | **6/6** | `get(as_of=…)` answers from history |
| both_states | 0/2 | **2/2** | both lookups are as-of lookups |
| delta_direction | 0/3 | **3/3** | two as-of lookups, then compared |
| accumulation | 1/1 | **1/1** | the single answer is the current value, as for v4_replace |
| abstention | 6/6 | **6/6** | nothing valid → `None` |
| all_usable | 54/65 | **65/65** | |

GoodAI LTM (instance-level):

| Test | v4_replace | Prediction | Why / risk |
|---|---|---|---|
| Colours | 3/3 | **3/3** | current value |
| SallyAnne | 1/3 | **3/3** | an as-of lookup at the observer's exit |
| NameList | 0/3 | **3/3**, *with a named risk* | `history` lists every value. **Risk:** if a script repeats a name that is already current, states record it as corroboration (one entry), and the gold list would contain it twice → failure. |

## What would count against states

- Any **current_state** or **abstention** regression below v4_replace:
  states would be trading current truth for history.
- Any history question still answered `None`: states would not deliver the
  "queryable past" they promise.
- A NameList failure caused by the repeat-as-corroboration rule. That is a
  real semantic mismatch: states treat repeating the current value as the
  same state, while the benchmark treats it as another event. It would be
  evidence for issue #5's typed-memory history, not against it.

## Also checked

The six existing variants run in the same fresh environment (TypedMem
0.9.3). Their rows must reproduce the committed results exactly. Any
difference is reported as a finding about TypedMem 0.9, not absorbed.

---

## Addendum (before running Mode A): the Mode A state-level diagnostic

Added after the two external runs above came out as predicted (65/65, 9/9),
and **before** Mode A is run with states. Those runs only feed ordered,
single-source statements, so they can't separate states from keep-both or
bitemporal baselines. Mode A can: its gold encodes authority vetoes and
per-type confidence guards.

States make two design choices that differ from Mode A's gold. Both were
owner decisions in TypedMem design 0002, and they are not bugs:

1. **A later but weaker value opens a conflict**, and `get` returns nothing.
   Mode A's gold instead expects the stronger earlier value to stay current
   (a silent veto, transition `ignore`).
2. **Confidence is not a guard.** States order by validity time and
   authority only. Mode A's `resolve_by: confidence` types expect a newer
   but less-confident write to be ignored.

Adapter transitions (frozen): `new→add`, `changed→replace`, `past→keep`,
`conflict→keep`, `unchanged→ignore`, `scheduled→keep`. The primary metric is
**state accuracy**; transition accuracy is secondary, because states never
overwrite and so their vocabulary differs.

Predictions, by scenario (a scenario "fails" if any of its state queries is
wrong):

| Category | Predicted correct | Predicted to fail | Reason |
|---|---|---|---|
| temporal (10) | all 10 | — | validity windows, retroactive, expired, future |
| known_gap history G-01, G-02, G-03, G-06 | all 4 | — | the queryable past |
| known_gap G-04, G-05, G-07 | — | current-state queries (→ None); history queries correct | a weaker later value is a conflict, not vetoed |
| authority (11) | A-02, A-03, A-05, A-09, A-11 | A-01, A-04, A-06, A-07, A-08, A-10 | conflict instead of veto; A-07: a write without provenance gets default authority 1.0 in states, so it *is* defended |
| typed (11) | C-01, C-04, C-05, C-06, C-08, C-11 | C-02, C-07, C-09; C-03 and C-10 partly | no confidence guard (C-02, C-07); C-09 expects an older write to replace, while states file it in history |
| control (2), mixed (1) | control 2 | mixed: uncertain | |

- **Corruption rate > 0**, from the confidence-guard cases (C-02, C-07):
  states let a newer, less-confident write become current where gold says
  ignore. The authority cases don't count as corruption, because a conflict
  doesn't displace the current value.
- If states come out much *better* than this, check the adapter before
  believing it.
