"""Deterministic compression for corpus review queues."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from intelligence_common import base_artifact, clamp, deterministic_id


TIER_LABELS = {
    1: "RC blockers",
    2: "High-impact corpus blockers",
    3: "Recurring pressure or archetype issues",
    4: "Per-video editorial improvements",
    5: "Informational or audit-only items",
}


def _video_key(item: dict) -> str:
    return item.get("source_video") or "corpus"


def _issue_family(item: dict) -> str:
    reason = (item.get("reason") or "").lower()
    artifact = item.get("artifact_path") or ""
    if "readiness" in reason or "release_readiness" in artifact:
        return "readiness"
    if "pressure" in reason or "editorial_pressure" in artifact:
        return "editorial_pressure"
    if "counterfactual" in reason:
        return "counterfactual_uncertainty"
    if "recommendation requires review" in reason:
        suffix = reason.split(":", 1)[-1].strip(" .")
        return suffix or "recommendation"
    return reason.strip(" .")[:80] or "review_item"


def _segment_refs(item: dict) -> list[str]:
    refs = []
    for ref in item.get("evidence_references") or []:
        if isinstance(ref, str) and ref:
            refs.append(ref.split("#")[-1] if "#" in ref else ref)
    return sorted(set(refs))


def _recurring_families(review_items: list[dict], archetypes: dict, intelligence: dict) -> set[str]:
    counts = Counter(_issue_family(item) for item in review_items)
    recurring = {family for family, count in counts.items() if count > 1}
    for row in (intelligence.get("recurring_recommendation_types") or []):
        if (row.get("count") or 0) > 1 and row.get("issue_type"):
            recurring.add(str(row["issue_type"]).lower())
    for row in (intelligence.get("recurring_pressure_patterns") or []):
        if (row.get("high_count") or 0) > 0:
            recurring.add("editorial_pressure")
    for row in (archetypes.get("dominant_archetypes") or []):
        if (row.get("count") or 0) > 1 and row.get("archetype"):
            recurring.add(str(row["archetype"]).lower())
    return recurring


def _tier_for(items: list[dict], family: str, recurring: set[str], arbitration: dict, rc_assessment: dict) -> int:
    max_priority = max((item.get("priority_score") or 0.0) for item in items) if items else 0.0
    failed_checks = [row for row in (rc_assessment.get("checklist") or []) if row.get("status") != "pass"]
    if family == "readiness" or (failed_checks and max_priority >= 0.45):
        return 1
    if max_priority >= 0.72 or arbitration.get("classification") == "not_ready":
        return 2
    if family in recurring or any(token in recurring for token in family.lower().split()):
        return 3
    if family not in {"counterfactual_uncertainty", "audit"}:
        return 4
    return 5


def build_review_queue_compression(review_queue: dict, priority_review_items: dict, corpus_intelligence: dict, editorial_archetypes: dict, readiness_arbitration: dict, rc_assessment: dict) -> dict:
    """Return compressed queue, tiers, clusters, and summary artifacts."""

    raw_items = list(review_queue.get("review_items") or [])
    priority_ids = {row.get("review_item_id") for row in (priority_review_items.get("review_items") or [])}
    recurring = _recurring_families(raw_items, editorial_archetypes, corpus_intelligence)

    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for item in raw_items:
        groups[(_video_key(item), _issue_family(item))].append(item)

    compressed_items = []
    for (video, family), items in sorted(groups.items(), key=lambda row: (row[0][1], row[0][0])):
        original_ids = sorted(item.get("review_item_id") for item in items if item.get("review_item_id"))
        priority_score = clamp(max((item.get("priority_score") or 0.0) for item in items) + min(len(items) - 1, 6) * 0.035)
        tier = _tier_for(items, family, recurring, readiness_arbitration, rc_assessment)
        evidence_refs = sorted(set(ref for item in items for ref in (item.get("evidence_references") or []) if ref))
        affected_segments = sorted(set(seg for item in items for seg in _segment_refs(item)))
        recurring_pattern = "recurring" if len(items) > 1 or family in recurring else "single_video"
        compressed_items.append(
            {
                "compressed_item_id": deterministic_id("CREV", video, family, original_ids),
                "tier": tier,
                "tier_label": TIER_LABELS[tier],
                "priority_score": priority_score,
                "affected_videos": [video],
                "affected_segments": affected_segments,
                "issue_family": family,
                "recurring_pattern": recurring_pattern,
                "evidence_refs": evidence_refs,
                "original_item_refs": original_ids,
                "priority_review_refs": sorted(item_id for item_id in original_ids if item_id in priority_ids),
                "suggested_human_action": _suggest_action(family, tier),
                "expected_readiness_effect": _expected_effect(family, tier),
                "non_mutating_status": "review_only_no_media_or_timeline_mutation",
            }
        )

    compressed_items = sorted(compressed_items, key=lambda row: (row["tier"], -row["priority_score"], row["issue_family"], row["compressed_item_id"]))
    tier_rows = []
    for tier, label in TIER_LABELS.items():
        tier_items = [row for row in compressed_items if row["tier"] == tier]
        tier_rows.append(
            {
                "tier": tier,
                "tier_label": label,
                "item_count": len(tier_items),
                "compressed_item_refs": [row["compressed_item_id"] for row in tier_items],
                "highest_priority_score": max((row["priority_score"] for row in tier_items), default=0.0),
            }
        )
    cluster_rows = []
    for family, items in sorted(_by_family(compressed_items).items()):
        cluster_rows.append(
            {
                "cluster_id": deterministic_id("RCLUSTER", family, [row["compressed_item_id"] for row in items]),
                "issue_family": family,
                "compressed_item_refs": [row["compressed_item_id"] for row in items],
                "affected_videos": sorted(set(video for row in items for video in row["affected_videos"])),
                "original_item_count": sum(len(row["original_item_refs"]) for row in items),
                "recurring_pattern": "recurring" if len(items) > 1 else items[0].get("recurring_pattern"),
            }
        )

    summary = {
        "analysis_status": "complete",
        "method": "deterministic_review_queue_compression_summary_v1",
        "review_queue_compression_summary_id": deterministic_id("RQSUM", len(raw_items), [row["compressed_item_id"] for row in compressed_items]),
        "raw_review_item_count": len(raw_items),
        "compressed_review_item_count": len(compressed_items),
        "compression_ratio": round(len(compressed_items) / max(len(raw_items), 1), 3),
        "tier_1_blocker_count": sum(1 for row in compressed_items if row["tier"] == 1),
        "traceability_status": "all_original_items_preserved" if _all_originals_preserved(raw_items, compressed_items) else "missing_original_item_reference",
        "limitations": ["Compressed review queues are deterministic review-planning artifacts and do not delete or mutate the raw review queue."],
    }
    compressed = base_artifact(method="deterministic_compressed_review_queue_v1")
    compressed.update(
        {
            "compressed_review_queue_id": deterministic_id("CQUEUE", review_queue.get("review_queue_id"), [row["compressed_item_id"] for row in compressed_items]),
            "source_review_queue_ref": "workbench/review_queue.json",
            "compressed_items": compressed_items,
            "summary": summary,
        }
    )
    tiers = base_artifact(method="deterministic_review_queue_tiers_v1")
    tiers.update({"review_queue_tiers_id": deterministic_id("RQTIER", [row["compressed_item_refs"] for row in tier_rows]), "tiers": tier_rows, "summary": {"tier_count": len(tier_rows)}})
    clusters = base_artifact(method="deterministic_review_queue_clusters_v1")
    clusters.update({"review_queue_clusters_id": deterministic_id("RQCLUSTERS", [row["cluster_id"] for row in cluster_rows]), "clusters": cluster_rows, "summary": {"cluster_count": len(cluster_rows)}})
    summary_artifact = base_artifact(method="deterministic_review_queue_compression_summary_v1")
    summary_artifact.update(summary)
    return {
        "compressed_review_queue": compressed,
        "review_queue_tiers": tiers,
        "review_queue_clusters": clusters,
        "review_queue_summary": summary_artifact,
    }


def _by_family(items: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        grouped[item["issue_family"]].append(item)
    return grouped


def _all_originals_preserved(raw_items: list[dict], compressed_items: list[dict]) -> bool:
    raw_ids = sorted(item.get("review_item_id") for item in raw_items if item.get("review_item_id"))
    mapped = sorted(ref for item in compressed_items for ref in item.get("original_item_refs", []))
    return raw_ids == mapped


def _suggest_action(family: str, tier: int) -> str:
    if family == "readiness":
        return "Review release readiness evidence and identify the smallest human-reviewed clarification set before any edit planning."
    if "pressure" in family:
        return "Inspect pressure segments together and decide whether bridge, pacing release, or callback clarification is warranted."
    if "continuity" in family:
        return "Review affected transitions for explicit connective tissue and unresolved topic shifts."
    if tier == 5:
        return "Keep for audit context unless it recurs in a blocker tier."
    return "Review grouped evidence, choose whether the issue is intentional, and document the decision externally."


def _expected_effect(family: str, tier: int) -> str:
    if tier == 1:
        return "May remove an RC blocker if evidence is resolved and validated."
    if tier == 2:
        return "Likely improves corpus readiness confidence if recurring evidence weakens."
    if "pressure" in family:
        return "May reduce recurring pressure and improve comparative stabilization."
    return "May reduce human-review noise and clarify editorial intent."

