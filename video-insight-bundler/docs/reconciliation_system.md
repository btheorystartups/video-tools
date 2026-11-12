# Reconciliation System

The reconciliation system compares imported reviewer responses against existing operational review artifacts and assigns explicit outcomes:

- `appended`
- `merged_cleanly`
- `conflict_detected`
- `requires_manual_review`
- `rejected_invalid`
- `duplicate_ignored`

Reconciliation does not mutate source media, timelines, review registries, governance records, or prior annotations. It writes merge-result artifacts, unresolved conflict queues, imported-vs-existing diffs, dashboard pages, and audit logs.

Operational dashboards under `visualizations/reconciliation/` show import summaries, rejected imports, conflicts, queues, diffs, audit events, and lineage entries. These pages use relative links only and include visible limitation language.
## Phase 37 Adjudication Handoff

Reconciliation conflicts now feed deterministic adjudication workflows under `adjudication/`. Phase 37 does not resolve reconciliation conflicts. It creates manual workflow states, side-by-side reviewer disagreement views, rationale diffs, unresolved ambiguity records, governance conflict analysis, consensus-required records, adjudication queues, arbitration packets, and append-only adjudication lineage.

The reconciliation system remains append-preserving. Imported reviewer records are never silently preferred over existing state, and unresolved reviewer divergence remains visible until a human records an explicit adjudication rationale.

Limitation language is rendered on every adjudication page: “This system provides deterministic reviewer adjudication and governance-conflict workflow support. It does not autonomously resolve reviewer disagreements, infer identity, diagnose emotion, predict viewer behavior, or make autonomous editorial decisions. Human review is required.”
