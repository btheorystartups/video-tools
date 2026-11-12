"""Rule-based deterministic anomaly clustering for longitudinal artifacts."""

from __future__ import annotations

from stability import STATUS_COMPLETE, STATUS_LIMITED, deterministic_id, utc_now_iso


def build_anomaly_clusters(
    snapshots: list[dict],
    current_consensus: dict,
    current_boundary_diagnostics: dict,
    current_recommendations: dict,
) -> dict:
    clusters = []
    consensus_items = current_consensus.get("consensus_items") or []
    contradiction_items = [
        row for row in consensus_items
        if row.get("consensus_class") == "disagreement" or row.get("conflicting_modalities")
    ]
    weak_continuity = [
        row for row in consensus_items
        if float(row.get("continuity_confidence") or 0.0) < 0.45 or float(row.get("false_positive_probability") or 0.0) >= 0.58
    ]
    unstable_boundaries = [
        row for row in current_boundary_diagnostics.get("boundaries", [])
        if row.get("likely_review_boundary") or int(row.get("contradiction_count") or 0) > 0
    ]
    weak_callbacks = [
        row for row in current_recommendations.get("recommendations", [])
        if row.get("issue_type") in {"unresolved_setup_payoff", "editorial_ambiguity"}
    ]
    hotspots = [
        row for row in current_recommendations.get("recommendations", [])
        if row.get("severity") in {"high", "medium"}
    ]
    for label, rows, basis in [
        ("contradiction_zones", contradiction_items, "consensus disagreement or conflicting modalities"),
        ("weak_continuity_regions", weak_continuity, "low continuity or high false-positive boundary risk"),
        ("unstable_boundaries", unstable_boundaries, "boundary diagnostics flagged human review"),
        ("weak_callbacks", weak_callbacks, "callback or ambiguity recommendations remain active"),
        ("recommendation_hotspots", hotspots, "medium/high severity recommendations"),
    ]:
        clusters.append(_cluster(label, rows, basis, snapshots))
    recurring_drift = [
        row for row in snapshots
        if (row.get("key_metrics") or {}).get("topic_drift_score") is not None
        and float((row.get("key_metrics") or {}).get("topic_drift_score") or 0.0) >= 0.6
    ]
    clusters.append(_cluster("recurring_drift_regions", recurring_drift, "historical topic drift score exceeded threshold", snapshots))
    return {
        "anomaly_clusters_version": "1.0",
        "analysis_status": STATUS_COMPLETE if len(snapshots) >= 3 else STATUS_LIMITED,
        "generated_at_utc": utc_now_iso(),
        "tracked_run_count": len(snapshots),
        "anomaly_clusters": clusters,
        "cluster_summary": {
            "cluster_count": len(clusters),
            "active_cluster_count": sum(1 for row in clusters if row["item_count"] > 0),
            "highest_pressure_cluster": max(clusters, key=lambda row: (row["cluster_pressure"], row["cluster_type"])) if clusters else None,
        },
        "limitations": [
            "Clustering is rule-based and explainable; no ML clustering, embeddings, or semantic inference is used.",
            "Clusters prioritize human review rather than autonomous editing.",
        ],
    }


def _cluster(label: str, rows: list[dict], basis: str, snapshots: list[dict]) -> dict:
    ids = []
    for row in rows[:20]:
        ids.append(row.get("transition_id") or row.get("boundary_id") or row.get("issue_type") or row.get("run_id") or "item")
    return {
        "cluster_id": deterministic_id("anom", label, ids, len(snapshots), length=16),
        "cluster_type": label,
        "item_count": len(rows),
        "representative_ids": ids[:12],
        "cluster_pressure": round(min(1.0, len(rows) / 8.0), 3),
        "rule_basis": basis,
        "review_priority": "high" if len(rows) >= 5 else "medium" if rows else "low",
    }
