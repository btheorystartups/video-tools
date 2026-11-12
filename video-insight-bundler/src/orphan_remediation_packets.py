"""Deterministic orphan remediation review packets."""

from __future__ import annotations

from phase45_interaction_common import all_interaction_events, orphan_ids, phase45_artifact, render_interaction_page, stable_row_id


def build_orphan_remediation_registry(outputs: dict) -> dict:
    candidates = [row.get("source_event_id") for row in all_interaction_events(outputs, 24) if row.get("source_event_id")]
    rows = []
    for index, orphan_id in enumerate(orphan_ids(outputs)[:48]):
        rows.append(
            {
                "orphan_remediation_packet_id": stable_row_id("ORPKT", orphan_id, index),
                "orphan_id": orphan_id,
                "orphan_explanation": "Continuity reference lacks a complete linked route in the current static graph.",
                "missing_continuity_context": "No autonomous repair is applied; reviewer must confirm linkage context.",
                "possible_linkage_candidates": candidates[:5],
                "unresolved_route_summary": "Review required before any continuity lineage can be extended.",
                "remediation_review_suggestion": "Inspect candidate links and record a human-reviewed continuity decision.",
                "human_review_required": True,
            }
        )
    artifact = phase45_artifact("deterministic_orphan_remediation_packets_v1")
    artifact.update({"orphan_remediation_registry_id": stable_row_id("ORPKTREG", [row["orphan_remediation_packet_id"] for row in rows]), "orphan_remediation_packets": rows, "summary": {"orphan_remediation_packet_count": len(rows)}})
    return artifact


def render_orphan_remediation_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("orphan_remediation_registry") or {}).get("orphan_remediation_packets") or []
    return render_interaction_page("Orphan Remediation Dashboard", "orphan_remediation_dashboard.html", rows, ["orphan_id", "orphan_explanation", "possible_linkage_candidates", "remediation_review_suggestion"], "orphan_remediation_packet_id", [("Orphan packets", len(rows))])
