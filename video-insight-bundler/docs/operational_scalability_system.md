# Operational Scalability System

Phase 38 introduces explicit local operational indexes for safer large reruns.

Generated artifacts live under `Corpus_analysis/operations/` and include rebuild, validation, cache, dependency, scoped rerun, selective regeneration, and artifact indexes.

The system records artifact hashes, schemas, dependencies, dashboard links, validation state, and rebuild relevance. It does not maintain hidden mutable runtime state; every reuse or rerun decision is represented as JSON.
