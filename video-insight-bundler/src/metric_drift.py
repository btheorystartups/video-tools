"""Metric and readiness drift comparison."""

from __future__ import annotations

from stability import STATUS_COMPLETE, utc_now_iso

METRICS = [
    "release_readiness_score",
    "topic_drift_score",
    "mean_consensus_score",
    "visual_continuity_score",
    "artifact_integrity_score",
    "graph_consistency_score",
    "reference_integrity_score",
    "lineage_consistency_score",
]


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compare_metrics(previous: dict | None, current: dict) -> dict:
    if not previous:
        return {
            "report_version": "1.0",
            "analysis_status": STATUS_COMPLETE,
            "generated_at_utc": utc_now_iso(),
            "previous_run_id": None,
            "current_run_id": current.get("run_id"),
            "metric_drift": [],
            "meaningful_metric_drift_count": 0,
        }
    previous_metrics = (previous or {}).get("key_metrics") or {}
    current_metrics = current.get("key_metrics") or {}
    rows = []
    for key in METRICS:
        old = _num(previous_metrics.get(key))
        new = _num(current_metrics.get(key))
        if old is None and new is None:
            continue
        delta = None if old is None or new is None else round(new - old, 4)
        classification = "no_drift" if delta == 0 else "meaningful"
        if delta is None:
            classification = "limited"
        elif abs(delta) < 0.015:
            classification = "minor"
        rows.append({"metric": key, "previous": old, "current": new, "delta": delta, "classification": classification})
    return {
        "report_version": "1.0",
        "analysis_status": STATUS_COMPLETE,
        "generated_at_utc": utc_now_iso(),
        "previous_run_id": (previous or {}).get("run_id"),
        "current_run_id": current.get("run_id"),
        "metric_drift": rows,
        "meaningful_metric_drift_count": sum(1 for row in rows if row["classification"] == "meaningful"),
    }


def compare_readiness(previous: dict | None, current: dict) -> dict:
    if not previous:
        return {
            "report_version": "1.0",
            "analysis_status": STATUS_COMPLETE,
            "generated_at_utc": utc_now_iso(),
            "previous_run_id": None,
            "current_run_id": current.get("run_id"),
            "previous_readiness": {},
            "current_readiness": current.get("readiness") or {},
            "score_delta": None,
            "class_changed": False,
            "classification": "no_previous_run",
        }
    old = (previous or {}).get("readiness") or {}
    new = current.get("readiness") or {}
    old_score = _num(old.get("score"))
    new_score = _num(new.get("score"))
    delta = None if old_score is None or new_score is None else round(new_score - old_score, 4)
    class_changed = old.get("class") != new.get("class")
    return {
        "report_version": "1.0",
        "analysis_status": STATUS_COMPLETE,
        "generated_at_utc": utc_now_iso(),
        "previous_run_id": (previous or {}).get("run_id"),
        "current_run_id": current.get("run_id"),
        "previous_readiness": old,
        "current_readiness": new,
        "score_delta": delta,
        "class_changed": class_changed,
        "classification": "meaningful" if class_changed or (delta is not None and abs(delta) >= 0.015) else "no_drift",
    }
