"""Operator-facing delta drilldown navigation."""

from __future__ import annotations

from phase49_delta_common import build_phase49_registry, render_phase49_dashboard


def build_delta_drilldown_navigation_registry(outputs: dict) -> dict:
    return build_phase49_registry(outputs, "delta_drilldown_navigation")


def render_delta_drilldown_navigation_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase49_dashboard(outputs, "delta_drilldown_navigation")
