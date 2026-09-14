# Phase 2 — per-type governing-state semantics

**Status:** frozen before any Phase 2 scenario is written.
**Rule for this document:** every argument must stand without reference to
how TypedMem (or any system) is implemented. A rule is justified by what the
state type *means*, or it is not justified.

## 0. Vocabulary

A slot holds one *governing* memory: the one an agent should act on now. An
incoming memory competes with the existing governing one on three
comparable dimensions:

```text
S   source priority     verified_result = explicit_user  >  document  >  observed_behavior  >  model_inference
C   confidence          the writer's own certainty in the claim, 0–1
R   recency             the incoming memory is observed later (Phase 2 holds this fixed: incoming is always newer;
                        the "newer observation of an older state" case is a separate small block, see §4)
```

A *guard* is a condition the incoming memory must satisfy to govern. Each
type below is defined by which guards apply. "No weaker on S" means
`S_in ≥ S_ex`; "no weaker on C" means `C_in ≥ C_ex`.

## 1. The table

| state type | semantic question | governs when incoming is… | what must NOT dominate | typical update |
|---|---|---|---|---|
| **factual state** | what is currently true of the world? | no weaker on S **and** no weaker on C | recency alone; a newer, less certain claim | "lives in San Jose" → "probably Seattle" |
| **deadline** | what is the latest accepted time constraint? | no weaker on S — confidence irrelevant | an older, more confidently stated date | Friday → "moved to Monday" |
| **commitment** | what has the actor most recently committed to? | no weaker on S and from an explicit source — confidence irrelevant | permanent dominance of an old explicit statement; an inference that the actor "would" commit | "won't use X" → "changed my mind, use X" |
| **explicit preference / constraint** | what stated preference or rule should guide action? | no weaker on S — confidence irrelevant; among explicit statements the latest | behavioural or model inference overriding an explicit statement | "prefer aisle" vs "seems to book window" |
| **verified operational result** | what state has been externally established? | no weaker on S — verified beats everything; among verified the latest | a model's belief about a tool's evidence | CI failing → "probably a flake" |
| *inferred trait* (secondary) | what hypothesis is best supported? | evidence aggregation, not replacement | one explicit-looking, low-evidence overwrite; hard replace in either direction | "prefers concise" from mixed evidence |

## 2. Per-type argument

Each entry: definition · what a correct update is · why no single dimension
may rule alone · a counterexample · how general the rule is.

### 2.1 Factual state

*Definition.* A claim about how the world currently is, whose truth does
not depend on the speaker's intent: a location, a configuration value, a
count.

*Correct update.* A fact changes when better-or-equal evidence says so.
"Better" has two parts: the source is at least as entitled to speak, and
the claim is at least as certain. Recency contributes nothing by itself —
the world does not become different because someone guessed later.

