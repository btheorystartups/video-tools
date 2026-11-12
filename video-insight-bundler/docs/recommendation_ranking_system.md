# Recommendation Ranking System

Phase 32 adds `dashboard/recommendation_ranking.json` and `visualizations/recommendation_priority_dashboard.html`.

Recommendation ranking considers expected impact, effort estimate, remediation complexity, governance severity, recurrence, corpus influence, stabilization influence where available, confidence, and uncertainty. Each ranked item includes priority score, effort estimate, likely benefit, evidence confidence, overcorrection risk, preserve-as-intentional option, evidence refs, and non-mutation status.

Ranking prioritizes human review. It does not apply edits or make autonomous creative decisions.

The expert dashboard system provides deterministic editorial-review guidance and optimization interpretation. It does not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict audience behavior, or make autonomous creative decisions. Human review is required before production or editorial changes.
## Traceability And Lineage

Ranked recommendations now feed `recommendations/recommendation_traceability.json` and `recommendations/recommendation_lineage.json`, linking each recommendation to source segments, metric signals, evidence refs, and lowest-risk optimization paths.
