"""Ambiguity accumulation analysis."""

from __future__ import annotations

from phase41_longitudinal_common import ambiguity_count, phase41_artifact, render_longitudinal_page, risk_level, stable_row_id


def build_ambiguity_accumulation(outputs: dict) -> dict:
    count = ambiguity_count(outputs)
    rows = [{"ambiguity_accumulation_id": stable_row_id("AMBACC", count), "accumulation_type": "unresolved_ambiguity_growth", "current_count": count, "accumulation_level": risk_level(min(1.0, count / 10)), "human_review_required": True}]
    artifact = phase41_artifact("deterministic_ambiguity_accumulation_v1")
    artifact.update({"ambiguity_accumulation_id": stable_row_id("AMBACCREG", [row["ambiguity_accumulation_id"] for row in rows]), "ambiguity_accumulation_entries": rows, "summary": {"ambiguity_accumulation_entry_count": len(rows)}})
    return artifact


def render_ambiguity_accumulation_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("ambiguity_accumulation") or {}).get("ambiguity_accumulation_entries") or []
    return render_longitudinal_page("Ambiguity Accumulation Dashboard", "ambiguity_accumulation_dashboard.html", rows, ["accumulation_type", "current_count", "accumulation_level"], "ambiguity_accumulation_id", [("Ambiguity entries", len(rows))])

