"""Deterministic deltas between observed and simulated revision states."""

from __future__ import annotations

from stability import canonical_json, sha256_text


CATEGORY_ORDER = [
    "metadata",
    "recommendation",
    "timing",
    "media",
    "visualization_reporting",
    "analysis_only",
]


def _short_hash(data: dict) -> str:
    return sha256_text(canonical_json(data))[:16]


def _score_delta(from_report: dict, to_report: dict) -> float:
    return round(
        float(to_report.get("release_readiness_score", 0.0)) - float(from_report.get("release_readiness_score", 0.0)),
        3,
    )


def build_revision_deltas(root_revision: dict, candidate_states: list[dict], candidates: list[dict]) -> dict:
    by_revision = {state.get("revision_id"): state for state in candidate_states}
    by_candidate = {candidate.get("simulated_revision_id"): candidate for candidate in candidates}
    deltas = []
    for to_revision_id, state in sorted(by_revision.items()):
        candidate = by_candidate.get(to_revision_id, {})
        changes = candidate.get("proposed_changes") or []
        categories = {category: [] for category in CATEGORY_ORDER}
        for change in changes:
            change_type = change.get("change_type", "analysis_only")
            category = "visualization_reporting" if change_type in {"report", "visualization"} else change_type
            if category not in categories:
                category = "analysis_only"
            categories[category].append(change)

        delta_seed = {
            "from_revision_id": root_revision.get("revision_id"),
            "to_revision_id": to_revision_id,
            "changes": changes,
            "score_delta": _score_delta(root_revision.get("release_readiness", {}), state.get("release_readiness", {})),
        }
        delta = {
            "delta_id": f"DELTA_{_short_hash(delta_seed)}",
            "from_revision_id": root_revision.get("revision_id"),
            "to_revision_id": to_revision_id,
            "candidate_id": candidate.get("candidate_id"),
            "changed_fields": sorted({change.get("field", change.get("change_type", "unknown")) for change in changes}),
            "changed_metrics": sorted(candidate.get("affected_metrics") or []),
            "affected_segments": sorted(candidate.get("affected_segments") or []),
            "affected_artifacts": sorted({artifact for change in changes for artifact in change.get("affected_artifacts", [])}),
            "change_categories": categories,
            "score_delta": _score_delta(root_revision.get("release_readiness", {}), state.get("release_readiness", {})),
            "constraint_delta": {
                "from_pass_rate": root_revision.get("constraint_summary", {}).get("constraint_pass_rate"),
                "to_pass_rate": state.get("constraint_summary", {}).get("constraint_pass_rate"),
            },
            "release_readiness_delta": {
                "from_class": root_revision.get("release_readiness", {}).get("release_readiness_class"),
                "to_class": state.get("release_readiness", {}).get("release_readiness_class"),
                "score_delta": _score_delta(root_revision.get("release_readiness", {}), state.get("release_readiness", {})),
            },
            "mutation_safety_delta": {
                "from": root_revision.get("mutation_safety", {}).get("mutation_safety_class", "SAFE_ANALYSIS_ONLY"),
                "to": candidate.get("mutation_safety_class"),
            },
            "identity_preservation_delta": round(float(candidate.get("identity_preservation_score", 1.0)) - 1.0, 3),
            "human_review_required": bool(candidate.get("human_review_required")),
            "rollback_complexity": candidate.get("rollback_complexity", "low"),
        }
        deltas.append(delta)
    return {"deltas": sorted(deltas, key=lambda row: row["candidate_id"] or row["to_revision_id"])}
