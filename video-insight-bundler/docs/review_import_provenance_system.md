# Review Import Provenance System

Review import provenance preserves where imported reviewer content came from and how it entered reconciliation.

Tracked fields include:

- import source
- deterministic import timestamp
- template version
- import batch
- reviewer identifier placeholder
- canonical imported artifact hash
- reconciliation pass ID
- affected artifacts

The provenance system is designed for local filesystem artifacts. It does not require servers, runtime databases, cloud APIs, LLM calls, embeddings, or collaborative editing state.
