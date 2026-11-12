"""Schema version drift detection."""

from __future__ import annotations

from stability import STATUS_COMPLETE, utc_now_iso


def _rank(version: str | None) -> tuple:
    if not version:
        return ()
    parts = []
    for item in str(version).replace("-", ".").split("."):
        try:
            parts.append(int(item))
        except ValueError:
            parts.append(item)
    return tuple(parts)


def compare_schema_versions(previous: dict | None, current: dict) -> dict:
    if not previous:
        return {
            "report_version": "1.0",
            "analysis_status": STATUS_COMPLETE,
            "generated_at_utc": utc_now_iso(),
            "previous_run_id": None,
            "current_run_id": current.get("run_id"),
            "schema_version_diffs": [],
            "schema_downgrade_count": 0,
        }
    old_versions = (previous or {}).get("schema_versions") or {}
    new_versions = current.get("schema_versions") or {}
    diffs = []
    for artifact in sorted(set(old_versions) | set(new_versions)):
        old = old_versions.get(artifact)
        new = new_versions.get(artifact)
        if old == new:
            continue
        classification = "schema_upgrade"
        if old and new and _rank(new) < _rank(old):
            classification = "suspicious_schema_downgrade"
        elif old and not new:
            classification = "schema_version_removed"
        elif not old and new:
            classification = "schema_version_added"
        diffs.append({"artifact": artifact, "previous_version": old, "current_version": new, "classification": classification})
    return {
        "report_version": "1.0",
        "analysis_status": STATUS_COMPLETE,
        "generated_at_utc": utc_now_iso(),
        "previous_run_id": (previous or {}).get("run_id"),
        "current_run_id": current.get("run_id"),
        "schema_version_diffs": diffs,
        "schema_downgrade_count": sum(1 for row in diffs if row["classification"] == "suspicious_schema_downgrade"),
    }
