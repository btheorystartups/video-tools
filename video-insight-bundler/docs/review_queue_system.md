# Review Queue System

Phase 35 creates operational review queues under `queues/`. Queue subsets cover high-priority review, low-effort/high-impact review, unresolved blockers, escalation-required items, governance review, pacing review, and rhetorical review.

Each queue item carries related artifacts, severity, effort estimate, expected review time, related recommendations, related annotations, related segments, governance items, suggested next action, and deterministic priority score.

The review continuity system provides deterministic editorial-review workflow support and audit-preserving operational review continuity. It does not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous creative decisions. Human review is required before production or governance changes.
## Reconciliation Queues

Phase 36 adds queues for unresolved import conflicts, imports requiring reconciliation review, and imported follow-ups. These queues make merge risk explicit and prevent hidden reviewer-state changes.
