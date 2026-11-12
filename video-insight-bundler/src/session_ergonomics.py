"""Long-session operator ergonomics registries and dashboards."""

from __future__ import annotations

from operator_workflow_common import ergonomics_links, phase40_artifact, render_registry_page, risk_level, stable_row_id


def build_session_ergonomics_registry(outputs: dict) -> dict:
    rows = [
        _row("review_density", _queue_count(outputs), "queue_items", "Chunk review queues and show compact summaries first."),
        _row("navigation_friction", _dashboard_count(outputs), "dashboard_entries", "Prefer compact navigation groups and resume links."),
        _row("queue_pressure", _queue_count(outputs) + _ambiguity_count(outputs), "pending_items", "Expose high-pressure queues as survivable chunks."),
        _row("evidence_overload", _evidence_count(outputs), "evidence_refs", "Collapse duplicate evidence and keep detail on demand."),
        _row("workflow_interruption_risk", _escalation_count(outputs) + _followup_count(outputs), "open_continuity_items", "Offer deterministic resume points and interruption summaries."),
        _row("context_switch_load", _domain_count(outputs), "active_domains", "Group related review domains in compact paths."),
    ]
    artifact = phase40_artifact("deterministic_session_ergonomics_v1")
    artifact.update({"session_ergonomics_registry_id": stable_row_id("SERGREG", [row["session_ergonomics_id"] for row in rows]), "ergonomics_entries": rows, "summary": {"entry_count": len(rows), "high_pressure_count": sum(1 for row in rows if row["pressure_level"] == "high")}})
    return artifact


def render_session_ergonomics_dashboards(outputs: dict) -> dict[str, str]:
    links = ergonomics_links("")
    specs = {
        "session_ergonomics_dashboard.html": ("Session Ergonomics Dashboard", (outputs.get("session_ergonomics_registry") or {}).get("ergonomics_entries") or [], ["signal", "observed_count", "pressure_level", "operator_support"], "session_ergonomics_id"),
    }
    return {filename: render_registry_page(title, "Session Ergonomics", filename, rows, fields, id_field, [("Rows", len(rows))], links) for filename, (title, rows, fields, id_field) in specs.items()}


def _row(signal: str, count: int, unit: str, support: str) -> dict:
    score = min(1.0, count / 10.0)
    return {
        "session_ergonomics_id": stable_row_id("SERG", signal, count),
        "signal": signal,
        "observed_count": count,
        "unit": unit,
        "pressure_score": round(score, 3),
        "pressure_level": risk_level(score),
        "operator_support": support,
        "deterministic_no_adaptive_behavior": True,
    }


def _queue_count(outputs: dict) -> int:
    return sum(len((outputs.get(key) or {}).get("queue_items") or []) for key in ["review_queue_registry", "adjudication_queue_registry", "unresolved_conflict_queue", "reconciliation_required_queue", "governance_adjudication_queue", "imported_review_followup_queue"])


def _dashboard_count(outputs: dict) -> int:
    return len((outputs.get("dashboard_render_registry") or {}).get("render_entries") or [])


def _ambiguity_count(outputs: dict) -> int:
    return len((outputs.get("unresolved_ambiguity_registry") or {}).get("ambiguities") or [])


def _escalation_count(outputs: dict) -> int:
    return len((outputs.get("governance_escalation_events") or {}).get("escalation_events") or []) + len((outputs.get("review_escalation_registry") or {}).get("escalation_items") or [])


def _followup_count(outputs: dict) -> int:
    return len((outputs.get("review_followup_registry") or {}).get("followup_items") or []) + len((outputs.get("imported_review_followup_queue") or {}).get("queue_items") or [])


def _evidence_count(outputs: dict) -> int:
    text = str(outputs.get("recommendation_traceability") or {}) + str(outputs.get("review_handoff_packets") or {})
    return text.count("evidence") + len((outputs.get("inline_evidence_preview_index") or {}).get("previews") or [])


def _domain_count(outputs: dict) -> int:
    return sum(1 for key in ["review_queue_registry", "reconciliation_registry", "adjudication_queue_registry", "governance_review_session", "performance_profile_registry"] if outputs.get(key))
