"""Multi-run artifact lineage registry."""

from __future__ import annotations

from phase50_snapshot_common import build_phase50_registry, render_phase50_dashboard


def build_multi_run_artifact_lineage(outputs: dict) -> dict:
    return build_phase50_registry(outputs, "multi_run_artifact_lineage")


def render_multi_run_artifact_lineage_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase50_dashboard(outputs, "multi_run_artifact_lineage")
