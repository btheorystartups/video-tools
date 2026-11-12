"""Deterministic rerun reproducibility comparison."""

from __future__ import annotations

from phase48_diff_common import build_phase48_registry, render_phase48_dashboard


def build_rerun_reproducibility_registry(outputs: dict) -> dict:
    return build_phase48_registry(outputs, "rerun_reproducibility")


def render_rerun_reproducibility_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase48_dashboard(outputs, "rerun_reproducibility")
