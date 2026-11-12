"""Deterministic drilldown continuity chains."""

from __future__ import annotations

from phase44_wayfinding_common import continuity_pairs, focus_specs, path_for_focus, phase44_artifact, render_wayfinding_page, stable_row_id


def build_drilldown_continuity_registry(outputs: dict) -> dict:
    rows = []
    for focus, _keywords in focus_specs():
        rows.extend(continuity_pairs(path_for_focus(outputs, focus, 5), "DCC", f"{focus}_drilldown_chain"))
    artifact = phase44_artifact("deterministic_drilldown_continuity_chain_v1")
    artifact.update({"drilldown_continuity_registry_id": stable_row_id("DCCREG", [row["continuity_path_id"] for row in rows]), "drilldown_chains": rows, "summary": {"drilldown_chain_count": len(rows)}})
    return artifact
