"""Operator attention pressure heatmaps."""

from __future__ import annotations

from operator_workflow_common import ergonomics_links, phase40_artifact, render_registry_page, risk_level, stable_row_id


def build_operator_attention_heatmap_registry(outputs: dict) -> dict:
    specs = [
        ("unresolved_ambiguity_concentration", len((outputs.get("unresolved_ambiguity_registry") or {}).get("ambiguities") or [])),
        ("governance_pressure_concentration", len((outputs.get("governance_conflict_analysis") or {}).get("governance_conflicts") or [])),
        ("escalation_density", len((outputs.get("governance_escalation_events") or {}).get("escalation_events") or []) + len((outputs.get("review_escalation_registry") or {}).get("escalation_items") or [])),
        ("queue_overload_regions", sum(len((outputs.get(key) or {}).get("queue_items") or []) for key in ["review_queue_registry", "adjudication_queue_registry", "unresolved_conflict_queue", "reconciliation_required_queue"])),
        ("high_friction_workflow_regions", len((outputs.get("interruption_recovery_registry") or {}).get("recovery_entries") or []) + len((outputs.get("session_ergonomics_registry") or {}).get("ergonomics_entries") or [])),
    ]
    max_count = max([count for _, count in specs] or [1], default=1)
    rows = []
    for dimension, count in specs:
        score = round(count / max(1, max_count), 3)
        rows.append({"operator_attention_heatmap_id": stable_row_id("OAH", dimension, count), "dimension": dimension, "attention_count": count, "attention_pressure_score": score, "pressure_level": risk_level(score), "human_review_required": True})
    artifact = phase40_artifact("deterministic_operator_attention_heatmap_v1")
    artifact.update({"operator_attention_heatmap_registry_id": stable_row_id("OAHREG", [row["operator_attention_heatmap_id"] for row in rows]), "attention_cells": rows, "summary": {"attention_cell_count": len(rows), "max_attention_count": max_count}})
    return artifact


def render_operator_attention_heatmap_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("operator_attention_heatmap_registry") or {}).get("attention_cells") or []
    return {"operator_attention_heatmap_dashboard.html": render_registry_page("Operator Attention Heatmap Dashboard", "Session Ergonomics", "operator_attention_heatmap_dashboard.html", rows, ["dimension", "attention_count", "attention_pressure_score", "pressure_level"], "operator_attention_heatmap_id", [("Cells", len(rows))], ergonomics_links(""))}
