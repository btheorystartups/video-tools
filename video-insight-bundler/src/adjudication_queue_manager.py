"""Prioritized queues for governed conflict adjudication."""

from __future__ import annotations

from reviewer_adjudication import adjudication_artifact
from review_operational_common import severity_rank
from stability import deterministic_id


def build_adjudication_queue_registry(governance_conflict_analysis: dict, unresolved_ambiguity_registry: dict, consensus_workflow_registry: dict, rationale_diff_registry: dict) -> dict:
    ambiguities = {row.get("conflict_id"): row for row in unresolved_ambiguity_registry.get("ambiguities") or []}
    consensus = {row.get("conflict_id"): row for row in consensus_workflow_registry.get("consensus_workflows") or []}
    diffs = {row.get("conflict_id"): row for row in rationale_diff_registry.get("rationale_diffs") or []}
    rows = []
    for impact in governance_conflict_analysis.get("governance_conflicts") or []:
        conflict_id = impact.get("conflict_id")
        ambiguity = ambiguities.get(conflict_id) or {}
        diff = diffs.get(conflict_id) or {}
        queue_types = _queue_types(impact, ambiguity, consensus.get(conflict_id) or {}, diff)
        score = _score(impact, ambiguity, diff)
        rows.append(
            {
                "queue_item_id": deterministic_id("ADJQ", conflict_id, queue_types, score),
                "conflict_id": conflict_id,
                "source_item_id": impact.get("source_item_id"),
                "queue_types": queue_types,
                "priority_score": score,
                "governance_severity": impact.get("governance_severity"),
                "ambiguity_count": len(ambiguity.get("ambiguity_types") or []),
                "rationale_conflict_count": len(diff.get("rationale_conflicts") or []),
                "suggested_next_action": "Open arbitration packet and record explicit human adjudication rationale.",
                "manual_review_required": True,
            }
        )
    rows = sorted(rows, key=lambda row: (-row["priority_score"], row["conflict_id"] or ""))
    artifact = adjudication_artifact("deterministic_adjudication_queue_registry_v1")
    artifact.update({"adjudication_queue_registry_id": deterministic_id("ADJQREG", [row["queue_item_id"] for row in rows]), "queue_items": rows, "summary": {"queue_item_count": len(rows), "governance_critical_count": sum(1 for row in rows if "governance critical" in row["queue_types"])}})
    return artifact


def build_adjudication_queues(adjudication_queue_registry: dict) -> dict:
    items = adjudication_queue_registry.get("queue_items") or []
    return {
        "governance_adjudication_queue": _queue("governance_adjudication_queue", [row for row in items if "governance critical" in row["queue_types"] or "governance review" in row["queue_types"]]),
        "reviewer_disagreement_queue": _queue("reviewer_disagreement_queue", [row for row in items if "most severe disagreement" in row["queue_types"] or "unresolved rationale conflicts" in row["queue_types"]]),
        "unresolved_ambiguity_queue": _queue("unresolved_ambiguity_queue", [row for row in items if "highest ambiguity" in row["queue_types"]]),
        "arbitration_required_queue": _queue("arbitration_required_queue", [row for row in items if "arbitration required" in row["queue_types"]]),
        "consensus_required_queue": _queue("consensus_required_queue", [row for row in items if "consensus required" in row["queue_types"]]),
    }


def _queue(name: str, rows: list[dict]) -> dict:
    artifact = adjudication_artifact(f"deterministic_{name}_v1")
    artifact.update({f"{name}_id": deterministic_id(name.upper()[:10], [row.get("queue_item_id") for row in rows]), "queue_items": rows, "summary": {"queue_item_count": len(rows)}})
    return artifact


def _queue_types(impact: dict, ambiguity: dict, consensus: dict, diff: dict) -> list[str]:
    types = []
    if impact.get("governance_severity") == "critical":
        types.append("governance critical")
    if impact.get("requires_governance_reviewer"):
        types.append("governance review")
    if len(ambiguity.get("ambiguity_types") or []) >= 2:
        types.append("highest ambiguity")
    if severity_rank(impact.get("governance_severity")) >= 4:
        types.append("most severe disagreement")
    if impact.get("requires_arbitration"):
        types.append("arbitration required")
    if consensus.get("consensus_state") != "consensus_reached_with_rationale":
        types.append("consensus required")
    if diff.get("rationale_conflicts"):
        types.append("unresolved rationale conflicts")
    return sorted(set(types or ["manual adjudication"]))


def _score(impact: dict, ambiguity: dict, diff: dict) -> float:
    return round(min(1.0, severity_rank(impact.get("governance_severity")) / 5 + (0.08 * len(ambiguity.get("ambiguity_types") or [])) + (0.05 * len(diff.get("rationale_conflicts") or []))), 3)
