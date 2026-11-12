"""Snapshot comparison pair registry."""

from __future__ import annotations

from phase50_snapshot_common import build_phase50_registry, render_phase50_dashboard


def build_snapshot_comparison_registry(outputs: dict) -> dict:
    return build_phase50_registry(outputs, "snapshot_comparison")


def render_snapshot_comparison_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase50_dashboard(outputs, "snapshot_comparison")
