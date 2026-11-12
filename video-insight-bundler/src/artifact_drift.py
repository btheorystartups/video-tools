"""Artifact hash drift classification."""

from __future__ import annotations

from stability import STATUS_COMPLETE, utc_now_iso

EXPECTED_PATTERNS = ("reports/", "visualizations/", "graphs/", "analysis_index.", "manifest.json")


def compare_artifact_hashes(previous: dict | None, current: dict) -> dict:
    if not previous:
        return {
            "report_version": "1.0",
            "analysis_status": STATUS_COMPLETE,
            "generated_at_utc": utc_now_iso(),
            "previous_run_id": None,
            "current_run_id": current.get("run_id"),
            "changed_artifact_count": 0,
            "missing_artifact_count": 0,
            "suspicious_drift_count": 0,
            "artifact_drift": [],
            "explanation": "No previous run snapshot exists for this source; artifact drift starts on the next retained run.",
        }
    previous_hashes = (previous or {}).get("artifact_hashes") or {}
    current_hashes = current.get("artifact_hashes") or {}
    changed = []
    for path in sorted(set(previous_hashes) | set(current_hashes)):
        old = previous_hashes.get(path)
        new = current_hashes.get(path)
        if old == new:
            continue
        classification = "expected" if path.startswith(EXPECTED_PATTERNS) else "meaningful"
        if old and not new:
            classification = "suspicious"
        changed.append({"artifact_path": path, "previous_hash": old, "current_hash": new, "classification": classification})
    suspicious = [row for row in changed if row["classification"] == "suspicious"]
    return {
        "report_version": "1.0",
        "analysis_status": STATUS_COMPLETE,
        "generated_at_utc": utc_now_iso(),
        "previous_run_id": (previous or {}).get("run_id"),
        "current_run_id": current.get("run_id"),
        "changed_artifact_count": len(changed),
        "missing_artifact_count": sum(1 for row in changed if row.get("current_hash") is None),
        "suspicious_drift_count": len(suspicious),
        "artifact_drift": changed,
        "explanation": "Report, visualization, graph, manifest, and index changes are expected regeneration drift; missing previously tracked artifacts are suspicious.",
    }
