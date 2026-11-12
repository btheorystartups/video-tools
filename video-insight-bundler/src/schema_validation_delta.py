"""Schema and validation delta summaries."""

from __future__ import annotations

from phase49_delta_common import build_phase49_registry, render_phase49_dashboard


def build_schema_validation_delta_registry(outputs: dict) -> dict:
    return build_phase49_registry(outputs, "schema_validation_delta")


def render_schema_validation_delta_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase49_dashboard(outputs, "schema_validation_delta")
