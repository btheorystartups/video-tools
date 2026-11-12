"""Panel-level what-changed explanations."""

from __future__ import annotations

from phase49_delta_common import build_phase49_registry, render_phase49_dashboard


def build_panel_change_explainer_registry(outputs: dict) -> dict:
    return build_phase49_registry(outputs, "panel_change_explainer")


def render_panel_change_explainer_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase49_dashboard(outputs, "panel_change_explainer")
