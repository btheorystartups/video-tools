"""Deterministic replay regression analysis."""

from __future__ import annotations

from phase48_diff_common import build_phase48_registry, render_phase48_dashboard


def build_replay_regression_registry(outputs: dict) -> dict:
    return build_phase48_registry(outputs, "replay_regression")


def render_replay_regression_analysis_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase48_dashboard(outputs, "replay_regression")
