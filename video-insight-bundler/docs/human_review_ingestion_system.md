# Human Review Ingestion System

Phase 36 adds deterministic, local-first intake for human-authored reviewer content. The system generates reviewer templates, imports completed local responses into canonical JSON, validates them, and passes only validated records into reconciliation artifacts.

Supported imported content includes annotations, rationale, decisions, follow-ups, escalation notes, and checkpoint continuations. Imports are append-preserving: existing review state is compared but not silently overwritten.

Safety rules:

- Invalid review states, escalation states, duplicate import IDs, orphaned source references, and incompatible checkpoints are rejected before reconciliation.
- Conflicting decisions or escalation states are queued as unresolved conflicts.
- Governance-relevant conflicts never clear blockers automatically.
- Provenance, canonical hashes, merge results, lineage, audit events, and queues are written as static artifacts.

Limitation: This system provides deterministic editorial-review ingestion and reconciliation support. It does not autonomously resolve governance decisions, infer identity, diagnose emotion, predict viewer behavior, or make autonomous editorial decisions. Human review is required.
