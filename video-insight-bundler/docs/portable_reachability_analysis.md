# Portable Reachability Analysis

Exports generate `portable_reachability_report.json`, `portable_export_audit_report.json`, and `portable_export_audit_report.md`.

These reports explain which files are linked from `index.html` and dashboards, which files are intentionally audit-only, and which files are suspiciously unreachable.

## V69 Topology Simplification

Topology simplification builds on reachability by classifying cycles and orphans, isolating stale/internal orphan nodes from main navigation, and emitting `navigation_tree_report.json`, `cycle_reduction_report.json`, and `orphan_reduction_report.json`.
