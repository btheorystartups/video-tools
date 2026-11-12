"""Deterministic queue evolution narratives."""

from __future__ import annotations

from collections import Counter

from phase42_narrative_common import base_registry_id, phase42_artifact, queue_rows, render_narrative_page, stable_row_id


def build_queue_evolution_narrative(outputs: dict) -> dict:
    counts = Counter(row["source_registry"] for row in queue_rows(outputs))
    rows = []
    for registry, count in sorted(counts.items()):
        rows.append(
            {
                "queue_evolution_id": stable_row_id("QEV", registry, count),
                "queue_type": registry,
                "current_count": count,
                "narrative": f"Queue source {registry} currently contributes {count} tracked operator review items.",
                "human_review_required": True,
            }
        )
    artifact = phase42_artifact("deterministic_queue_evolution_narrative_v1")
    artifact.update({"queue_evolution_narrative_id": base_registry_id("QEVREG", rows, "queue_evolution_id"), "queue_evolution_entries": rows, "summary": {"queue_evolution_count": len(rows)}})
    return artifact


def render_queue_evolution_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("queue_evolution_narrative") or {}).get("queue_evolution_entries") or []
    return render_narrative_page("Queue Evolution Dashboard", "queue_evolution_dashboard.html", rows, ["queue_type", "current_count", "narrative"], "queue_evolution_id", [("Queue entries", len(rows))])
