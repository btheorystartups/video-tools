"""Profile artifact density for corpus-scale observability."""

from __future__ import annotations

from collections import Counter

from operator_workflow_common import phase39_artifact, stable_row_id


def build_artifact_density_registry(outputs: dict) -> dict:
    artifacts = (outputs.get("artifact_operational_index") or {}).get("artifacts") or []
    counts = Counter(str(row.get("artifact_ref") or "unknown").split("/", 1)[0] for row in artifacts)
    rows = []
    for area, count in sorted(counts.items()):
        rows.append({
            "artifact_density_id": stable_row_id("ADENS", area, count),
            "artifact_area": area,
            "artifact_count": count,
            "dashboard_link_count": sum(len(row.get("linked_dashboards") or []) for row in artifacts if str(row.get("artifact_ref") or "").startswith(area + "/")),
            "schema_link_count": sum(len(row.get("linked_schemas") or []) for row in artifacts if str(row.get("artifact_ref") or "").startswith(area + "/")),
            "density_class": "high" if count >= 10 else "medium" if count >= 5 else "low",
        })
    artifact = phase39_artifact("deterministic_artifact_density_profiler_v1")
    artifact.update({"artifact_density_registry_id": stable_row_id("ADENSREG", [row["artifact_density_id"] for row in rows]), "density_entries": rows, "summary": {"density_area_count": len(rows), "artifact_count": sum(row["artifact_count"] for row in rows)}})
    return artifact
