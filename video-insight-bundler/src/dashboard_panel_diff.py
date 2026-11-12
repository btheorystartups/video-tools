"""Dashboard panel diff summaries."""

from __future__ import annotations

from phase49_delta_common import build_phase49_registry, render_phase49_dashboard


def build_dashboard_panel_diff_registry(outputs: dict) -> dict:
    return build_phase49_registry(outputs, "dashboard_panel_diff")


def render_dashboard_panel_diff_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase49_dashboard(outputs, "dashboard_panel_diff")
