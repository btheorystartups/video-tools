# Temporal Evidence Index System

The temporal evidence index is the backbone for Phase 33 timeline drilldowns. It normalizes segment-level evidence across videos into time regions with strongest signals, severity, recommendations, blockers, graphs, reports, and suggested review actions.

Phase 34 reuses the same evidence entries to build inline evidence previews, minimaps, temporal heatmaps, persistent context panels, review shortcuts, and workstation crosslinks. The underlying evidence semantics are unchanged.

No source media, timeline, Resolve project, server, database, cloud API, LLM, embedding system, or vector database is used.

The temporal review system provides deterministic editorial-review guidance and timeline-linked evidence navigation. It does not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous creative decisions. Human review is required before production or editorial changes.

## Primary Artifact

- `timeline/temporal_evidence_index.json`

Each entry records video ID, segment ID, timestamp range, evidence types, strongest signals, highest-severity signal, recommendations, blockers, relevant graphs, relevant reports, evidence refs, and a conservative suggested review action.
