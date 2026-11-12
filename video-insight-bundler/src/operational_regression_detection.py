"""Deterministic informational operational regression detection."""

from __future__ import annotations

from phase41_longitudinal_common import latest_lineage_entries, phase41_artifact, render_longitudinal_page, risk_level, stable_row_id


def build_operational_regression_registry(outputs: dict) -> dict:
    entries = latest_lineage_entries(outputs)
    latest = entries[-1] if entries else {}
    previous = entries[-2] if len(entries) > 1 else {}
    specs = [
        ("validation_slowdown", "validation_timing_seconds"),
        ("dashboard_density_overload", "dashboard_generation_seconds"),
        ("rebuild_cost_spike", "rebuild_timing_seconds"),
        ("queue_explosion", "queue_total_count"),
        ("artifact_growth_spike", "artifact_total_count"),
    ]
    rows = []
    for regression_type, metric in specs:
        current = float(latest.get(metric) or 0)
        prior = float(previous.get(metric) or 0)
        delta = round(current - prior, 3)
        ratio = round(current / prior, 3) if prior else (1.0 if current else 0.0)
        detected = ratio >= 1.25 and delta > 0
        rows.append({"operational_regression_id": stable_row_id("OREG", regression_type, current, prior), "regression_type": regression_type, "metric": metric, "current_value": current, "previous_value": prior, "delta": delta, "growth_ratio": ratio, "regression_detected": detected, "regression_level": risk_level(min(1.0, max(0.0, ratio - 1.0))), "informational_only": True, "human_review_required": True})
    artifact = phase41_artifact("deterministic_operational_regression_detection_v1")
    artifact.update({"operational_regression_registry_id": stable_row_id("OREGREG", [row["operational_regression_id"] for row in rows]), "regression_entries": rows, "summary": {"regression_entry_count": len(rows), "detected_regression_count": sum(1 for row in rows if row["regression_detected"])}})
    return artifact


def render_operational_regression_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("operational_regression_registry") or {}).get("regression_entries") or []
    return render_longitudinal_page("Operational Regression Dashboard", "operational_regression_dashboard.html", rows, ["regression_type", "current_value", "previous_value", "delta", "regression_detected"], "operational_regression_id", [("Regression entries", len(rows))])

