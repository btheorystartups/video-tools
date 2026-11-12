# Reviewer Adjudication System

Phase 37 adds governed reviewer adjudication for conflicts created by human-review ingestion and reconciliation.

Core artifacts:

- `adjudication/conflict_resolution_registry.json`
- `adjudication/reviewer_adjudication_registry.json`
- `adjudication/reviewer_disagreement_registry.json`
- `adjudication/rationale_diff_registry.json`
- `adjudication/unresolved_ambiguity_registry.json`
- `adjudication/consensus_workflow_registry.json`
- `adjudication/arbitration_packet_registry.json`

The system keeps disagreement visible. It records pending adjudication state, reviewer rationale, evidence references, unresolved concerns, governance impact, escalation state, follow-up requirements, and packet links without changing operational state.

Limitation: This system provides deterministic reviewer adjudication and governance-conflict workflow support. It does not autonomously resolve reviewer disagreements, infer identity, diagnose emotion, predict viewer behavior, or make autonomous editorial decisions. Human review is required.

Phase 38 adds human adjudication event ingestion, event validation, event lineage, provenance, append-only history, governance escalation imports, and outcome dashboards. These event records document human adjudication workflow state without mutating prior adjudication lineage or auto-resolving conflicts.
