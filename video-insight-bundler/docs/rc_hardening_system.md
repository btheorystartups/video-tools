# RC Hardening System

Phase 27 adds deterministic release-candidate hardening for corpus outputs.

The system writes compressed queue artifacts under `workbench/`, governance diagnostics under `governance/`, remediation planning artifacts under `remediation/`, static reports under `reports/`, PNG charts under `graphs/`, direct-from-disk HTML pages under `visualizations/`, schemas under `schemas/`, and `verification_evidence/rc_hardening_validation.json`.

The hardening pass explains why a corpus remains below RC, which thresholds failed or are near a boundary, which blockers recur, which archetypes need human guidance, and which actions are useful next. It keeps raw queue traceability through original item references.

RC hardening and remediation outputs are deterministic review-planning artifacts. They do not apply edits, mutate media, change timelines, perform semantic inference, or make autonomous release decisions.

## Limitations

The outputs are review planning evidence. They do not prove semantic truth, infer author intent, identify people or objects, call cloud APIs, generate embeddings, use vector databases, call LLMs, call Resolve, or mutate media.
