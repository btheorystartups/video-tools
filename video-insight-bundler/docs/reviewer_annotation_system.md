# Reviewer Annotation System

Phase 35 adds deterministic reviewer annotation scaffolding under `annotations/`. Annotations can be linked to segments, recommendations, blockers, evidence, governance tasks, follow-ups, escalations, accepted-risk rationale, and preserve-as-intentional rationale.

Generated artifacts include `reviewer_annotations.json`, `annotation_timeline_markers.json`, `annotation_group_registry.json`, `annotation_filter_registry.json`, `annotation_review_index.json`, and `annotation_crosslinks.json`.

The review continuity system provides deterministic editorial-review workflow support and audit-preserving operational review continuity. It does not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous creative decisions. Human review is required before production or governance changes.
## Human-Authored Imports

Reviewer worksheets allow human-authored annotations to be exported and re-imported. Imported annotations are normalized to canonical JSON, validated, assigned provenance, and reconciled without overwriting existing annotations.
