"""Archived evidence chain snapshot registry."""

from __future__ import annotations

from phase50_snapshot_common import build_phase50_registry, render_phase50_dashboard


def build_archived_evidence_chain_snapshot_registry(outputs: dict) -> dict:
    return build_phase50_registry(outputs, "archived_evidence_chain_snapshot")


def render_archived_evidence_chain_snapshot_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase50_dashboard(outputs, "archived_evidence_chain_snapshot")
