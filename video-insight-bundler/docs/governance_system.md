# Release Candidate Governance System

Governance artifacts live under `governance/`:

- `governance_policy.json`
- `readiness_arbitration.json`
- `rc_assessment.json`
- `release_candidate_checklist.json`
- `governance_summary.json`
- `governance_diagnostics.json`
- `governance_failure_explanations.json`
- `rc_threshold_analysis.json`
- `blocker_analysis.json`
- `rc_promotion_path.json`

The governance policy defines minimum corpus size, validation pass rate, artifact integrity, unresolved reference tolerance, failed video tolerance, comparative stability, audit completeness, provenance coverage, mutation risk, and forbidden semantic/cloud runtimes.

Readiness arbitration combines:

- per-video readiness
- corpus readiness
- integrity readiness
- comparative readiness
- audit readiness
- governance readiness

Classification options are `not_ready`, `beta_plus`, `rc_candidate`, and `release_candidate`. The arbitration is conservative: failed videos, validation errors, insufficient corpus size, instability, or weak audit/provenance coverage hold classification down.

Phase 27 extends arbitration context with compressed queue severity, blocker analysis, remediation availability, governance diagnostic clarity, unresolved RC blockers, and promotion path confidence. Remediation availability is diagnostic only and never increases readiness by itself.

`governance_diagnostics.json` explains threshold pass/fail state, near-boundary thresholds, hard blockers, advisory failures, evidence references, and suggested remediation. `rc_threshold_analysis.json` and `rc_promotion_path.json` state what must improve for promotion without lowering standards. `blocker_analysis.json` tracks recurring readiness, pressure, review queue, archetype, validation, audit, comparative, and provenance blockers.

Corpus, workbench, audit, governance, and release-candidate outputs are deterministic editorial-review artifacts. They do not perform autonomous editing, semantic inference, identity recognition, cloud analysis, or media/timeline mutation.

RC hardening and remediation outputs are deterministic review-planning artifacts. They do not apply edits, mutate media, change timelines, perform semantic inference, or make autonomous release decisions.

## Phase 29 Human Governance Workflow

Phase 29 adds review-session snapshots, reviewer decision support, Tier 1 evidence navigation, reviewer focus queues, governance reassessment, readiness delta analysis, governance history snapshots, and replay logs.

The reassessment layer is conservative. Proposed dispositions remain unresolved. Accepted-risk, false-positive, resolved, and externally-reviewed dispositions require decision evidence before they can be treated as non-blocking. If unresolved Tier 1 blockers or failed governance thresholds remain, readiness remains capped at `not_ready`.

## Phase 30 Human Decision Intake

Phase 30 adds a deterministic local intake layer for reviewer decisions. The system generates reviewer templates, validates only canonical `review_input/reviewer_decisions.json`, normalizes valid decisions, rejects invalid decisions with suggested fixes, reconciles valid decisions with Tier 1 blockers, and records provenance and ledger entries.

Invalid decisions never influence readiness. Valid clearing decisions only become reassessment candidates after reconciliation and gatekeeper checks. Raw Tier 1 blocker artifacts remain non-mutating source evidence.

Governance reassessment artifacts are deterministic review and audit artifacts. They do not automatically resolve blockers, apply edits, accept risk, classify false positives, or make autonomous release decisions. Human review is required.

## Phase 31 Governance Dashboard Interpretation

Governance dashboards now expose threshold gaps, readiness status, review queue tiers, blocker disposition, reassessment gatekeeping, and reviewer decision support through explanatory cards and graph detail pages. The pages distinguish deterministic threshold evidence from human creative judgment and keep accepted-risk or false-positive outcomes behind schema-valid human decisions.

Dashboard interpretation and optimization guidance are deterministic editorial-review aids. They do not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous creative decisions. Human review is required before production or editing changes.

Phase 32 governance-oriented UI adds benchmark-aware readiness comparisons, threshold overlays, severity ribbons through metric cards, optimization effort estimates, and compare workflows. Governance pages continue to enforce evidence precedence: recommendations and effort estimates never clear blockers or promote readiness without schema-valid human decisions.

The expert dashboard system provides deterministic editorial-review guidance and optimization interpretation. It does not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict audience behavior, or make autonomous creative decisions. Human review is required before production or editorial changes.
## Temporal Governance Review

Governance blockers are exposed as timeline review signals and recommendation pins when source segment evidence is available. These pages do not clear blockers or change readiness; validated human decisions remain required.

Phase 34 surfaces governance relevance in persistent context panels, review-state summaries, shortcut links, and workstation crosslinks. These surfaces do not loosen thresholds, auto-resolve blockers, or change readiness without validated human decisions.

## Phase 35 Governance Continuity

Governance review now has persistent operational support through escalation registries, governance queues, follow-up items, reviewer rationale records, activity history, governance review packets, and printable handoff packets. These artifacts preserve conservative review-state management and require explicit human review before any governance or production change.

The review continuity system provides deterministic editorial-review workflow support and audit-preserving operational review continuity. It does not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous creative decisions. Human review is required before production or governance changes.
## Human Review Import Governance

Human review ingestion preserves governance conservatism. Imported accepted-risk, escalation, or blocker-related reviewer content is never allowed to clear governance blockers automatically; conflicts become unresolved reconciliation queue items.
## Phase 37 Governance Conflict Handling

Governance-sensitive reviewer conflicts are now surfaced in `adjudication/governance_conflict_analysis.json`. The analysis identifies blocker disagreement, escalation disagreement, accepted-risk disagreement patterns, evidence sufficiency disagreement, review completeness disagreement, and unresolved governance ambiguity.

Governance conflict outputs do not change readiness, clear blockers, accept risk, or promote release state automatically. They generate visibility, arbitration packets, and queues for human governance review while preserving reconciliation lineage and reviewer divergence.
