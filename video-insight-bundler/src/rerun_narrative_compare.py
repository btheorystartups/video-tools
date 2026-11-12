"""Deterministic rerun narrative comparison."""

from __future__ import annotations

from phase48_diff_common import build_phase48_registry, render_phase48_dashboard


def build_rerun_narrative_registry(outputs: dict) -> dict:
    return build_phase48_registry(outputs, "rerun_narrative")


def render_rerun_narrative_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase48_dashboard(outputs, "rerun_narrative")
