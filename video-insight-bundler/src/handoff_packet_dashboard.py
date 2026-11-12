"""Deterministic handoff packet dashboard registry."""

from __future__ import annotations

from phase43_recall_common import phase43_artifact, render_recall_page, stable_row_id


def build_handoff_packet_registry(outputs: dict) -> dict:
    entries = (outputs.get("operator_handoff_registry") or {}).get("handoff_entries") or []
    packets = []
    for entry in entries:
        packets.append(
            {
                "handoff_packet_id": stable_row_id("HPKT", entry.get("operator_handoff_entry_id"), entry.get("source_event_ids")),
                "handoff_entry_id": entry.get("operator_handoff_entry_id"),
                "packet_type": entry.get("handoff_type"),
                "source_event_ids": entry.get("source_event_ids") or [],
                "dashboard_ref": "visualizations/recall/operator_handoff_dashboard.html",
                "human_review_required": True,
            }
        )
    artifact = phase43_artifact("deterministic_handoff_packet_dashboard_v1")
    artifact.update({"handoff_packet_registry_id": stable_row_id("HPKTREG", [row["handoff_packet_id"] for row in packets]), "handoff_packets": packets, "summary": {"handoff_packet_count": len(packets)}})
    return artifact


def render_handoff_packet_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("handoff_packet_registry") or {}).get("handoff_packets") or []
    return render_recall_page("Handoff Packet Dashboard", "handoff_packet_dashboard.html", rows, ["packet_type", "handoff_entry_id", "dashboard_ref"], "handoff_packet_id", [("Handoff packets", len(rows))])
