# Artifact Integrity System

Phase 14 adds a deterministic global integrity layer for generated analysis bundles. It validates artifact presence, local references, graph edges, revision lineage, dashboard coverage, schema-version inventory, and non-destructive migration metadata.

## Longitudinal Extension

The integrity suite now treats `longitudinal/` and `verification_evidence/longitudinal_validation.json` as generated platform artifacts. Longitudinal validation checks schema conformance plus run-reference consistency across retained snapshots, trend rows, anomaly references, and persistent-pattern references.

These checks preserve the local-first contract: they never call cloud services, embeddings, vector databases, LLMs, Resolve, or media/timeline mutation APIs.

Longitudinal and semantic-evolution outputs are deterministic historical-analysis heuristics intended for editorial review and system explainability. They are not semantic truth systems, predictive systems, or autonomous editorial agents.

## Outputs

- `integrity/artifact_integrity.json`
- `integrity/graph_consistency.json`
- `integrity/reference_validation.json`
- `integrity/lineage_validation.json`
- `integrity/dashboard_coverage.json`
- `integrity/artifact_dependency_graph.json`
- `integrity/migration_registry.json`
- `verification_evidence/integrity_validation.json`
- `verification_evidence/graph_validation.json`
- `verification_evidence/migration_validation.json`

## Rules

- `scene_segments.json` is the authority for segment IDs.
- `revision_graph/revision_graph.json` is the authority for revision and candidate lineage.
- `discourse/argument_graph.json` is the authority for argument-node IDs.
- Static dashboard links must resolve locally and use relative paths.
- Migration metadata is additive scaffolding only; destructive migrations are unsupported.

## Readiness Impact

Release readiness now records artifact integrity, graph consistency, reference integrity, lineage consistency, and dashboard coverage scores. Readiness is downgraded when unresolved references, lineage issues, or severe consistency failures are present.

## Limitations

Integrity validation is structural and deterministic. It detects missing files, malformed references, and graph/lineage inconsistencies, but it does not infer semantic correctness or editorial truth.
