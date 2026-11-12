"""Fine-grained operational regression localization."""

from __future__ import annotations

from phase49_delta_common import build_phase49_registry, render_phase49_dashboard


def build_regression_localization_registry(outputs: dict) -> dict:
    return build_phase49_registry(outputs, "regression_localization")


def render_regression_localization_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase49_dashboard(outputs, "regression_localization")
