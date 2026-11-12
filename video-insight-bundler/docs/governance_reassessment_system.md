# Governance Reassessment System

Phase 29 adds deterministic governance reassessment after human blocker decisions are present.

Generated artifacts:

- `governance/governance_reassessment.json`
- `governance/governance_reassessment_delta.json`
- `governance/governance_history.json`
- `governance/governance_replay_log.json`
- `governance/governance_snapshot_registry.json`
- `verification_evidence/governance_reassessment_validation.json`

The reassessment records resolved blockers, remaining blockers, reclassified blockers, readiness delta, classification delta, changed thresholds, still-failing thresholds, evidence refs, and explanations for both readiness movement and no-change outcomes.

Readiness delta analysis tracks threshold movement, blocker movement, review queue changes, disposition changes, confidence movement, and governance severity movement. Unexplained readiness jumps are explicitly flagged.

If unresolved Tier 1 blockers remain, or if non-blocking dispositions lack evidence, the hardening cap remains active and readiness remains capped at `not_ready`.

Phase 30 routes human dispositions through `validated_human_decisions.json`, `decision_reconciliation.json`, and `reassessment_gatekeeper.json` before reassessment. Reassessment may consider only validated and reconciled clearing decisions. If no valid clearing decisions exist, or if any Tier 1 blocker remains unresolved, readiness remains capped.

Governance reassessment artifacts are deterministic review and audit artifacts. They do not automatically resolve blockers, apply edits, accept risk, classify false positives, or make autonomous release decisions. Human review is required.

Phase 31 adds explanatory reassessment and delta pages. The dashboard clarifies why readiness changed or remained capped, which evidence artifacts support that state, and which optimization or review actions remain non-mutating.

Dashboard interpretation and optimization guidance are deterministic editorial-review aids. They do not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous creative decisions. Human review is required before production or editing changes.
