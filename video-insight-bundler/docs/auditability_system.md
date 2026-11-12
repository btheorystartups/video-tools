# Auditability System

Audit artifacts live under `audit/`:

- `audit_trail.json`
- `validation_replay.json`
- `provenance_reconstruction.json`
- `artifact_replay_index.json`
- `evidence_traceability.json`

The audit trail records source hashes, analysis commands, profile hashes, dependency versions, schema validation statuses, generated artifact hashes, warnings, limitations, and a non-mutation statement.

Validation replay lists replayable checks for schema validation, reference validation, dashboard links, PNG/HTML/JSON checks, and corpus-level validation artifacts.

Provenance reconstruction links:

- readiness to evidence artifacts
- recommendations to evidence and segment IDs
- corpus recommendations to per-video evidence
- governance decisions to readiness, integrity, audit, and provenance artifacts

Evidence precedence remains: source hashes and deterministic IDs, schema/integrity validation, explicit transcript/timing evidence, multimodal deterministic consensus, corpus/audit/governance sidecars, then human review.

Corpus, workbench, audit, governance, and release-candidate outputs are deterministic editorial-review artifacts. They do not perform autonomous editing, semantic inference, identity recognition, cloud analysis, or media/timeline mutation.
## RC Hardening Auditability

Phase 27 adds `verification_evidence/rc_hardening_validation.json`. The validation checks compressed queue references, blocker references, remediation references, evidence references, threshold references, video references, and expected artifact paths.

Phase 29 adds `verification_evidence/governance_reassessment_validation.json`. The validation checks cap preservation when unresolved blockers remain, delta explanation presence, governance history snapshots, navigation evidence refs, and expected Phase 29 artifact paths.

Phase 30 adds `verification_evidence/human_decision_intake_validation.json`. The validation covers reviewer decision templates, validated decisions, rejected decisions, reconciliation output, governance ledger output, reassessment gatekeeper output, and decision provenance.

Governance history snapshots and replay logs are audit artifacts only. They do not authorize RC promotion or mutate media.

The raw review queue is never deleted or rewritten by compression. Compressed items keep `original_item_refs`, remediation items keep `source_issue_id`, and governance diagnostics keep threshold and evidence references.

RC hardening and remediation outputs are deterministic review-planning artifacts. They do not apply edits, mutate media, change timelines, perform semantic inference, or make autonomous release decisions.
