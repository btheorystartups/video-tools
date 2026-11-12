# Incremental Cache Optimization

V67 adds explicit artifact identity and invalidation evidence for portable exports.

Generated files: `incremental_cache_optimization_report.json`, `cache_invalidation_report.json`, `artifact_identity_registry.json`, and `dependency_hash_registry.json`.

Miss reasons include `content_changed`, `metadata_changed`, `dependency_changed`, `reference_changed`, `profile_policy_changed`, `validation_tier_changed`, `generation_mode_changed`, `source_missing`, `cache_missing`, `forced_refresh`, and `unsafe_to_reuse`.

The cache uses normalized package/source paths and semantic JSON hashing that ignores volatile exporter timestamps. Generated reports that genuinely change summaries, topology, manifests, or registry content still invalidate.
