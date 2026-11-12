# Conflict Resolution Workflow

Conflict workflows are explicit manual review records derived from reconciliation conflicts.

Supported states:

- `unresolved`
- `under_review`
- `escalation_required`
- `governance_review_required`
- `consensus_required`
- `partially_resolved`
- `resolved_with_rationale`
- `deferred`

The generator never transitions a conflict to `resolved_with_rationale` automatically. Resolution requires a human reviewer to record rationale outside the deterministic scaffold.

Workflows preserve conflict type, source item, queue references, reviewer role labels, required manual actions, unresolved questions, and append-only history requirements.

Phase 38 records human adjudication and escalation events as additional workflow evidence. Imported events can document decisions, continuations, deferrals, or escalations, but they do not automatically close conflicts.
