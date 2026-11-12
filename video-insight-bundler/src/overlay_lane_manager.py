"""Group timeline overlays into compact deterministic lanes."""

from __future__ import annotations

from collections import Counter, defaultdict

from intelligence_common import base_artifact
from stability import deterministic_id
from temporal_evidence_index import LIMITATION


LANE_GROUPS = {
    "speech_pacing_overlay": ("speech_pacing", "Speech / pacing"),
    "acoustic_energy_overlay": ("acoustic_intensity", "Acoustic intensity"),
    "silence_overlay": ("silence_pause", "Silence / pause"),
    "rhetorical_pressure_overlay": ("rhetorical_pressure", "Rhetorical pressure"),
    "topic_continuity_overlay": ("topic_continuity", "Topic continuity"),
    "visual_reset_overlay": ("visual_reset", "Visual reset"),
    "boundary_diagnostic_overlay": ("boundary_diagnostics", "Boundary diagnostics"),
    "recommendation_overlay": ("recommendations", "Recommendations"),
    "blocker_overlay": ("blockers", "Blockers"),
    "archetype_overlay": ("archetypes", "Archetypes"),
    "governance_overlay": ("governance", "Governance"),
}


def build_overlay_lane_registry(overlays: dict) -> dict:
    grouped: dict[tuple[str | None, str], list[dict]] = defaultdict(list)
    for overlay in overlays.get("overlays") or []:
        lane_id, _ = LANE_GROUPS.get(overlay.get("overlay_type"), ("other", "Other"))
        grouped[(overlay.get("video_id"), lane_id)].append(overlay)
    lanes = []
    for (video_id, lane_id), rows in sorted(grouped.items(), key=lambda item: (item[0][0] or "", item[0][1])):
        label = next((label for key, (lid, label) in LANE_GROUPS.items() if lid == lane_id), lane_id.replace("_", " ").title())
        severity_counts = Counter(row.get("severity") or "low" for row in rows)
        high = severity_counts.get("high", 0)
        visible = lane_id in {"speech_pacing", "rhetorical_pressure", "recommendations", "blockers", "governance"} or high > 0
        lanes.append(
            {
                "lane_id": deterministic_id("OLANE", video_id, lane_id),
                "video_id": video_id,
                "lane_key": lane_id,
                "lane_label": label,
                "overlay_count": len(rows),
                "visible_by_default": visible,
                "severity_summary": dict(severity_counts),
                "related_overlays": [row.get("overlay_id") for row in rows],
                "collapse_state_default": "expanded" if visible else "collapsed",
                "explanation": "Grouped lane for faster timeline scanning while preserving access to every overlay.",
                "evidence_refs": sorted({ref for row in rows for ref in (row.get("evidence_refs") or [])}),
                "non_claim_limitation": LIMITATION,
            }
        )
    output = base_artifact(method="deterministic_overlay_lane_manager_v1")
    output.update({"overlay_lane_registry_id": deterministic_id("OLANEREG", [row["lane_id"] for row in lanes]), "lane_groups": list(LANE_GROUPS.values()), "lanes": lanes, "summary": {"lane_count": len(lanes), "overlay_count": sum(row.get("overlay_count", 0) for row in lanes)}, "limitations": [LIMITATION]})
    return output
