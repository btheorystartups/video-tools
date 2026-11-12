"""Deterministic rationale comparison for reviewer conflicts."""

from __future__ import annotations

from reviewer_adjudication import adjudication_artifact
from stability import deterministic_id


def build_rationale_diff_registry(conflicts: dict, import_registry: dict) -> dict:
    imports = {row.get("import_item_id"): row for row in import_registry.get("imported_items") or []}
    rows = []
    for conflict in conflicts.get("conflicts") or []:
        items = [imports.get(item_id) or {} for item_id in conflict.get("conflicting_items") or []]
        rationales = [item.get("rationale_text") or item.get("reviewer_notes") or "" for item in items if item]
        evidence_sets = [set(item.get("evidence_refs") or []) for item in items]
        rows.append(
            {
                "rationale_diff_id": deterministic_id("RDIFF2", conflict.get("conflict_id"), rationales),
                "conflict_id": conflict.get("conflict_id"),
                "source_item_id": conflict.get("source_item_id"),
                "reviewer_items": [item.get("import_item_id") for item in items if item.get("import_item_id")],
                "rationale_texts": rationales,
                "rationale_overlaps": _overlap(rationales),
                "rationale_conflicts": _rationale_conflicts(items, rationales),
                "evidence_refs": sorted({ref for refs in evidence_sets for ref in refs}),
                "evidence_agreement": sorted(set.intersection(*evidence_sets)) if evidence_sets else [],
                "evidence_disagreement": sorted(set.union(*evidence_sets) - set.intersection(*evidence_sets)) if evidence_sets else [],
                "governance_disagreement": conflict.get("governance_relevance") or any((item.get("governance_notes") or "") for item in items),
                "unresolved_ambiguity": _ambiguity(conflict, items, rationales),
            }
        )
    artifact = adjudication_artifact("deterministic_rationale_diff_engine_v1")
    artifact.update({"rationale_diff_registry_id": deterministic_id("RDIFFREG2", [row["rationale_diff_id"] for row in rows]), "rationale_diffs": rows, "summary": {"rationale_diff_count": len(rows), "unresolved_ambiguity_count": sum(1 for row in rows if row["unresolved_ambiguity"])}})
    return artifact


def _overlap(texts: list[str]) -> list[str]:
    token_sets = [set(text.lower().split()) for text in texts if text]
    if len(token_sets) < 2:
        return []
    return sorted(set.intersection(*token_sets))[:20]


def _rationale_conflicts(items: list[dict], texts: list[str]) -> list[str]:
    conflicts = []
    decisions = {item.get("decision") for item in items if item.get("decision")}
    escalations = {item.get("escalation_state") for item in items if item.get("escalation_state")}
    if len(decisions) > 1:
        conflicts.append("reviewer decisions differ")
    if len(escalations) > 1:
        conflicts.append("reviewer escalation states differ")
    if len({text.strip().lower() for text in texts if text.strip()}) > 1:
        conflicts.append("reviewer rationale text differs")
    return conflicts


def _ambiguity(conflict: dict, items: list[dict], texts: list[str]) -> list[str]:
    ambiguity = []
    if not any(item.get("evidence_refs") for item in items):
        ambiguity.append("insufficient evidence references")
    if len({text.strip().lower() for text in texts if text.strip()}) > 1:
        ambiguity.append("conflicting rationale")
    if conflict.get("governance_relevance"):
        ambiguity.append("governance uncertainty")
    return ambiguity
