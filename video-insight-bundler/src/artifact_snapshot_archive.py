"""Artifact snapshot archive registry."""

from __future__ import annotations

from phase50_snapshot_common import build_phase50_registry, render_phase50_dashboard


def build_artifact_snapshot_archive(outputs: dict) -> dict:
    return build_phase50_registry(outputs, "artifact_snapshot_archive")


def render_artifact_snapshot_archive_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase50_dashboard(outputs, "artifact_snapshot_archive")
