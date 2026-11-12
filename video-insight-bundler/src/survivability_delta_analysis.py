"""Deterministic survivability delta analysis."""

from __future__ import annotations

from phase48_diff_common import build_phase48_registry, render_phase48_dashboard


def build_survivability_delta_registry(outputs: dict) -> dict:
    return build_phase48_registry(outputs, "survivability_delta")


def render_survivability_delta_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase48_dashboard(outputs, "survivability_delta")
