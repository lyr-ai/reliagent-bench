# Track C — Semantic provenance (cases)

Methodology and rationale: [`docs/semantic-provenance-plan.md`](../../../docs/semantic-provenance-plan.md).
This directory holds the cases. **Cases are neutral** — they name no ontology and no
failure mechanism, so any representation (five-type or simpler) is scored on the same
diagnosis-based ground truth.

Each case is a directory of four artifacts:

- `case.yaml` — scenario + evaluation task (no failure hints)
- `operational_trace.json` — the operational baseline (events + success; no semantic edges)
- `semantic_input.yaml` — representation-neutral source facts to annotate from
- `ground_truth.yaml` — the diagnosis that must be recovered (scored on findings, not graph shape)

Annotation experiments for a case live under its `annotations/`.

Status: **one case (SP-001)**. Per the plan's first exit criterion, SP-002 is not
authored until SP-001's methodology questions are answered by evidence — see its
[`annotations/disagreement_report.md`](cases/SP-001-correct-action-superseded-claim/annotations/disagreement_report.md).
