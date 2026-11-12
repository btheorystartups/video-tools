# Remediation Tracking System

The remediation tracker records proposed human-review actions without applying them.

Each remediation includes a stable ID, source issue ID, affected videos and segments, action type, suggested action, evidence references, expected effect, dependency list, risk, mutation flag, human-review flag, and status. The default status is `proposed`.

Generated artifacts:

- `remediation/remediation_tracker.json`
- `remediation/recurring_pressure_remediation.json`
- `remediation/readiness_blocker_remediation.json`
- `remediation/archetype_remediation.json`
- `remediation/remediation_summary.json`

Statuses are planning states only: `proposed`, `reviewed_external`, `deferred`, or `rejected`. The bundler does not transition them based on hidden work.

RC hardening and remediation outputs are deterministic review-planning artifacts. They do not apply edits, mutate media, change timelines, perform semantic inference, or make autonomous release decisions.
