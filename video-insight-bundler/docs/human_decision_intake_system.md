# Human Decision Intake System

Phase 30 adds deterministic local human decision intake for Tier 1 blocker dispositions.

Reviewer-authored decisions live under `Corpus_analysis/review_input/`. The canonical automated intake file is `reviewer_decisions.json`. The system also writes `reviewer_decisions.template.json`, `reviewer_decisions.template.csv`, `reviewer_decisions.template.md`, and `reviewer_decisions_readme.md` so reviewers can prepare decisions without editing governance artifacts directly.

Allowed dispositions are `proposed`, `confirmed_blocker`, `externally_reviewed`, `accepted_risk`, `deferred`, `resolved`, and `false_positive`.

Validation requires a current `blocker_id`, matching `source_compressed_item_id`, allowed disposition, reviewer name, ISO review date, confidence, rationale, evidence note, and any disposition-specific reason. Clearing dispositions require evidence references. Invalid, incomplete, mismatched, or unsupported decisions are written to `governance/rejected_human_decisions.json` and cannot influence readiness.

Validated decisions are normalized to `governance/validated_human_decisions.json`, reconciled in `governance/decision_reconciliation.json`, checked by `governance/reassessment_gatekeeper.json`, and traced in `governance/decision_provenance.json`.

Human decision intake artifacts are deterministic local governance-review artifacts. They do not apply edits, mutate media, accept risk automatically, classify false positives automatically, or make autonomous release decisions. Only explicit, schema-valid human decisions can influence reassessment.

Phase 31 dashboards surface decision intake, validation, reconciliation, ledger, and reassessment gatekeeper status with explanatory panels. These pages help reviewers understand what a valid local decision can and cannot change.

Dashboard interpretation and optimization guidance are deterministic editorial-review aids. They do not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous creative decisions. Human review is required before production or editing changes.

## Limitations

CSV and Markdown files are templates and review aids. Only JSON is canonical for automated validation. Templates are never treated as valid decisions. Reassessment remains conservative while any Tier 1 blocker is unresolved or any other governance threshold fails.
