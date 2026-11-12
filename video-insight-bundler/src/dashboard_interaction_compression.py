"""Deterministic dashboard interaction compression registry."""

from __future__ import annotations

from phase45_interaction_common import focus_specs, phase45_artifact, render_interaction_page, route_rows, stable_row_id


def build_interaction_compression_registry(outputs: dict) -> dict:
    routes = route_rows()
    rows = []
    for index, (focus, _keywords) in enumerate(focus_specs()):
        rows.append(
            {
                "interaction_compression_id": stable_row_id("ICMP", focus, index),
                "compression_scope": focus,
                "source_dashboard_count": len(routes),
                "compressed_step_count": min(4, len(routes)),
                "compression_ratio": round(min(1.0, 4 / max(1, len(routes))), 3),
                "compression_summary": f"{focus} review can start from the lens, priority route, pathway, and repair queue dashboards.",
                "human_review_required": True,
            }
        )
    artifact = phase45_artifact("deterministic_dashboard_interaction_compression_v1")
    artifact.update({"interaction_compression_registry_id": stable_row_id("ICMPREG", [row["interaction_compression_id"] for row in rows]), "interaction_compression_entries": rows, "summary": {"interaction_compression_count": len(rows)}})
    return artifact


def render_interaction_compression_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("interaction_compression_registry") or {}).get("interaction_compression_entries") or []
    return render_interaction_page("Interaction Compression Dashboard", "interaction_compression_dashboard.html", rows, ["compression_scope", "source_dashboard_count", "compressed_step_count", "compression_ratio", "compression_summary"], "interaction_compression_id", [("Compression entries", len(rows))])
