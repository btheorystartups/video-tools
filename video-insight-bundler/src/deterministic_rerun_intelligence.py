"""Deterministic rerun intelligence."""

from __future__ import annotations

from phase48_diff_common import build_phase48_registry, render_phase48_dashboard


def build_deterministic_rerun_registry(outputs: dict) -> dict:
    return build_phase48_registry(outputs, "deterministic_rerun")


def render_deterministic_rerun_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase48_dashboard(outputs, "deterministic_rerun")
