"""Synthesize package changes without raw diff dumping."""

from __future__ import annotations

from pathlib import Path

from stability import deterministic_id, utc_now_iso, write_json


def build_change_intelligence(package_root: Path, manifest: dict, diff_report: dict | None, historical: dict | None, *, change_summary: str = "balanced") -> dict:
    changed = []
    for key in ["changed_files", "new_files", "removed_files"]:
        for item in (diff_report or {}).get(key, [])[:25]:
            path = item.get("package_path") if isinstance(item, dict) else str(item)
            changed.append(
                {
                    "change_id": deterministic_id("CHG", key, path),
                    "artifact": path,
                    "change_type": key.replace("_files", ""),
                    "change_priority_score": _score(path, key),
                    "summary": f"{Path(path).name if path else 'Artifact'} is {key.replace('_files', '').replace('_', ' ')} and may affect review continuity.",
                }
            )
    if not changed:
        changed.append({"change_id": deterministic_id("CHG", "no_delta"), "artifact": "package_diff_report.json", "change_type": "no_material_delta", "change_priority_score": 35, "summary": "No material file-level delta was available; reviewers should rely on current synthesis and validation."})
    changed.sort(key=lambda row: row["change_priority_score"], reverse=True)
    limit = 5 if change_summary == "concise" else 12 if change_summary == "balanced" else 25
    report = {
        "analysis_status": "complete",
        "method": "change_intelligence_engine_v77",
        "generated_at_utc": utc_now_iso(),
        "change_summary": change_summary,
        "what_changed_since_last_export": [row["summary"] for row in changed[:limit]],
        "what_matters_most": [row["summary"] for row in changed[:3]],
        "review_focus": "Inspect changed high-priority dashboards, then verify recommendations and governance evidence.",
        "meaningful_changes": changed[:limit],
        "summary": {"meaningful_change_count": len(changed[:limit]), "total_detected_change_count": len(changed)},
    }
    write_json(package_root / "change_intelligence_report.json", report)
    write_json(package_root / "review" / "change_intelligence_report.json", report)
    return report


def _score(path: str | None, key: str) -> int:
    lower = str(path or "").lower()
    score = 45
    if key == "removed_files":
        score += 12
    if any(token in lower for token in ("governance", "recommendation", "validation", "dashboard", "synthesis")):
        score += 25
    if any(token in lower for token in ("diff", "delta", "continuity", "lineage")):
        score += 15
    return min(100, score)
