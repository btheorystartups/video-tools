"""Route-level replay delta provenance."""

from __future__ import annotations

from phase49_delta_common import build_phase49_registry, render_phase49_dashboard


def build_replay_route_delta_registry(outputs: dict) -> dict:
    return build_phase49_registry(outputs, "replay_route_delta")


def render_replay_route_delta_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase49_dashboard(outputs, "replay_route_delta")
