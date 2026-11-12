"""Corpus and video version comparison readiness registry."""

from __future__ import annotations

from phase50_snapshot_common import build_phase50_registry, render_phase50_dashboard


def build_corpus_version_comparison_readiness(outputs: dict) -> dict:
    return build_phase50_registry(outputs, "corpus_version_comparison_readiness")


def render_corpus_version_comparison_readiness_dashboard(outputs: dict) -> dict[str, str]:
    return render_phase50_dashboard(outputs, "corpus_version_comparison_readiness")
