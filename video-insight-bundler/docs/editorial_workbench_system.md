# Editorial Workbench System

The editorial workbench is a static local review layer generated under `workbench/` and `visualizations/`.

It ranks:

- videos needing review
- segments needing review
- recommendations needing review
- chronic pressure regions
- contradiction-heavy regions
- high-uncertainty counterfactuals
- high-impact low-confidence recommendations

Every review item includes a priority score, reason, source video, artifact path, evidence references, suggested human action, and a non-mutating status.

The workbench is static HTML and JSON only. It does not start a server, mutate media, apply edits, or call external services.

Corpus, workbench, audit, governance, and release-candidate outputs are deterministic editorial-review artifacts. They do not perform autonomous editing, semantic inference, identity recognition, cloud analysis, or media/timeline mutation.
## Phase 27 Review Queue Compression

The workbench now includes compressed review planning outputs:

- `workbench/compressed_review_queue.json`
- `workbench/review_queue_tiers.json`
- `workbench/review_queue_clusters.json`
- `workbench/review_queue_summary.json`
- `workbench/next_best_human_actions.json`

Compression groups duplicate and overlapping items by video, issue family, archetype, recurring blocker, and evidence references. Each compressed item preserves original raw queue IDs in `original_item_refs`, so the raw queue remains the source of record.

Tiering is conservative: Tier 1 is reserved for RC blockers, Tier 2 for high-impact corpus blockers, Tier 3 for recurring pressure or archetype issues, Tier 4 for per-video improvements, and Tier 5 for informational or audit-only items.

## Phase 29 Review Navigation

The workbench now writes `review_navigation_index.json`, `tier_1_evidence_navigation.json`, `reviewer_focus_queue.json`, and `reviewer_session_summary.json`.

These artifacts organize Tier 1 blockers by blocker family, video, segment, archetype, pressure family, governance severity, readiness impact, review effort, likely false-positive potential, and likely accepted-risk potential. They preserve evidence refs and raw review queue refs so a reviewer can inspect the same source artifacts from the static dashboard.

## Phase 30 Decision Intake Workbench

The static workbench now links decision intake status, reviewer templates, validation results, rejected decisions, reconciliation summaries, governance ledger entries, and reassessment gatekeeper output. All pages remain static, use relative links, and open directly from disk.

Navigation artifacts do not apply decisions or change readiness. They reduce review overhead while preserving conservative governance.

RC hardening and remediation outputs are deterministic review-planning artifacts. They do not apply edits, mutate media, change timelines, perform semantic inference, or make autonomous release decisions.

## Phase 31 Expert Dashboard UX

The workbench now uses expert graph cards and detail pages. Each major graph card explains what the artifact measures, why it matters, current status, practical optimization options, evidence references, and what not to infer.

Optimization guidance is advisory and non-mutating. Suggested actions include preserve as-is, edit pacing, add examples, add transitions, add visual resets, clarify argument structure, re-record only after review, or accept an intentional style.

Dashboard interpretation and optimization guidance are deterministic editorial-review aids. They do not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous creative decisions. Human review is required before production or editing changes.

## Phase 32 Expert Review Workflow

The workbench now includes metric cards, recommendation ranking, effort estimates, segment drilldown tables, and compare workflows. These pages improve operational review density by separating scan-level status, evidence-level details, and production-planning guidance.

The expert dashboard system provides deterministic editorial-review guidance and optimization interpretation. It does not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict audience behavior, or make autonomous creative decisions. Human review is required before production or editorial changes.
## Timeline Review Workflow

The workbench links into temporal review journeys so reviewers can move from queue item to timeline segment, evidence, recommendation lineage, and human decision intake without relying on external services.

Phase 34 adds workstation cards from the dashboard and workbench into the advanced timeline workstation. The cards link to enhanced timelines, overlay filters, temporal heatmaps, shortcuts, review-state summaries, and compare readability pages.

## Phase 35 Operational Continuity

The editorial workbench now links to review continuity dashboards for session memory, annotation review, progress tracking, resume navigation, follow-up tracking, queue review, escalation handling, activity history, printable packet export, and reviewer rationale capture. These pages turn the static workbench into an audit-preserving editorial operations surface without adding a runtime service.

The review continuity system provides deterministic editorial-review workflow support and audit-preserving operational review continuity. It does not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous creative decisions. Human review is required before production or governance changes.
