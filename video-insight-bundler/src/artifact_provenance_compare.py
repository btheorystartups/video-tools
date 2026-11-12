"""Artifact provenance comparison."""

from __future__ import annotations

from phase49_delta_common import build_phase49_registry, render_phase49_dashboard


def build_artifact_provenance_compare_registry(outputs: dict) -> dict:
    return build_phase49_registry(outputs, "artifact_provenance_compare")


def render_artifact_provenance_compare_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase49_dashboard(outputs, "artifact_provenance_compare")
