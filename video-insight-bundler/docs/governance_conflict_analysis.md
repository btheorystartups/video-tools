# Governance Conflict Analysis

Governance conflict analysis classifies reviewer conflicts that may affect blocker state, escalation state, accepted risk, evidence sufficiency, or review completeness.

Generated outputs include:

- conflict categories
- governance severity
- governance impact summary
- governance reviewer requirement
- arbitration requirement
- manual review flags

The analysis is conservative. It does not clear blockers, accept risk, change readiness, or settle disputes automatically.

Phase 38 adds `governance_escalation_events.json` for imported escalation review events. These records preserve the governance conflict reference, severity, escalation reason, and human review requirement without applying an automatic governance outcome.
