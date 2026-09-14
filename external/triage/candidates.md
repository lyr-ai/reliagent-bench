# External validation — candidate benchmarks and desk screening

**Step 1 of [`docs/typedmem-external-validation.md`](../../docs/typedmem-external-validation.md) §19.**
**Status:** desk screening from papers and documentation only. **No example has
been inspected yet**; every cell below is what the benchmark's own
description claims, and is to be confirmed or overturned by the ≥30-example
inspection (§6) before anything is selected. Written 2026-09-13.

Screening is against the ten criteria in §5. `✓` = documented; `~` = partial
or indirect; `✗` = documented absent; `?` = not determinable from
documentation.

## Serious candidates

| criterion | LongMemEval | LoCoMo | GoodAI LTM | PerLTQA | PrefEval | MSC | DialSim |
|---|---|---|---|---|---|---|---|
| multi-session | ✓ ~40 sessions (S) / ~500 (M) | ✓ up to 35 sessions | ✓ one very long interleaved conversation | ~ per-character histories | ~ long single context | ✓ 5 sessions | ✓ episodes |
| state updates | **✓ `knowledge-update` category, 78 Qs** | ~ implicit in temporal Qs | **✓ several tests change information mid-run** | ? | ~ preferences may be revised | ~ personas evolve | ? |
| temporal queries | **✓ `temporal-reasoning`, 133 Qs** | ✓ `temporal`, 321 Qs | ~ time-ordered updates, few as-of questions | ? | ✗ | ✗ | ~ |
| contradictions | ✓ updates supersede earlier facts | ~ | ✓ | ? | ~ | ~ | ? |
| provenance | ~ speaker only (`single-session-user` vs `-assistant`) | ~ speaker only | ~ speaker only | ~ memory-type labels, not source | ~ explicit vs. implicit preference | ✗ | ✗ |
| semantic types | ~ `preference` category; otherwise untyped | ✗ | ~ by test (lists, locations, instructions) | **✓ profile / relationship / event / dialogue** | preferences only | ✗ | ✗ |
| raw history | ✓ timestamped sessions | ✓ dated sessions | ✓ full transcript | ✓ | ✓ | ✓ | ✓ |
| gold answers | ✓ 500 curated | ✓ ~1,986 QA | ✓ deterministic per test | ✓ 8,593 | ✓ | ✗ next-utterance | ✓ |
| adapter feasibility | ✓ static QA; oracle-candidate possible | ✓ static QA | ~ interactive agent protocol; would need a replay adapter | ✓ | ~ | — | ~ |
| licence / repro | ✓ public code + data | ✓ public data | ✓ MIT; some GPT-generated tests not for commercial use | ? | ? | ✓ | ? |

### Notes per candidate

**LongMemEval** (Wu et al., 2024) — 500 questions over five abilities:
information extraction, multi-session reasoning, temporal reasoning,
knowledge updates, abstention. The `knowledge-update` (78) and
`temporal-reasoning` (133) categories are the closest thing found to Mode A's
temporal category on externally designed data; `abstention` is a natural
negative control; `single-session-preference` (30) is a weak handle on type.
Provenance is speaker-level only. **First to inspect.** What inspection must
establish: whether knowledge-update questions are resolvable by *latest
valid state* alone (Finding 1 territory), or whether any depend on *who
said it* (Finding 3) — the documentation does not say.

**LoCoMo** (Maharana et al., 2024) — long conversations with dated sessions;
categories single-hop, multi-hop, temporal (321), open-domain, adversarial
(446, unanswerable). Temporal questions appear to be mostly *when did X
happen* rather than *what was true at T*; that is the thing to check.
Adversarial questions are a negative control of a different kind (should
abstain). **Second to inspect, for the temporal subset only.**

**GoodAI LTM Benchmark** — generative, interactive: an agent is run through a
long conversation in which tests are interleaved with filler, and several
tests deliberately update information (lists, locations, instructions) and
score the *latest* state. Closest match to "state updates" in spirit, and the
only candidate where updates are the *point* of the test rather than a
category. Costs: the protocol is interactive, so an adapter has to replay the
scripted conversation as writes; and updates are mostly "newest wins" with no
provenance or confidence structure, so it can test Finding 1 and not 2 or 3.
**Inspect after LongMemEval; select only if the interactive adapter is
cheap.**

**PerLTQA** (Du et al., 2024) — 8,593 questions across 30 characters with
memory-type labels (profile, social relationship, event, dialogue). The only
candidate with native *semantic types*, which is the ERQ3 requirement — but
whether structurally similar updates resolve differently by type is not
something the documentation addresses, and the temporal structure is
unclear. **Inspect for ERQ3 feasibility specifically.**

**PrefEval** — preference adherence over long contexts, explicit and implicit
preference statements. Single state type; possible preference revisions.
Relevant only if revisions exist and are labelled. **Low priority; screen a
sample before deciding.**

**MSC** (Multi-Session Chat) — five sessions per pair, persona-grounded; gold
is the next utterance, not a state answer. Fails the gold-answer criterion
for this phase. **Not selected.**

**DialSim** — TV-show role-play with a response-time constraint;
unanswerable questions. Little state-update structure evident. **Not
selected unless inspection of another candidate fails.**

## Inspected

**LongMemEval** — 36 examples, purposeful deterministic sample (12 knowledge-update,
12 temporal-reasoning, 6 preference, 6 abstention), rules frozen before reading:
[`longmemeval.json`](longmemeval.json). Result: Finding 1 **testable at the
threshold** (10 slot-value updates, 5 needing the earlier state); Findings 2 and
3 **not testable** (0 provenance-sensitive, 0 type-dependent). The
`temporal-reasoning` category is date arithmetic over events, not temporal
state, and does not feed Finding 1. Adapter would be Track E-B: writes are
values in free text; oracle flags say *which* turns, not *what* value.

## Seen only by title — not screened

Surfaced by the search and not yet read: DynamicMem (arXiv 2606.22877),
RealMem (2601.06966), ConvoMem (2511.10523), AgentMemBench (2608.00009),
StoryBench (2506.13356), EvoArena (2606.13681), MemoryRewardBench
(2601.11969). Titles suggest dynamic or evolving memory; none is added to the
table until its paper has been read. Listed here so that the candidate set is
recorded before selection, per §18.

## Provisional reading against the three findings

| Mode A finding | where it could be tested externally | risk |
|---|---|---|
| 1 — bitemporal sufficient | LongMemEval knowledge-update + temporal; GoodAI update tests; LoCoMo temporal | low — likely testable |
| 2 — a universal guard helps some types and hurts others | PerLTQA types, if updates exist per type; LongMemEval preference vs. fact | **high — may be `NOT TESTABLE`** |
| 3 — confidence ≠ authority | needs source-dependent conflicts; only speaker-level provenance exists anywhere found | **high — may be `NOT TESTABLE`** |

If inspection confirms the last two rows, that is the §7 result — *existing
benchmarks evaluate recall and update, not provenance- or type-dependent
transition semantics* — and Mode B is designed around Findings 2 and 3. It
is recorded here as the expected outcome before any example is read, so that
it cannot later be presented as a discovery.

## Next action

Inspect ≥ 30 examples each from LongMemEval (`knowledge-update`,
`temporal-reasoning`, `abstention`, a sample of `preference`) and GoodAI LTM
(the tests that update information), classify per §6, and write
`external/triage/longmemeval.json` and `external/triage/goodai-ltm.json`.
Then LoCoMo's temporal subset and PerLTQA's typed subset. Select at most two.
Freeze.
