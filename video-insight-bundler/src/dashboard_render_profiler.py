"""Profile static dashboard render density."""

from __future__ import annotations

from operator_workflow_common import deterministic_cost, phase39_artifact, stable_row_id


def build_dashboard_render_registry(outputs: dict) -> dict:
    artifacts = (outputs.get("artifact_operational_index") or {}).get("artifacts") or []
    dashboard_refs = sorted({ref for row in artifacts for ref in (row.get("linked_dashboards") or [])})
    rows = []
    for ref in dashboard_refs:
        source_count = sum(1 for row in artifacts if ref in (row.get("linked_dashboards") or []))
        rows.append({
            "dashboard_render_id": stable_row_id("DRENDER", ref, source_count),
            "dashboard_ref": ref,
            "source_artifact_count": source_count,
            "estimated_render_seconds": deterministic_cost(source_count, len(ref), base=0.01, scale=0.002),
            "density_class": "high" if source_count >= 5 else "medium" if source_count >= 2 else "low",
            "static_html_only": True,
        })
    artifact = phase39_artifact("deterministic_dashboard_render_profiler_v1")
    artifact.update({"dashboard_render_registry_id": stable_row_id("DRENDERREG", [row["dashboard_render_id"] for row in rows]), "render_entries": rows, "summary": {"dashboard_count": len(rows), "estimated_total_render_seconds": round(sum(row["estimated_render_seconds"] for row in rows), 3)}})
    return artifact
