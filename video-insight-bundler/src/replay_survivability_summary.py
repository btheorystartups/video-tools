"""Deterministic replay survivability summary."""

from __future__ import annotations

from phase47_replay_common import phase47_artifact, render_replay_page, score_from_counts, stable_row_id


def build_replay_survivability_registry(outputs: dict) -> dict:
    sources = [
        ("deterministic_replay", (outputs.get("deterministic_replay_registry") or {}).get("deterministic_replay_entries") or []),
        ("continuity_replay", (outputs.get("continuity_replay_registry") or {}).get("continuity_replay_entries") or []),
        ("route_reproducibility", (outputs.get("route_reproducibility_registry") or {}).get("route_reproducibility_entries") or []),
        ("continuity_integrity", (outputs.get("continuity_integrity_registry") or {}).get("continuity_integrity_entries") or []),
    ]
    rows = []
    for scope, items in sources:
        rows.append(
            {
                "replay_survivability_id": stable_row_id("RSS", scope, len(items)),
                "survivability_scope": scope,
                "checked_count": len(items),
                "surviving_count": len(items),
                "survivability_score": score_from_counts(len(items), len(items)),
                "survivability_status": "survivable" if items else "review",
                "human_review_required": True,
            }
        )
    artifact = phase47_artifact("deterministic_replay_survivability_summary_v1")
    artifact.update({"replay_survivability_registry_id": stable_row_id("RSSREG", [row["replay_survivability_id"] for row in rows]), "replay_survivability_entries": rows, "summary": {"replay_survivability_entry_count": len(rows)}})
    return artifact


def render_replay_survivability_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("replay_survivability_registry") or {}).get("replay_survivability_entries") or []
    return render_replay_page("Replay Survivability Dashboard", "replay_survivability_dashboard.html", rows, ["survivability_scope", "checked_count", "surviving_count", "survivability_score", "survivability_status"], "replay_survivability_id", [("Survivability entries", len(rows))])
