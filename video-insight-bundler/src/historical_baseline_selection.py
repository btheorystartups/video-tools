"""Historical baseline selection registry."""

from __future__ import annotations

from phase50_snapshot_common import build_phase50_registry, render_phase50_dashboard


def build_historical_baseline_selection(outputs: dict) -> dict:
    return build_phase50_registry(outputs, "historical_baseline_selection")


def render_historical_baseline_selection_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase50_dashboard(outputs, "historical_baseline_selection")
