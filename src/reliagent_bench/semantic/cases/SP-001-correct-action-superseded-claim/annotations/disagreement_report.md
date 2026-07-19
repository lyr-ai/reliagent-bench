# SP-001 — annotation & disagreement report

One case, annotated twice, to test whether **the case and the methodology** are sound
before authoring SP-002. The disagreements — not the agreements — are the data.

## Method

- **Annotation A** applied the five-type ontology (Evidence/Claim/Conflict/Decision/Transition).
- **Annotation B** started from the raw facts and used the smallest ontology that still
  expresses the failure (Observation / State-timeline / Decision — 3 concepts).

### Honest limitation (read this first)

Both annotations were produced by a **single annotator, in one session**. That is *not*
a valid RQ3 (inter-annotator reproducibility) measurement — RQ3 requires genuinely
independent annotators and real temporal separation, neither of which a single agent
can self-certify. What this pass *can* legitimately test is narrower and still useful:
whether the case is **stateable neutrally**, whether the operational baseline **omits
the answer**, and whether **more than one ontology** can recover the diagnosis. Treat
the "agreement" below as a soundness check on the case, not evidence about people.

## Where the two annotations agreed

Both reached the **same diagnosis**: the recommendation is justified by a
certificate-state value that a later observation superseded; the action's correctness
does not remove the provenance defect. Agreement held **despite different graph
structure** — A used Claim nodes + a Transition node; B used a state timeline with an
`as_of` pointer. This is the point of a diagnosis-based ground truth: structure differed,
finding matched.

## Points of hesitation (the real signal)

1. **"Certificate was renewed" — Evidence or Transition?** It is an *observation*
   (Evidence); the *state change* it implies is the Transition. Easy to conflate the
   two. A represented both (E2 and T1); B collapsed the transition into timeline order.
2. **"Certificate is valid" — explicit Claim or derived state?** A made it a Claim (C2);
   B made it a timeline value. Genuine divergence in node identity — same fact, different
   object. Neither is obviously more correct.
3. **Supersession — Conflict, relation, or temporal edge?** Both annotators concluded it
   is **not a Conflict**: O1→O2 is a legitimate temporal update, not a contradiction. A
   modeled it as a Transition node; B as ordering in a timeline. **The Conflict node was
   never used.**
4. **Does the recommendation need a Decision node?** Yes — both kept a decision object,
   because the decision is the locus of the defect. This is the one node type both
   ontologies agreed is required.

## Preliminary ontology signal (n=1 — do not generalize)

For this F6-style failure, **Conflict was unused and Transition-as-a-node was not
required** (B expressed it as a timeline ordering). That is weak, single-case evidence
pointing toward a **smaller ontology** (the Outcome-D direction). It is one case; it
means nothing until it recurs across the contradiction / cascading-dependency categories,
where Conflict may well become necessary.

## A case-design flag to resolve before SP-002

`ground_truth.final_action_acceptable: true` is **debatable given the facts as written.**
O2 says the certificate is *already renewed and valid*, so `recommend_certificate_renewal`
is arguably *unnecessary* — an annotator could reasonably diagnose a **task error (redundant
action)** rather than, or in addition to, a provenance defect. That ambiguity risks
contaminating the very distinction the case exists to isolate (justification defect vs.
action correctness).

Two clean fixes, pick one before scaling:
- **(preferred)** flip the polarity so the action is unambiguously correct: O1 = "valid",
  O2 = "expired / invalid" → renewal *is* warranted, but the decision cites the superseded
  "valid" claim. Action correct, justification stale — no redundancy confound.
- keep the facts but change the action to one that is unambiguously fine regardless
  (e.g., `notify_owner_of_status`) so action-correctness cannot compete with the
  provenance finding.

## Exit-criteria assessment

| # | Question | Verdict |
|---|---|---|
| 1 | Ground truth stateable without StateGraph vocabulary? | **Yes** — `ground_truth.yaml` uses "superseded state / decision depends on earlier state." |
| 2 | Does the operational trace omit the decisive relationship? | **Yes** — events + success only; no dependency edge, no supersession edge. |
| 3 | Can both five-type and a simpler ontology represent it? | **Yes** — A used 4 of 5 types; B used 3 concepts. |
| 4 | Two annotations agree on root cause despite different structure? | **Yes on the diagnosis** — but see the single-annotator limitation; not a real RQ3 result. |
| 5 | Evaluation on diagnosis, not exact graph matching? | **Yes** — ground truth scores findings; `not_required` explicitly frees Conflict/Transition. |

**Overall:** the case largely satisfies its own exit criteria, with **one substantive
flag** (criterion-1/2 neutrality is fine, but the action-acceptability ambiguity above
should be fixed) and **one standing caveat** (criterion 4 needs a genuinely independent
second annotator to count for RQ3). Recommend revising SP-001's polarity, then — before
SP-002 — getting one truly independent annotation to convert criterion 4 from "plausible"
to "measured."
