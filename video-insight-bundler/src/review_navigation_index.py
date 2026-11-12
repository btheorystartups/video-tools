"""Navigation indexes for Tier 1 governance review."""

from __future__ import annotations

from intelligence_common import base_artifact, deterministic_id


def build_review_navigation_index(compressed_review_queue: dict, tier_1_blocker_disposition: dict, blocker_analysis: dict, archetype_remediation: dict) -> dict:
    blockers = {row.get("blocker_id"): row for row in tier_1_blocker_disposition.get("blocker_dispositions", [])}
    hard_by_family = {}
    for row in blocker_analysis.get("blockers", []):
        hard_by_family.setdefault(row.get("blocker_label") or row.get("blocker_type") or "unknown", []).append(row)
    archetypes = {row.get("archetype_label") or row.get("archetype"): row for row in archetype_remediation.get("archetype_remediations", [])}
    nav_rows = []
    evidence_rows = []
    focus_rows = []
    for item in compressed_review_queue.get("compressed_items", []):
        if item.get("tier") != 1:
            continue
        related = [row for row in blockers.values() if row.get("source_compressed_item_id") == item.get("compressed_item_id")]
        blocker_id = related[0].get("blocker_id") if related else item.get("compressed_item_id")
        family = item.get("issue_family") or "unknown"
        severity = "hard_blocker" if item.get("tier") == 1 else "review"
        effort = _effort(item)
        false_positive = _potential(family, "false_positive")
        accepted_risk = _potential(family, "accepted_risk")
        nav_rows.append(
            {
                "navigation_id": deterministic_id("RNAV", blocker_id, item.get("compressed_item_id")),
                "blocker_id": blocker_id,
                "source_compressed_item_id": item.get("compressed_item_id"),
                "priority_score": item.get("priority_score") or 0.0,
                "blocker_family": family,
                "videos": item.get("affected_videos") or [],
                "segments": item.get("affected_segments") or [],
                "archetype": _archetype_for(family, archetypes),
                "pressure_family": "editorial_pressure" if "pressure" in family else "readiness_or_governance",
                "governance_severity": severity,
                "readiness_impact": item.get("expected_readiness_effect"),
                "review_effort": effort,
                "likely_false_positive_potential": false_positive,
                "likely_accepted_risk_potential": accepted_risk,
                "evidence_refs": item.get("evidence_refs") or [],
                "raw_review_item_refs": item.get("original_item_refs") or [],
            }
        )
        evidence_rows.append(
            {
                "blocker_id": blocker_id,
                "evidence_refs": item.get("evidence_refs") or [],
                "raw_review_item_refs": item.get("original_item_refs") or [],
                "artifact_refs": sorted({(ref.split("#", 1)[0] if "#" in ref else ref) for ref in item.get("evidence_refs", [])}),
            }
        )
        focus_rows.append(
            {
                "focus_id": deterministic_id("RFOCUS", blocker_id, effort, item.get("priority_score")),
                "blocker_id": blocker_id,
                "priority_score": item.get("priority_score") or 0.0,
                "review_effort": effort,
                "focus_reason": _focus_reason(family, item),
                "first_evidence_ref": (item.get("evidence_refs") or [""])[0],
                "recommended_next_action": "Open the evidence refs, choose a disposition only if evidence supports it, then rerun corpus reassessment.",
            }
        )
    nav_rows = sorted(nav_rows, key=lambda row: (-row["priority_score"] if "priority_score" in row else 0, row["blocker_family"], row["blocker_id"]))
    focus_rows = sorted(focus_rows, key=lambda row: (-row["priority_score"], row["review_effort"], row["blocker_id"]))
    index = base_artifact(method="deterministic_review_navigation_index_v1")
    index.update(
        {
            "review_navigation_index_id": deterministic_id("RNAVSET", [(row["blocker_id"], row["source_compressed_item_id"]) for row in nav_rows]),
            "navigation_items": nav_rows,
            "summary": {"navigation_item_count": len(nav_rows), "tier_1_navigation_count": len(nav_rows)},
        }
    )
    evidence = base_artifact(method="deterministic_tier_1_evidence_navigation_v1")
    evidence.update({"tier_1_evidence_navigation_id": deterministic_id("T1EVIDNAV", evidence_rows), "evidence_navigation": evidence_rows, "summary": {"evidence_navigation_count": len(evidence_rows)}})
    focus = base_artifact(method="deterministic_reviewer_focus_queue_v1")
    focus.update({"reviewer_focus_queue_id": deterministic_id("RFOCUSSET", [(row["blocker_id"], row["priority_score"]) for row in focus_rows]), "focus_items": focus_rows, "summary": {"focus_queue_count": len(focus_rows)}})
    return {"review_navigation_index": index, "tier_1_evidence_navigation": evidence, "reviewer_focus_queue": focus}


def _effort(item: dict) -> int:
    return min(5, max(1, len(item.get("evidence_refs") or []) + len(item.get("affected_segments") or []) // 3 + 1))


def _potential(family: str, kind: str) -> str:
    if kind == "false_positive" and ("counterfactual" in family or "pressure" in family):
        return "medium"
    if kind == "accepted_risk" and "readiness" in family:
        return "low"
    return "low"


def _archetype_for(family: str, archetypes: dict) -> str:
    for key in sorted(archetypes):
        if key and key.lower() in family.lower():
            return key
    return "not_mapped"


def _focus_reason(family: str, item: dict) -> str:
    if family == "readiness":
        return "Readiness blocker participates directly in RC cap."
    if "pressure" in family:
        return "Pressure blocker may represent recurring editorial instability."
    return item.get("suggested_human_action") or "Tier 1 blocker requires evidence-backed review."
