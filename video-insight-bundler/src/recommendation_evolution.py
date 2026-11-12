"""Recommendation evolution tracking across historical runs."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean, pstdev

from stability import STATUS_COMPLETE, STATUS_LIMITED, deterministic_id, utc_now_iso


def _rec_key(row: dict) -> str:
    issue = row.get("issue_type") or "unknown"
    segments = ",".join(sorted(str(item) for item in (row.get("affected_segment_ids") or [])))
    return f"{issue}|{segments}"


def build_recommendation_evolution(snapshots: list[dict], current_recommendations: dict) -> dict:
    current_rows = current_recommendations.get("recommendations") or []
    run_count = len(snapshots)
    # Historical snapshots currently retain counts but not full recommendation bodies.
    # The latest run supplies concrete recommendation identity; older runs provide persistence pressure.
    latest_counts = Counter(row.get("issue_type", "unknown") for row in current_rows)
    by_key = defaultdict(list)
    for row in current_rows:
        by_key[_rec_key(row)].append(row)
    recurring = []
    persistent = []
    contradictions = []
    for key, rows in sorted(by_key.items()):
        confidences = [float(row.get("confidence") or 0.0) for row in rows]
        representative = rows[0]
        item = {
            "recommendation_evolution_id": deterministic_id("rec_evo", key, run_count, confidences, length=16),
            "recommendation_key": key,
            "issue_type": representative.get("issue_type"),
            "affected_segment_ids": representative.get("affected_segment_ids") or [],
            "latest_confidence": round(confidences[-1], 3) if confidences else None,
            "confidence_mean": round(mean(confidences), 3) if confidences else None,
            "confidence_volatility": round(pstdev(confidences), 3) if len(confidences) > 1 else 0.0,
            "latest_severity": representative.get("severity"),
            "observed_in_latest_run": True,
            "stability": "persistent" if run_count >= 3 and latest_counts[representative.get("issue_type", "unknown")] > 1 else "latest_only",
        }
        recurring.append(item)
        if item["stability"] == "persistent":
            persistent.append(item)
        if (representative.get("consensus_backing") or {}).get("conflicting_evidence_warnings"):
            contradictions.append(item)
    resolved = []
    prior_counts = [int(row.get("recommendation_count") or 0) for row in snapshots[:-1]]
    latest_count = int(snapshots[-1].get("recommendation_count") or len(current_rows)) if snapshots else len(current_rows)
    if prior_counts and latest_count < max(prior_counts):
        resolved.append(
            {
                "resolved_recommendation_id": deterministic_id("rec_resolved", prior_counts, latest_count, length=16),
                "evidence": "latest recommendation count is lower than prior retained maximum",
                "prior_max_count": max(prior_counts),
                "latest_count": latest_count,
            }
        )
    return {
        "recommendation_evolution_version": "1.0",
        "analysis_status": STATUS_COMPLETE if run_count >= 3 else STATUS_LIMITED,
        "generated_at_utc": utc_now_iso(),
        "tracked_run_count": run_count,
        "recurring_recommendations": recurring,
        "resolved_recommendations": resolved,
        "persistent_recommendations": persistent,
        "recommendation_confidence_evolution": [
            {"run_id": row.get("run_id"), "recommendation_count": row.get("recommendation_count")}
            for row in snapshots
        ],
        "recommendation_stability": {
            "latest_recommendation_count": latest_count,
            "persistent_count": len(persistent),
            "resolved_count": len(resolved),
            "stability_class": "stable" if not persistent and len(contradictions) == 0 else "watch",
        },
        "recommendation_contradictions": contradictions,
        "limitations": [
            "Historical snapshots retain recommendation counts; full recommendation identity is available for the latest run.",
            "Persistence is conservative until future snapshots retain recommendation fingerprints.",
        ],
    }
