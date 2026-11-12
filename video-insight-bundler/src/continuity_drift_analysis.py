"""Deterministic continuity drift analysis."""

from __future__ import annotations

from phase48_diff_common import build_phase48_registry, render_phase48_dashboard


def build_continuity_drift_registry(outputs: dict) -> dict:
    return build_phase48_registry(outputs, "continuity_drift")


def render_continuity_drift_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase48_dashboard(outputs, "continuity_drift")