*Why no single dimension.* Recency-only lets a guess overwrite knowledge.
Confidence-only lets a confident guess overwrite a modestly stated
observation. Source-only lets an explicit but hesitant restatement ("I
think I was born in Dallas?") overwrite an explicit certain one.

*Counterexample.* Explicit "born in Austin" (C 0.9), then explicit "I think
Dallas, not sure" (C 0.4). Newest-wins writes Dallas onto a form.

*Generality.* Domain-general. The rule is the ordinary epistemics of a
belief: revise on evidence, not on time.

### 2.2 Deadline

*Definition.* A time constraint that someone with standing has set. It is
not a fact about the world; it is a fact about what has been decided.

*Correct update.* The latest decision by anyone entitled to make it. A
deadline moved yesterday is the deadline, however tentatively it was
announced; the previous one was superseded by the act of moving it.

*Why no single dimension.* Confidence must not guard: a decision does not
need to be certain to be the decision. Source must guard: a model's
inference that the deadline "probably moved" is not a decision. Recency is
decisive only within admissible sources.

*Counterexample.* "Deadline is Friday" (C 0.9), then "moved to Monday"
(C 0.5). A confidence-before-recency policy schedules for a date that no
longer exists.

*Generality.* General to any *decided* state — schedules, budgets,
assignments — where the thing recorded is an act, not an observation.

### 2.3 Commitment

*Definition.* A position the actor has taken about their own future conduct.
It binds because the actor said so, and can be released only the same way.

*Correct update.* The actor's latest explicit position. A revision does not
need to be emphatic; "I've changed my mind" revises, and an old commitment
stated with total certainty is no longer the commitment.

*Why no single dimension.* Confidence must not guard — a hesitant retraction
is still a retraction. Source must guard tightly: an inference that the
actor "would now accept X" is not a commitment, and an observation of the
actor doing X once is not a revision. Only explicit statements from a source
entitled to commit can move this state.

*Counterexample.* "I will not use library X" (C 1.0), then "changed my
mind, fine to use X" (C 0.8). A policy that ranks confidence above recency
refuses the library the user just accepted.

*Generality.* General to promises, opt-ins, standing instructions the actor
owns. Not general to constraints set by *someone else* (those are
explicit constraints, 2.4).

### 2.4 Explicit preference / constraint

*Definition.* A stated preference or rule that should shape action: "I
prefer aisle"; "customer emails need approval". Distinct from a commitment
in that it guides choices rather than binding conduct, and may be set by a
different party than the actor.

*Correct update.* The latest explicit statement from a source no weaker than
the existing one. Behaviour that appears to contradict a stated preference
does not revise it — people book window seats when aisle is sold out.

*Why no single dimension.* Recency-only lets an inference from behaviour
overwrite a statement. Confidence-only lets a confident inference do the
same. Source guards; among explicit statements, the latest speaks.

*Counterexample.* "I prefer aisle" (explicit), then "seems to prefer
window" (observed behaviour, C 0.85). Newest-wins books the window.

*Generality.* General to stated preferences and rules. Does not cover
preferences the actor has *never* stated — those are inferred traits (2.6).

### 2.5 Verified operational result

*Definition.* State established by a tool or external system: a test run, a
CI status, a deployment outcome. It is evidence, not opinion.

*Correct update.* A newer verified result supersedes an older one. Nothing
un-verified supersedes a verified result — a model's belief that a failure
"was probably a flake" does not make CI green.

*Why no single dimension.* Confidence is meaningless across the verified /
inferred boundary: the inference can be 0.99 confident and still be a
guess about evidence it did not produce. Recency is decisive only among
verified results.

*Counterexample.* CI: FAILING (verified), then "probably transient" (model
inference, C 0.9). A recency- or confidence-first policy merges a failing
PR.

*Generality.* General wherever a system of record exists. The rule is simply
that record beats belief.

### 2.6 Inferred trait — secondary

*Definition.* A hypothesis about the actor, held on the strength of
accumulated evidence rather than a statement: "prefers concise answers".

*Correct update.* Not replacement at all: evidence aggregates, confidence
moves, and a single new observation should shift the hypothesis rather than
overwrite it. An explicit statement from the actor converts the trait into
an explicit preference (2.4) — it leaves this type.

*Why it is secondary.* Its correct semantics are probabilistic, and any
scenario that forces a *replace* decision on it can be argued either way.
It is therefore not used in any core reversal pair (§3), and any result on
it is reported as exploratory.

## 3. What the table implies for the experiment — stated before running it

Reading the "governs when" column:

```text
factual state            S-guard  AND  C-guard
deadline                 S-guard
commitment               S-guard (explicit only)
explicit preference      S-guard
verified result          S-guard (verified top)
```

**Every core type shares the source guard.** The types differ on whether
*confidence* also guards, and that is the only axis on which the four
low-controversy types disagree. Two consequences follow, and both are
predictions:

1. **A fixed source ranking is expected to be sufficient for every conflict
   whose only difference is source.** That is Phase 1's BRQ1/F3 result and
   it is expected to hold in Phase 2. The paper claims nothing else for
   provenance.
2. **Every reversal pair among the core types lives on the confidence-vs-
   recency axis.** The pattern *equal source, lower confidence, newer*
   resolves to the *existing* memory for a factual state and to the
   *incoming* memory for a deadline, a commitment, or an explicit
   preference. Any fixed ordering that places C before R fails the latter
   three; any that places R before C fails the fact. Orderings that place C
   or R before S fail every type on source conflicts. So the E1 prediction
   is specific: **no fixed ordering is correct on all four core types, and
   the ones that come closest split exactly on fact vs. the other three.**

If E1 finds an ordering that is correct on all four, this table is wrong
somewhere and the claim is withdrawn.

## 4. The held-out block: newer observation of an older state

A write that is observed later but describes an *earlier* state (validity
start before the existing one) is excluded from the main matrix — every
type resolves it the same way (the existing, later-effective state stands),
so it cannot produce a reversal pair. It is kept as a small consistency
block so that no variant is rewarded for mishandling validity.

## 5. Admissible disagreements

Where a reasonable reader could dispute the table, said now so that gold is
not mistaken for the author's taste:

- **Commitment vs. preference.** Some would merge them. They are kept apart
  because a commitment binds the committer and can only be released by the
  committer, while a constraint can be set by another party. Where a
  scenario cannot make that distinction matter, it is labelled preference.
- **Deadline moved by a low-priority source.** If a calendar system
  (observed) moves a deadline that a person set (explicit), the source guard
  as written holds the old date. Some would let the system win. Such
  scenarios are excluded from the core pairs; the calendar case is written
  as a verified result when it is used at all.
- **Inferred trait**, as above — excluded from core pairs.
- **Confidence on decided state.** A reader might hold that a deadline
  announced at confidence 0.5 is not yet a deadline. The table's position
  is that a decision is a decision; the tentativeness belongs to the
  announcer, not the state. Scenarios keep the incoming confidence at or
  above 0.5 so that the objection is about principle, not about a
  throwaway remark.

## 6. Core and secondary types for Phase 2

```text
core        factual state · deadline · commitment · explicit preference / constraint
consistency verified operational result   (used in source-only cases and controls; no reversal pairs)
secondary   inferred trait                (exploratory; never in the headline result)
```

Reversal pairs are derived from this table, one row against another on the
confidence-vs-recency pattern, after this file is frozen — not the other
way round.
