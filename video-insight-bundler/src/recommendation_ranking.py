"""Rank deterministic recommendations by review priority and optimization value."""

from __future__ import annotations

from collections import Counter

from intelligence_common import base_artifact, num
from stability import deterministic_id


def _effort_from_reason(reason: str, severity: str) -> str:
    text = f"{reason} {severity}".lower()
    if "rewrite" in text or "unresolved_argument" in text:
        return "structural rewrite candidate"
    if "re-record" in text or "record" in text:
        return "re-record candidate"
    if "visual" in text or "transition" in text:
        return "moderate effort"
    if severity == "high":
        return "moderate effort"
    if severity == "medium":
        return "low effort"
    return "trivial adjustment"


def build_recommendation_ranking(outputs: dict) -> dict:
    review_items = (outputs.get("review_queue") or {}).get("review_items") or []
    compressed = (outputs.get("compressed_review_queue") or {}).get("compressed_items") or []
    compressed_by_raw = {}
    for item in compressed:
        for ref in item.get("original_item_refs") or []:
            compressed_by_raw[ref] = item
    family_counts = Counter((item.get("reason") or "review").split(":")[0] for item in review_items)
    rows = []
    for index, item in enumerate(review_items):
        reason = item.get("reason") or "Review item"
        compressed_item = compressed_by_raw.get(item.get("review_item_id"), {})
        tier = compressed_item.get("tier") or 5
        recurrence = family_counts[(reason or "review").split(":")[0]]
        confidence = num(item.get("confidence"), 0.65)
        base = num(item.get("priority_score"), 0.0)
        governance_boost = max(0, 6 - int(tier)) * 0.08
        recurrence_boost = min(recurrence, 6) * 0.025
        priority = round(min(1.0, base * 0.72 + governance_boost + recurrence_boost + confidence * 0.08), 3)
        severity = "high" if priority >= 0.75 else "medium" if priority >= 0.45 else "low"
        rows.append(
            {
                "recommendation_rank_id": deterministic_id("RRANK", item.get("review_item_id"), priority, index),
                "rank": 0,
                "source_review_item_id": item.get("review_item_id"),
                "source_compressed_item_id": compressed_item.get("compressed_item_id"),
                "source_video": item.get("source_video"),
                "recommendation_family": (reason or "review").split(":")[0][:96],
                "priority_score": priority,
                "severity": severity,
                "effort_estimate": _effort_from_reason(reason, severity),
                "likely_benefit": "higher" if priority >= 0.75 else "moderate" if priority >= 0.45 else "limited",
                "evidence_confidence": round(confidence, 3),
                "governance_severity": "tier_1" if tier == 1 else "tier_2_plus" if tier <= 2 else "review",
                "recurrence": recurrence,
                "risk_of_overcorrection": "Changing this without context can flatten intentional style or remove useful tension.",
                "preserve_as_intentional_option": "Preserve when the evidence is reviewed and the pattern supports the intended style.",
                "recommended_review_action": item.get("suggested_human_action") or "Review linked evidence before making production or edit changes.",
                "evidence_refs": item.get("evidence_references") or item.get("evidence_refs") or [],
                "mutation_required": False,
            }
        )
    rows = sorted(rows, key=lambda row: (-row["priority_score"], row.get("source_review_item_id") or ""))
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
    output = base_artifact(method="deterministic_recommendation_ranking_v1")
    output.update(
        {
            "recommendation_ranking_id": deterministic_id("RREC", [(row["source_review_item_id"], row["priority_score"]) for row in rows]),
            "ranked_recommendations": rows,
            "summary": {"ranked_recommendation_count": len(rows), "high_priority_count": sum(1 for row in rows if row["severity"] == "high")},
        }
    )
    return output
