"""Continuity edge diffing."""

from __future__ import annotations

from phase49_delta_common import build_phase49_registry, render_phase49_dashboard


def build_continuity_edge_diff_registry(outputs: dict) -> dict:
    return build_phase49_registry(outputs, "continuity_edge_diff")


def render_continuity_edge_diff_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase49_dashboard(outputs, "continuity_edge_diff")
