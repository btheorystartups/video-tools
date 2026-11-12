# Review Merge Lineage System

Review merge lineage records how imported reviewer state relates to existing review operations. Each lineage entry tracks:

- source import batch
- original artifact or review item
- affected review items
- reconciliation pass
- merge outcome
- resulting operational state
- unresolved conflicts

The resulting operational state is recorded as unchanged append-only evidence unless a future human workflow explicitly applies a reviewed operational update. Phase 36 only records import and reconciliation facts.
