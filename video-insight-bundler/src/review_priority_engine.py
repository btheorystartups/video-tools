"""Rank review actions and high-signal artifacts."""

from __future__ import annotations

from stability import deterministic_id, utc_now_iso
from review_navigation_policy import is_analytical_review_target


def build_review_priority_registry(findings: dict, governance: dict | None, review_style: str = "balanced") -> dict:
    style_bias = {"executive": {"audit": -20, "governance": 10, "recommendation": 12}, "audit_dense": {"audit": 18, "validation": 12}, "balanced": {}}.get(review_style, {})
    actions = []
    for finding in findings.get("findings") or []:
        group = finding.get("concern_group") or "review"
        priority = int(finding.get("review_priority") or 0) + style_bias.get(group, 0)
        actions.append(
            {
                "priority_id": deterministic_id("RPRI", finding.get("finding_id"), review_style),
                "finding_id": finding.get("finding_id"),
                "title": finding.get("title"),
                "priority_score": max(1, min(100, priority)),
                "review_style": review_style,
                "recommended_action": finding.get("what_to_review_next"),
                "supporting_artifacts": finding.get("supporting_artifacts") or [],
                "review_target": next(iter(finding.get("supporting_artifacts") or []), None),
                "review_questions": finding.get("human_review_questions") or [],
            }
        )
    actions.sort(key=lambda row: row["priority_score"], reverse=True)
    return {
        "analysis_status": "complete",
        "method": "review_priority_engine_v73",
        "generated_at_utc": utc_now_iso(),
        "review_style": review_style,
        "priorities": actions,
        "summary": {"priority_count": len(actions), "top_priority_score": actions[0]["priority_score"] if actions else 0},
    }


def build_high_signal_artifact_registry(governance: dict | None, findings: dict) -> dict:
    rows = []
    finding_paths = {path for finding in findings.get("findings") or [] for path in finding.get("supporting_artifacts") or []}
    for row in (((governance or {}).get("dashboard_governance_registry") or {}).get("dashboards") or []):
        if not is_analytical_review_target(row.get("package_path")):
            continue
        score = int(row.get("review_importance_score") or row.get("navigation_priority_score") or 0)
        if score >= 55 or row.get("package_path") in finding_paths:
            rows.append(
                {
                    "artifact_id": deterministic_id("HSART", row.get("package_path")),
                    "package_path": row.get("package_path"),
                    "title": row.get("title"),
                    "category": row.get("category"),
                    "signal_score": score + (15 if row.get("package_path") in finding_paths else 0),
                    "recommended_visibility": "primary" if score >= 80 else "review" if score >= 55 else "supporting",
                    "why_high_signal": "Ranked by governance importance and/or linked to top findings.",
                }
            )
    rows.sort(key=lambda item: item["signal_score"], reverse=True)
    return {
        "analysis_status": "complete",
        "method": "high_signal_artifact_registry_v73",
        "generated_at_utc": utc_now_iso(),
        "artifacts": rows[:50],
        "summary": {"high_signal_artifact_count": min(len(rows), 50)},
    }
