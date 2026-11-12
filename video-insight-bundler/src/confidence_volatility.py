"""Confidence volatility analysis for retained historical runs."""

from __future__ import annotations

from statistics import mean, pstdev

from stability import STATUS_COMPLETE, STATUS_LIMITED, deterministic_id, utc_now_iso
from trend_analysis import TREND_METRICS, _series


def _classify(volatility: float | None, latest_delta: float | None) -> str:
    if volatility is None:
        return "inconclusive"
    if volatility >= 0.18 or (latest_delta is not None and abs(latest_delta) >= 0.24):
        return "unstable"
    if volatility >= 0.1 or (latest_delta is not None and abs(latest_delta) >= 0.14):
        return "watch"
    return "stable"


def build_confidence_volatility(snapshots: list[dict], trend_report: dict | None = None) -> dict:
    regions = []
    for metric, path in TREND_METRICS.items():
        rows = _series(snapshots, path)
        values = [row["value"] for row in rows]
        volatility = round(pstdev(values), 3) if len(values) > 1 else None
        latest_delta = round(values[-1] - values[-2], 3) if len(values) > 1 else None
        klass = _classify(volatility, latest_delta)
        if klass != "stable" or metric in {"readiness", "recommendation_confidence", "continuity"}:
            regions.append(
                {
                    "volatility_region_id": deterministic_id("volatility", metric, values, length=16),
                    "metric": metric,
                    "volatility": volatility,
                    "latest_delta": latest_delta,
                    "classification": klass,
                    "run_values": rows,
                    "volatility_causes": _causes(metric, volatility, latest_delta),
                }
            )
    scores = [row["volatility"] for row in regions if row.get("volatility") is not None]
    volatility_score = round(min(1.0, mean(scores) * 2.5), 3) if scores else 0.0
    unstable = [row for row in regions if row.get("classification") == "unstable"]
    return {
        "confidence_volatility_version": "1.0",
        "analysis_status": STATUS_COMPLETE if len(snapshots) >= 3 else STATUS_LIMITED,
        "generated_at_utc": utc_now_iso(),
        "tracked_run_count": len(snapshots),
        "volatility_score": volatility_score,
        "volatility_regions": sorted(regions, key=lambda row: (-(row.get("volatility") or 0), row.get("metric", ""))),
        "volatility_clusters": [
            {
                "cluster_id": deterministic_id("volatility_cluster", [row["metric"] for row in unstable], length=16),
                "metrics": [row["metric"] for row in unstable],
                "cluster_pressure": round(min(1.0, len(unstable) / 5.0), 3),
            }
        ] if unstable else [],
        "confidence_collapse_regions": [
            row for row in regions if row.get("latest_delta") is not None and row["latest_delta"] <= -0.2
        ],
        "stability_classifications": {row["metric"]: row["classification"] for row in regions},
        "limitations": [
            "Volatility is measured from deterministic metric movement, not from probabilistic model confidence.",
            "Sparse history degrades to limited status.",
        ],
    }


def _causes(metric: str, volatility: float | None, latest_delta: float | None) -> list[str]:
    causes = []
    if volatility is not None and volatility >= 0.1:
        causes.append("historical metric variance exceeded conservative threshold")
    if latest_delta is not None and abs(latest_delta) >= 0.14:
        causes.append("latest run changed materially from prior retained run")
    if metric in {"readiness", "recommendation_confidence"}:
        causes.append("editorial confidence metric affects release-readiness interpretation")
    return causes or ["metric remained within stable historical bounds"]
