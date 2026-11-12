"""Evidence-chain diff provenance."""

from __future__ import annotations

from phase49_delta_common import build_phase49_registry, render_phase49_dashboard


def build_evidence_chain_diff_registry(outputs: dict) -> dict:
    return build_phase49_registry(outputs, "evidence_chain_diff")


def render_evidence_chain_diff_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase49_dashboard(outputs, "evidence_chain_diff")
