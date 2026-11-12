"""Deterministic replay regression dashboard registry."""

from __future__ import annotations

from phase48_diff_common import build_phase48_registry, render_phase48_dashboard


def build_replay_regression_dashboard_registry(outputs: dict) -> dict:
    return build_phase48_registry(outputs, "replay_regression_dashboard")


def render_replay_regression_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase48_dashboard(outputs, "replay_regression_dashboard")
