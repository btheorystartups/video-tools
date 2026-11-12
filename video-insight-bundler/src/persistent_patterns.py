"""Persistent editorial pattern detection across retained historical runs."""

from __future__ import annotations

from statistics import mean

from stability import STATUS_COMPLETE, STATUS_LIMITED, deterministic_id, utc_now_iso


def build_persistent_patterns(snapshots: list[dict], anomaly_report: dict, recommendation_report: dict) -> dict:
    metrics = [row.get("key_metrics") or {} for row in snapshots]
    patterns = []
    checks = [
        ("chronic_weak_boundaries", "false_positive_boundary_ratio", 0.35, "high"),
        ("chronic_rhetorical_gaps", "rhetorical_balance_score", 0.45, "low"),
        ("chronic_continuity_failures", "ambiguity_adjusted_continuity", 0.5, "low"),
        ("chronic_unresolved_claims", "argument_completeness_score", 0.5, "low"),
        ("chronic_contradiction_regions", "mean_consensus_score", 0.48, "low"),
        ("recurring_discourse_patterns", "callback_resolution_quality", 0.5, "low"),
    ]
    for pattern_type, metric, threshold, mode in checks:
        values = [float(row.get(metric)) for row in metrics if row.get(metric) is not None]
        if not values:
            active = False
        elif mode == "high":
            active = sum(1 for value in values if value >= threshold) >= max(2, len(values) // 2)
        else:
            active = sum(1 for value in values if value <= threshold) >= max(2, len(values) // 2)
        patterns.append(
            {
                "pattern_id": deterministic_id("pattern", pattern_type, values, threshold, length=16),
                "pattern_type": pattern_type,
                "metric": metric,
                "observed_values": [round(value, 3) for value in values],
                "mean_value": round(mean(values), 3) if values else None,
                "threshold": threshold,
                "is_persistent": active,
                "pressure": round(min(1.0, (sum(1 for value in values if (value >= threshold if mode == "high" else value <= threshold)) / max(len(values), 1))), 3) if values else 0.0,
            }
        )
    active_patterns = [row for row in patterns if row["is_persistent"]]
    return {
        "persistent_patterns_version": "1.0",
        "analysis_status": STATUS_COMPLETE if len(snapshots) >= 3 else STATUS_LIMITED,
        "generated_at_utc": utc_now_iso(),
        "tracked_run_count": len(snapshots),
        "patterns": patterns,
        "chronic_weak_boundaries": [row for row in patterns if row["pattern_type"] == "chronic_weak_boundaries" and row["is_persistent"]],
        "chronic_rhetorical_gaps": [row for row in patterns if row["pattern_type"] == "chronic_rhetorical_gaps" and row["is_persistent"]],
        "chronic_continuity_failures": [row for row in patterns if row["pattern_type"] == "chronic_continuity_failures" and row["is_persistent"]],
        "chronic_unresolved_claims": [row for row in patterns if row["pattern_type"] == "chronic_unresolved_claims" and row["is_persistent"]],
        "chronic_contradiction_regions": [row for row in patterns if row["pattern_type"] == "chronic_contradiction_regions" and row["is_persistent"]],
        "recurring_discourse_patterns": [row for row in patterns if row["pattern_type"] == "recurring_discourse_patterns" and row["is_persistent"]],
        "persistent_pattern_summary": {
            "persistent_pattern_count": len(active_patterns),
            "persistent_pattern_pressure": round(min(1.0, len(active_patterns) / 6.0), 3),
            "recommendation_stability": (recommendation_report.get("recommendation_stability") or {}).get("stability_class"),
            "active_anomaly_cluster_count": (anomaly_report.get("cluster_summary") or {}).get("active_cluster_count"),
        },
        "limitations": [
            "Persistence requires repeated deterministic evidence in retained local history.",
            "Pattern labels identify review pressure, not semantic truth or editorial intent.",
        ],
    }
