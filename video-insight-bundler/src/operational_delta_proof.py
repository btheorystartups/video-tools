"""Deterministic operational delta proofing."""

from __future__ import annotations

from phase48_diff_common import build_phase48_registry, render_phase48_dashboard


def build_operational_delta_registry(outputs: dict) -> dict:
    return build_phase48_registry(outputs, "operational_delta")


def render_operational_delta_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase48_dashboard(outputs, "operational_delta")
