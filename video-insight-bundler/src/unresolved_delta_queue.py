"""Unresolved delta review queue."""

from __future__ import annotations

from phase49_delta_common import build_phase49_registry, render_phase49_dashboard


def build_unresolved_delta_queue(outputs: dict) -> dict:
    return build_phase49_registry(outputs, "unresolved_delta_queue")


def render_unresolved_delta_queue_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase49_dashboard(outputs, "unresolved_delta_queue")
