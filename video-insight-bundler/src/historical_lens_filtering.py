"""Deterministic historical lens filtering."""

from __future__ import annotations

from phase43_recall_common import RECALL_LENSES, events_for_focus, phase43_artifact, render_recall_page, source_ids, stable_row_id


def build_historical_lens_registry(outputs: dict) -> dict:
    lenses = []
    for lens_name, keywords in RECALL_LENSES:
        events = events_for_focus(outputs, lens_name, 10)
        lenses.append(
            {
                "historical_lens_id": stable_row_id("HLENS", lens_name, source_ids(events)),
                "lens_name": lens_name,
                "filter_keywords": keywords,
                "matched_event_ids": source_ids(events),
                "matched_event_count": len(events),
                "deterministic_filter_basis": "source_type_and_summary_keyword_match",
                "human_review_required": True,
            }
        )
    artifact = phase43_artifact("deterministic_historical_lens_filtering_v1")
    artifact.update({"historical_lens_registry_id": stable_row_id("HLENSREG", [row["historical_lens_id"] for row in lenses]), "historical_lenses": lenses, "summary": {"historical_lens_count": len(lenses)}})
    return artifact


def render_historical_lens_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("historical_lens_registry") or {}).get("historical_lenses") or []
    return render_recall_page("Historical Lens Dashboard", "historical_lens_dashboard.html", rows, ["lens_name", "matched_event_count", "deterministic_filter_basis"], "historical_lens_id", [("Lenses", len(rows))])
