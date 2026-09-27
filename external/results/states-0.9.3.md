# TypedMem 0.9.3 states: results against the pre-registration

Predictions: `external/predictions/states-0.9.3.md`. The external runs were
committed at `7d50e01`; the Mode A addendum at `6011bb7`, before Mode A ran.
Nothing in any benchmark was changed. Environment: TypedMem 0.9.3 from PyPI.

## Reproducibility

In the fresh 0.9.3 environment, every pre-existing variant reproduces its
committed row exactly: the six LongMemEval/GoodAI variants, and the four
Mode A variants (`analysis/mode-a-pilot.md`). TypedMem 0.9's changes did not
move the typed-memory results.

## External runs: as predicted

| | v4_replace (issue #5) | v4_keep_both | v0_scd_g (bitemporal) | **v9_states** | predicted |
|---|---|---|---|---|---|
| LongMemEval KU, all usable | 54/65 | 65/65 | 65/65 | **65/65** | 65/65 |
| · historical / both / direction | 0/6 · 0/2 · 0/3 | 6/6 · 2/2 · 3/3 | 6/6 · 2/2 · 3/3 | **6/6 · 2/2 · 3/3** | same |
| · current state / abstention | 53/53 · 6/6 | 53/53 · 6/6 | 53/53 · 6/6 | **53/53 · 6/6** | same |
| GoodAI (Colours · NameList · SallyAnne) | 3 · 0 · 1 of 3 | 3 · 3 · 3 | 3 · 3 · 3 | **3 · 3 · 3** | same |

States close every `history_under_replace` failure these runs recorded, and
they only **tie** the keep-both and bitemporal baselines. These runs feed
ordered, single-source statements, so they cannot separate states from
those baselines. The named NameList risk (a repeated name recorded as
corroboration) did not occur: no script repeats a name.

## Mode A: where states differ from the gold

| Variant | state | temporal | transition | corruption | authority | temporal | typed | known_gap |
|---|---|---|---|---|---|---|---|---|
| v4_typedmem | 0.89 | 0.84 | 0.96 | 0.00 | 1.00 | 1.00 | 1.00 | 0.33 |
| v0_scd_g | 0.85 | 1.00 | 0.71 | 0.44 | 0.67 | 1.00 | 0.67 | 0.83 |
| **v9_states** | **0.81** | **1.00** | 0.69 | **0.22** | **0.50** | 1.00 | **0.67** | 0.75 |

Against the scenario-level predictions:
- **13 of the 14 predicted failures failed**, for the predicted reasons:
  - conflict instead of a silent veto: A-01, A-04, A-06, A-07, A-10, G-04, G-07 answer `None`;
  - no confidence guard: C-02, C-03, C-07, G-05, where a newer, less-confident value becomes current;
  - no "always replace" type: C-09, C-10, where an older write is filed in history instead of replacing.
- **Corruption 0.22, as predicted.** All four corrupted writes are confidence-guard cases (C-02, C-03, C-07, G-05).
- **Prediction wrong, better than predicted: A-08.** The weaker inference describes an *older* state, so states file it as history and the stronger current value stands. Correct.
- **Prediction wrong, worse than predicted: A-02.** A user statement (authority 1.0, observed later, `valid_from` 2024, no end) against a model inference (0.3, `valid_from` 2026-08). The gold reads the user statement as describing the past, so Seattle is current. States read an open-ended claim from a stronger source as still asserted: the weaker, later Seattle can't end it, so they report a **conflict**. This is a semantic question the states design had not faced: should a weaker source be able to end a stronger claim that starts earlier?

## Answers to the three questions

1. **Current truth.** No change where sources agree: 53/53 and 3/3, the same as
   every variant. Where they disagree, states are *less* accurate against this
   gold: by design they report conflicts instead of vetoes (authority 0.50),
   and they have no per-type confidence guards (typed 0.67).
2. **Historical queries.** They go to the ceiling everywhere measured:
   11/11 LongMemEval history questions (v4_replace: 0/11), 9/9 GoodAI,
   Mode A temporal 1.00 (v4: 0.84), and all four history-under-replace
   known-gap scenarios.
3. **Old failures that still need typed-memory history.** **None of the
   measured history failures.** What states can't express is typed-memory
   *policy*: confidence guards, "always replace" types, and silent authority
   vetoes. That is the typed core's job, not history.

## Implications for TypedMem

- **Issue #5** (typed-memory REPLACE loses history): every measured history
  need is met by states. Nothing here argues for giving REPLACE a history;
  keep it *not now*.
- **A-02 remains a disagreement**, deliberately not "fixed". The benchmark's
  gold assumes a later start ends an earlier open-ended claim. TypedMem's
  state contract (owner decision D2, 2026-09-27) does not: a later start time
  doesn't show that an earlier open-ended claim has ended. When overlapping
  claims can't be put in time order without inventing an end date, they stay
  in conflict, and authority keeps a weaker overlapping claim from silently
  ending a stronger one. A-08 is the contrast: there the weaker claim
  describes an *earlier* state, time order is known, and it goes into history.
  The benchmark measures one semantic assumption; TypedMem deliberately
  chooses another.
- **States don't replace the typed core; they solve a different problem.** States are strongest on current value, history and late arrival; the typed core on authority vetoes and per-type policies. The authority and typed rows are the cost of states' single contract.
  That trade-off was chosen in design 0002. It is now measured, not assumed.
