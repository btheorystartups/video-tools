"""Release-candidate threshold gap analysis."""

from __future__ import annotations

from intelligence_common import base_artifact, deterministic_id


def build_rc_threshold_analysis(arbitration: dict, rc_assessment: dict, governance_diagnostics: dict) -> dict:
    thresholds = governance_diagnostics.get("thresholds") or []
    failed_thresholds = [row for row in thresholds if row.get("status") != "pass"]
    near_thresholds = [row for row in thresholds if row.get("near_boundary")]
    failed_checks = [row for row in (rc_assessment.get("checklist") or []) if row.get("status") != "pass"]
    required_improvements = [
        {
            "source_id": row.get("threshold_id"),
            "required_improvement": row.get("suggested_remediation"),
            "gap_to_pass": row.get("gap_to_pass"),
            "evidence_refs": row.get("evidence_refs") or [],
        }
        for row in failed_thresholds
    ]
    minimal_path = [
        {
            "step_id": deterministic_id("RCPATHSTEP", row.get("threshold_id")),
            "threshold_id": row.get("threshold_id"),
            "action": row.get("suggested_remediation"),
            "why_minimal": "Directly addresses a failed conservative threshold.",
            "evidence_refs": row.get("evidence_refs") or [],
        }
        for row in failed_thresholds
    ]
    risky_path = [
        {
            "shortcut": "Reclassify without resolving failed thresholds",
            "risk": "Would weaken governance and conflict with evidence precedence.",
            "not_recommended": True,
        },
        {
            "shortcut": "Treat proposed remediation as completed work",
            "risk": "Would inflate readiness without validation or human review.",
            "not_recommended": True,
        },
    ]
    promotion_confidence = "medium" if not failed_thresholds and failed_checks else ("high" if not failed_thresholds and not failed_checks else "low")
    threshold_analysis = base_artifact(method="deterministic_rc_threshold_analysis_v1")
    threshold_analysis.update(
        {
            "rc_threshold_analysis_id": deterministic_id("RCTA", arbitration.get("classification"), rc_assessment.get("classification"), [(row.get("threshold_id"), row.get("gap_to_pass")) for row in failed_thresholds]),
            "current_classification": arbitration.get("classification"),
            "target_classification": "rc_candidate",
            "failed_checks": failed_checks,
            "near_failed_checks": near_thresholds,
            "required_improvements": required_improvements,
            "minimal_promotion_path": minimal_path,
            "risky_promotion_path": risky_path,
            "not_recommended_shortcuts": [row["shortcut"] for row in risky_path],
            "estimated_review_effort": _estimate_effort(len(failed_thresholds), len(failed_checks), len(near_thresholds)),
            "evidence_refs": sorted(set(ref for row in failed_thresholds + near_thresholds for ref in (row.get("evidence_refs") or []))),
            "summary": {
                "failed_threshold_count": len(failed_thresholds),
                "failed_rc_check_count": len(failed_checks),
                "near_boundary_count": len(near_thresholds),
                "promotion_confidence": promotion_confidence,
            },
        }
    )
    promotion_path = base_artifact(method="deterministic_rc_promotion_path_v1")
    promotion_path.update(
        {
            "rc_promotion_path_id": deterministic_id("RCPATH", threshold_analysis["rc_threshold_analysis_id"], [row.get("step_id") for row in minimal_path]),
            "current_classification": arbitration.get("classification"),
            "target_classification": "rc_candidate",
            "minimal_promotion_path": minimal_path,
            "promotion_blockers": [row.get("threshold_id") for row in failed_thresholds if row.get("blocking_status") == "blocking"],
            "not_recommended_shortcuts": threshold_analysis["not_recommended_shortcuts"],
            "summary": {
                "step_count": len(minimal_path),
                "promotion_confidence": promotion_confidence,
                "standards_lowered": False,
            },
        }
    )
    return {"rc_threshold_analysis": threshold_analysis, "rc_promotion_path": promotion_path}


def _estimate_effort(failed_threshold_count: int, failed_check_count: int, near_count: int) -> str:
    score = failed_threshold_count * 2 + failed_check_count + near_count
    if score <= 1:
        return "low"
    if score <= 5:
        return "medium"
    return "high"

