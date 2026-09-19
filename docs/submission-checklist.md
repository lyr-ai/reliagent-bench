# Submission checklist — *One Order Is Not Enough*

Internal working record for `paper/one-order-is-not-enough.md`. Nothing here
belongs in the manuscript; it lives outside so the draft stays submission-clean.

## Bibliography — verified 2026-09-19

Each entry checked against the source. **Complete.**

| # | Work | Checked |
|---|---|---|
| 1 | MemGPT (Packer et al.) | author list ✓ |
| 2 | A-MEM (Xu et al.) | author list ✓ |
| 3 | AGM 1985 | journal, volume, pages, year ✓ · DOI `10.2307/2274239` added |
| 4 | Snodgrass 1992, LNCS 639 | entry ✓ |
| 5 | Yin, Han & Yu 2008 | volume, pages, DOI ✓ |
| 6 | LoCoMo (Maharana et al.) | authors, ACL 2024 entry ✓ |
| 7 | LongMemEval (Wu et al.) | authors, arXiv id ✓ |
| 8 | MemConflict (Tao et al.) | full author list transcribed ✓ |

## Evidence and wording — settled

- Claim ladder (§9) matches the frozen hierarchy: 2 primary, 1 robustness, 1
  observation, 2 not-established.
- Controls claim qualified to the six complete permutations; `S_only` named.
- R1 claims only robustness to `effort: low → high`, not to reasoning depth.
- `0/60` stated as observed, never as a true zero; Figure 2 annotates `n`.
- Wrong-memory-vs-no-memory is descriptive, with the scenario-level
  heterogeneity reported (4/8/0 declared, 7/3/2 and 7/1/4 epistemic).
- `Typed` in prose, `b_typed` in code, mapping recorded in Reproducibility.
- Exact model snapshot **unavailable** and not inferred — alias, SDK version and
  the three run dates are recorded instead. This stays in the manuscript: it is
  a reproducibility fact, not an internal note.
- Survey claims narrowed so neither is falsified by MemConflict's white-box
  retrieval and ranking analysis.

## Open

- [ ] **Venue and template.** Drives everything below.
- [ ] **Figure sizing.** Figure 2 is currently 10.2 × 4.3 in, double-column. A
      single-column template needs the two panels stacked; `make_figures.py`
      takes the change in one place.
- [ ] **Length.** §5 and §6 carry the most compressible prose; the claim ladder
      and limitations should not be cut.
- [ ] **Anonymisation.** If review is anonymous, the Phase 1 reference becomes
      "a preceding experiment in the accompanying artifact", and the repository
      links in Reproducibility need an anonymised mirror.
- [ ] **Artifact link.** Decide what is released: the frozen results are in-repo,
      the raw responses are large but committed.

## Not blocking

- Protocol v2 exists, is tested, and is wired to nothing. It appears in the paper
  only under future work.
- The second-model replication is gated shut by a pre-registered rule. §10 states
  this as compliance, not omission.
