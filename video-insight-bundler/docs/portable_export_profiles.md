# Portable Export Profiles

Portable exports support `minimal`, `review`, `audit`, `full`, `executive`, `presentation`, `investigation`, and `diff_only`.

`review` is the default and is intended for shareable human review. Raw media is excluded by default in every profile unless explicitly requested. Use `full` for broad non-video export and `audit` when provenance, schemas, diffs, snapshots, and validation evidence matter.

Every profile shares cache records and consolidates large byte-identical generated JSON mirrors after dashboard generation. Unique evidence and original provenance are retained. See [portable export packaging](portable_export_package.md#metadata-compaction) for the cache format, consolidation policy, and maintenance command.

## V67 Cache Policy Interaction

Profile, validation tier, and generation mode are now part of cache invalidation. Changing `--export-profile`, `--validation-tier`, or `--generation-mode` can invalidate affected cache entries and is reported in `cache_invalidation_report.json`.
