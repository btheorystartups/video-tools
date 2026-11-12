"""Executive synthesis layer for portable review exports."""

from __future__ import annotations

from pathlib import Path

from critical_signal_detection import detect_critical_signals
from finding_aggregation import aggregate_findings
from review_priority_engine import build_high_signal_artifact_registry, build_review_priority_registry
from stability import utc_now_iso, write_json


def build_executive_synthesis(
    package_root: Path,
    manifest: dict,
    validation: dict,
    governance: dict | None,
    *,
    review_style: str = "balanced",
    change_intelligence: dict | None = None,
    reduction: dict | None = None,
) -> dict:
    findings = aggregate_findings(package_root, manifest, validation, governance, change_intelligence)
    priorities = build_review_priority_registry(findings, governance, review_style=review_style)
    high_signal = build_high_signal_artifact_registry(governance, findings)
    signals = detect_critical_signals(validation, governance, findings, reduction)
    top = findings.get("findings", [])[:5]
    report = {
        "analysis_status": "complete",
        "method": "executive_synthesis_engine_v73",
        "generated_at_utc": utc_now_iso(),
        "classification": "operational beta+ / internal beta_plus",
        "rc_promotion_recommended": False,
        "review_style": review_style,
        "concise_summary": _summary(top, validation),
        "top_findings": top,
        "highest_priority_review_actions": priorities.get("priorities", [])[:8],
        "strongest_governance_concerns": [row for row in top if row.get("concern_group") == "governance"][:3],
        "strongest_continuity_breaks": [row for row in top if row.get("concern_group") in {"continuity", "delta"}][:3],
        "strongest_deltas_since_prior_export": (change_intelligence or {}).get("meaningful_changes", [])[:5],
        "strongest_evidence_clusters": high_signal.get("artifacts", [])[:8],
        "critical_signals": signals.get("critical_signals", []),
        "recommended_review_order": [row.get("recommended_action") for row in priorities.get("priorities", [])[:8]],
        "limitations": [
            "Synthesis is deterministic and based on generated artifacts already present in the export.",
            "Human reviewers remain responsible for final interpretation and sign-off.",
        ],
        "summary": {
            "top_finding_count": len(top),
            "critical_signal_count": signals.get("summary", {}).get("critical_signal_count", 0),
            "high_signal_artifact_count": high_signal.get("summary", {}).get("high_signal_artifact_count", 0),
        },
    }
    for rel, payload in [
        ("executive_synthesis_report.json", report),
        ("critical_findings_registry.json", findings),
        ("review_priority_registry.json", priorities),
        ("high_signal_artifact_registry.json", high_signal),
    ]:
        write_json(package_root / rel, payload)
        write_json(package_root / "review" / rel, payload)
    return {
        "executive_synthesis_report": report,
        "critical_findings_registry": findings,
        "review_priority_registry": priorities,
        "high_signal_artifact_registry": high_signal,
        "critical_signal_registry": signals,
    }


def _summary(top: list[dict], validation: dict) -> str:
    if validation.get("broken_link_count") or validation.get("missing_asset_count"):
        return "Review should start with package integrity because validation detected navigation or asset issues."
    if top:
        return f"Review should start with {top[0]['title']} and then follow the ranked priority actions."
    return "No critical synthesis blockers were detected; proceed through the recommended review pathway."
