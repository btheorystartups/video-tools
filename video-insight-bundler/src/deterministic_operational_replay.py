"""Browserless deterministic operational replay registry."""

from __future__ import annotations

from phase47_replay_common import phase47_artifact, render_replay_page, replay_sequences, stable_row_id


def build_deterministic_replay_registry(outputs: dict) -> dict:
    rows = replay_sequences(outputs, 32)
    artifact = phase47_artifact("browserless_deterministic_operational_replay_v1")
    artifact.update(
        {
            "deterministic_replay_registry_id": stable_row_id("DORREG", [row["sequence_id"] for row in rows]),
            "deterministic_replay_entries": rows,
            "summary": {"deterministic_replay_entry_count": len(rows), "browserless_replay_entry_count": len(rows)},
        }
    )
    return artifact


def render_deterministic_replay_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("deterministic_replay_registry") or {}).get("deterministic_replay_entries") or []
    return render_replay_page("Deterministic Replay Dashboard", "deterministic_replay_dashboard.html", rows, ["sequence_order", "source_event_id", "dashboard_href", "replay_step_type", "replay_status"], "sequence_id", [("Replay entries", len(rows))])
