"""Deterministic operational traversal replay fixtures."""

from __future__ import annotations

from phase47_replay_common import phase47_artifact, render_replay_page, replay_sequences, stable_row_id


def build_traversal_fixture_registry(outputs: dict) -> dict:
    rows = []
    for window_start in range(0, min(len(replay_sequences(outputs, 40)), 40), 5):
        window = replay_sequences(outputs, 40)[window_start : window_start + 5]
        rows.append(
            {
                "traversal_fixture_id": stable_row_id("TRF", window_start, [row.get("sequence_id") for row in window]),
                "fixture_name": f"static_replay_window_{window_start // 5 + 1}",
                "step_count": len(window),
                "start_sequence_id": window[0].get("sequence_id") if window else None,
                "end_sequence_id": window[-1].get("sequence_id") if window else None,
                "fixture_status": "available" if window else "review",
                "human_review_required": True,
            }
        )
    artifact = phase47_artifact("deterministic_traversal_replay_fixture_v1")
    artifact.update({"traversal_fixture_registry_id": stable_row_id("TRFREG", [row["traversal_fixture_id"] for row in rows]), "traversal_fixture_entries": rows, "summary": {"traversal_fixture_entry_count": len(rows)}})
    return artifact


def render_traversal_fixture_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("traversal_fixture_registry") or {}).get("traversal_fixture_entries") or []
    return render_replay_page("Traversal Fixture Dashboard", "traversal_fixture_dashboard.html", rows, ["fixture_name", "step_count", "start_sequence_id", "end_sequence_id", "fixture_status"], "traversal_fixture_id", [("Traversal fixtures", len(rows))])
