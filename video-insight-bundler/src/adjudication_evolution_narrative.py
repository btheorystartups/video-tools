"""Deterministic adjudication evolution narratives."""

from __future__ import annotations

from collections import Counter

from phase42_narrative_common import adjudication_rows, base_registry_id, phase42_artifact, render_narrative_page, stable_row_id


def build_adjudication_evolution_narrative(outputs: dict) -> dict:
    counts = Counter(row["source_registry"] for row in adjudication_rows(outputs))
    rows = []
    for registry, count in sorted(counts.items()):
        rows.append(
            {
                "adjudication_evolution_id": stable_row_id("AEV", registry, count),
                "evolution_type": registry,
                "current_count": count,
                "narrative": f"Adjudication source {registry} contributes {count} tracked entries to the current longitudinal state.",
                "human_review_required": True,
            }
        )
    artifact = phase42_artifact("deterministic_adjudication_evolution_narrative_v1")
    artifact.update({"adjudication_evolution_narrative_id": base_registry_id("AEVREG", rows, "adjudication_evolution_id"), "adjudication_evolution_entries": rows, "summary": {"adjudication_evolution_count": len(rows)}})
    return artifact


def render_adjudication_evolution_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("adjudication_evolution_narrative") or {}).get("adjudication_evolution_entries") or []
    return render_narrative_page("Adjudication Evolution Dashboard", "adjudication_evolution_dashboard.html", rows, ["evolution_type", "current_count", "narrative"], "adjudication_evolution_id", [("Adjudication entries", len(rows))])
