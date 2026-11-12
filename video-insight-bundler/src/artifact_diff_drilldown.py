"""Artifact-level operational diff drilldowns."""

from __future__ import annotations

from phase49_delta_common import build_phase49_registry, render_phase49_dashboard


def build_artifact_diff_drilldown_registry(outputs: dict) -> dict:
    return build_phase49_registry(outputs, "artifact_diff_drilldown")


def render_artifact_diff_drilldown_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase49_dashboard(outputs, "artifact_diff_drilldown")
