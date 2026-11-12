"""Known beta limitations for portable review exports."""

from __future__ import annotations

from stability import deterministic_id, utc_now_iso


def build_known_limitations_registry() -> dict:
    items = [
        ("deterministic_synthesis", "Synthesis ranks existing generated artifacts and does not replace reviewer judgment."),
        ("static_workspace", "Review workspace is offline/static; notes are not persisted unless the reviewer saves them externally."),
        ("visual_standardization", "Dashboard consistency validation detects structural signals but does not perform visual screenshot review."),
    ]
    return {"analysis_status": "complete", "method": "known_limitations_registry_v79", "generated_at_utc": utc_now_iso(), "limitations": [{"limitation_id": deterministic_id("LIMIT", key), "limitation_type": key, "disposition": "known_beta_limitation", "summary": text} for key, text in items], "summary": {"limitation_count": len(items)}}
