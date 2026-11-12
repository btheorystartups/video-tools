"""Deterministic fatigue-reduction workflow structures."""

from __future__ import annotations

from operator_workflow_common import ergonomics_links, phase40_artifact, render_registry_page, stable_row_id


def build_fatigue_reduction_registry(outputs: dict) -> dict:
    chunk_count = len((outputs.get("queue_chunking_registry") or {}).get("queue_chunks") or [])
    disclosure_count = len((outputs.get("progressive_disclosure_registry") or {}).get("disclosure_entries") or [])
    duplicate_evidence_count = max(0, str(outputs.get("inline_evidence_preview_index") or {}).lower().count("duplicate"))
    specs = [
        ("chunked_queues", chunk_count, "Review work is divided into deterministic queue chunks."),
        ("progressive_evidence_expansion", disclosure_count, "Evidence details are collapsed until needed."),
        ("compact_evidence_summaries", _count(outputs, "inline_evidence_preview_index", "previews"), "Evidence previews stay compact and link outward."),
        ("collapsible_rationale_sections", _count(outputs, "reviewer_rationale_registry", "rationales"), "Rationale can be scanned before opening full text."),
        ("compact_recommendation_previews", _count(outputs, "recommendation_ranking", "ranked_recommendations"), "Recommendation previews prioritize action and governance status."),
        ("reduced_duplicate_evidence_visibility", duplicate_evidence_count, "Duplicate evidence remains traceable but visually compressed."),
    ]
    rows = []
    for name, count, support in specs:
        rows.append({
            "fatigue_reduction_id": stable_row_id("FRED", name, count),
            "structure": name,
            "source_count": count,
            "fatigue_pressure_reduced": count > 0,
            "operator_support": support,
            "deterministic_no_hidden_adaptation": True,
        })
    artifact = phase40_artifact("deterministic_fatigue_reduction_v1")
    artifact.update({"fatigue_reduction_registry_id": stable_row_id("FREDREG", [row["fatigue_reduction_id"] for row in rows]), "fatigue_reduction_entries": rows, "summary": {"entry_count": len(rows), "active_support_count": sum(1 for row in rows if row["fatigue_pressure_reduced"])}})
    return artifact


def render_fatigue_reduction_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("fatigue_reduction_registry") or {}).get("fatigue_reduction_entries") or []
    return {"fatigue_reduction_dashboard.html": render_registry_page("Fatigue Reduction Dashboard", "Session Ergonomics", "fatigue_reduction_dashboard.html", rows, ["structure", "source_count", "fatigue_pressure_reduced", "operator_support"], "fatigue_reduction_id", [("Structures", len(rows))], ergonomics_links(""))}


def _count(outputs: dict, key: str, field: str) -> int:
    return len((outputs.get(key) or {}).get(field) or [])
