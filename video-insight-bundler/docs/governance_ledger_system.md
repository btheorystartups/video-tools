# Governance Ledger System

Phase 30 adds a local governance ledger for validated human decision events.

The ledger is written to `governance/governance_ledger.json` with an index at `governance/governance_ledger_index.json`. Entries include the run ID, timestamp, event type, blocker ID, decision ID, prior and new state, reviewer name, evidence references, source artifacts, validation status, reconciliation status, readiness effect, and deterministic hash.

When a prior ledger exists in the output directory, entries are merged by deterministic `ledger_entry_id`. If a force rerun deletes managed output directories before ledger generation, prior snapshots may not be available; the artifact records this replacement behavior instead of silently claiming durable append-only persistence.

Ledger entries are audit evidence only. They do not mutate raw blocker artifacts, source media, timelines, or readiness state. Reassessment movement is controlled by validated decisions, reconciliation, and the reassessment gatekeeper.
