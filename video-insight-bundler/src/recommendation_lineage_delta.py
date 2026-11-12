"""Recommendation-lineage delta comparison."""

from __future__ import annotations

from phase49_delta_common import build_phase49_registry, render_phase49_dashboard


def build_recommendation_lineage_delta_registry(outputs: dict) -> dict:
    return build_phase49_registry(outputs, "recommendation_lineage_delta")


def render_recommendation_lineage_delta_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase49_dashboard(outputs, "recommendation_lineage_delta")
