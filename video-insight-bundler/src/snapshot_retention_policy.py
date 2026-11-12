"""Snapshot retention policy metadata."""

from __future__ import annotations

from phase50_snapshot_common import build_phase50_registry, render_phase50_dashboard


def build_snapshot_retention_policy(outputs: dict) -> dict:
    return build_phase50_registry(outputs, "snapshot_retention_policy")


def render_snapshot_retention_policy_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase50_dashboard(outputs, "snapshot_retention_policy")
