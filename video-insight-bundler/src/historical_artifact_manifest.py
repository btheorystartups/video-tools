"""Historical artifact manifest registry."""

from __future__ import annotations

from phase50_snapshot_common import build_phase50_registry, render_phase50_dashboard


def build_historical_artifact_manifest(outputs: dict) -> dict:
    return build_phase50_registry(outputs, "historical_artifact_manifest")


def render_historical_artifact_manifest_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase50_dashboard(outputs, "historical_artifact_manifest")
