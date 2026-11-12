# Longitudinal Intelligence System

The longitudinal system turns retained local run snapshots into deterministic multi-run editorial intelligence. It operates after pairwise run comparison and run-history writing, then writes `longitudinal/` JSON artifacts, Markdown reports, PNG graphs, static HTML pages, and `verification_evidence/longitudinal_validation.json`.

Longitudinal and semantic-evolution outputs are deterministic historical-analysis heuristics intended for editorial review and system explainability. They are not semantic truth systems, predictive systems, or autonomous editorial agents.

## Architecture

- `longitudinal_analysis.py`: orchestrates outputs, validation, graph/report/page writing, readiness backfeed, and consensus backfeed.
- `trend_analysis.py`: classifies retained metric series as improving, stable, degrading, volatile, or inconclusive.
- `confidence_volatility.py`: identifies unstable metrics, confidence-collapse regions, volatility clusters, and stability classifications.
- `recommendation_evolution.py`: tracks latest recommendation identity plus retained historical recommendation counts.
- `anomaly_clustering.py`: uses rule-based deterministic clusters for contradiction zones, weak continuity, unstable boundaries, weak callbacks, drift regions, and recommendation hotspots.
- `persistent_patterns.py`: detects chronic weak boundaries, rhetorical gaps, continuity failures, unresolved claims, contradiction regions, and recurring discourse patterns.
- `semantic_evolution.py`: defines future semantic continuity interfaces without embeddings, vector stores, cloud APIs, LLM calls, or semantic inference.

## Evidence Precedence

Source media hashes, profile hashes, schema validation, artifact integrity, graph consistency, lineage validation, deterministic IDs, and explicit artifact references retain highest authority. Longitudinal signals can lower confidence or add review pressure, but they do not mutate source media, segments, timelines, recommendations, or revision graph state.

Stable repeated runs improve confidence only conservatively. Volatility, recurring issues, persistent contradiction pressure, chronic weak boundaries, and anomaly clustering pressure can hold readiness down.

## Outputs

- `longitudinal/longitudinal_analysis.json`
- `longitudinal/trend_analysis.json`
- `longitudinal/confidence_volatility.json`
- `longitudinal/recommendation_evolution.json`
- `longitudinal/anomaly_clusters.json`
- `longitudinal/persistent_patterns.json`
- `longitudinal/semantic_evolution.json`
- `longitudinal/longitudinal_summary.json`

Static reports, graphs, and visualizations mirror those JSON artifacts with relative links and graceful degradation.

## Limitations

The system uses retained local snapshots and current generated artifacts. Sparse history reports `limited` status. Recommendation identity is strongest for the latest run until future snapshots retain recommendation fingerprints. Anomaly clustering is rule-based and explainable, not ML clustering. Semantic evolution is scaffolding only.

Phase 19-22A comparative intelligence consumes current and historical local analysis folders to add creator-level stability, comparative volatility, recurring structural debt, recommendation convergence, and style-fingerprint signals. These signals are conservative readiness inputs and review evidence only.
