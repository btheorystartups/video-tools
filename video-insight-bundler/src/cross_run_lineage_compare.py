"""Deterministic cross-run lineage comparison."""

from __future__ import annotations

from phase48_diff_common import build_phase48_registry, render_phase48_dashboard


def build_cross_run_lineage_registry(outputs: dict) -> dict:
    return build_phase48_registry(outputs, "cross_run_lineage")


def render_cross_run_lineage_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase48_dashboard(outputs, "cross_run_lineage")
