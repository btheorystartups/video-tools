"""Route-level replay delta dashboard registry."""

from __future__ import annotations

from phase49_delta_common import build_phase49_registry, render_phase49_dashboard


def build_route_delta_dashboard_registry(outputs: dict) -> dict:
    return build_phase49_registry(outputs, "route_delta_dashboard")


def render_route_delta_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase49_dashboard(outputs, "route_delta_dashboard")
