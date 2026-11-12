"""Historical throughput comparison."""

from __future__ import annotations

from phase41_longitudinal_common import count_rows, phase41_artifact, render_longitudinal_page, risk_level, stable_row_id


def build_historical_throughput_analysis(outputs: dict) -> dict:
    count = count_rows(outputs, "throughput_analysis_registry", "throughput_entries")
    queue_total = count_rows(outputs, "review_queue_registry", "queue_items")
    value = round(queue_total / max(1, count), 3)
    rows = [{"historical_throughput_id": stable_row_id("HTPUT", count, queue_total), "throughput_type": "queue_items_per_throughput_entry", "throughput_entry_count": count, "queue_count": queue_total, "workload_per_entry": value, "throughput_shift_level": risk_level(min(1.0, value / 50)), "human_review_required": True}]
    artifact = phase41_artifact("deterministic_historical_throughput_analysis_v1")
    artifact.update({"historical_throughput_analysis_id": stable_row_id("HTPUTREG", [row["historical_throughput_id"] for row in rows]), "historical_throughput_entries": rows, "summary": {"historical_throughput_entry_count": len(rows)}})
    return artifact


def render_historical_throughput_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("historical_throughput_analysis") or {}).get("historical_throughput_entries") or []
    return render_longitudinal_page("Historical Throughput Dashboard", "historical_throughput_dashboard.html", rows, ["throughput_type", "queue_count", "workload_per_entry", "throughput_shift_level"], "historical_throughput_id", [("Throughput entries", len(rows))])

