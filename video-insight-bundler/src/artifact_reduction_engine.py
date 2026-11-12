"""Artifact reduction planning without deleting audit evidence."""

from __future__ import annotations

from pathlib import Path

from stability import deterministic_id, utc_now_iso, write_json


def build_artifact_reduction_report(package_root: Path, governance: dict | None, *, mode: str = "balanced") -> dict:
    rows = (((governance or {}).get("dashboard_governance_registry") or {}).get("dashboards") or [])
    pages = [row for row in rows if str(row.get("package_path") or "").endswith((".html", ".htm"))]
    threshold = {"conservative": 35, "balanced": 50, "aggressive": 65}.get(mode, 50)
    suppressed = []
    grouped = []
    audit_preserved = []
    for row in pages:
        score = int(row.get("review_importance_score") or 0)
        category = row.get("category") or "internal"
        if category == "audit" or row.get("required_for_audit"):
            audit_preserved.append(row.get("package_path"))
        elif score < threshold and row.get("visibility") in {"hidden", "advanced"}:
            suppressed.append(row.get("package_path"))
        elif category in {"recommendation", "evidence", "continuity", "delta", "governance"}:
            grouped.append({"group_id": deterministic_id("DGRP", category), "category": category, "page": row.get("package_path")})
    pages_before = len(pages)
    pages_after = max(1, pages_before - len(suppressed) - max(0, len(grouped) - len({row["category"] for row in grouped})))
    ratio = round((pages_before - pages_after) / pages_before, 3) if pages_before else 0
    report = {
        "analysis_status": "complete",
        "method": "artifact_reduction_engine_v75",
        "generated_at_utc": utc_now_iso(),
        "artifact_reduction_mode": mode,
        "pages_before": pages_before,
        "pages_after": pages_after,
        "grouped_pages": grouped,
        "suppressed_pages": suppressed,
        "aggregated_pages": sorted({row["category"] for row in grouped}),
        "audit_preserved_pages": audit_preserved,
        "navigation_reduction_ratio": ratio,
        "estimated_cognitive_reduction": round(min(0.6, ratio * 0.85 + len(suppressed) * 0.01), 3),
        "summary": {
            "pages_before": pages_before,
            "pages_after": pages_after,
            "suppressed_page_count": len(suppressed),
            "grouped_page_count": len(grouped),
            "navigation_reduction_ratio": ratio,
            "estimated_cognitive_reduction": round(min(0.6, ratio * 0.85 + len(suppressed) * 0.01), 3),
        },
    }
    write_json(package_root / "artifact_reduction_report.json", report)
    write_json(package_root / "review" / "artifact_reduction_report.json", report)
    return report
