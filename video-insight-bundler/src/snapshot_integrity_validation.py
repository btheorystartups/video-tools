"""Snapshot integrity validation registry."""

from __future__ import annotations

from phase50_snapshot_common import build_phase50_registry, render_phase50_dashboard


def build_snapshot_integrity_validation(outputs: dict) -> dict:
    return build_phase50_registry(outputs, "snapshot_integrity_validation")


def render_snapshot_integrity_validation_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase50_dashboard(outputs, "snapshot_integrity_validation")
