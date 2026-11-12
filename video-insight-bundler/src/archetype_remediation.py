"""Map recurring editorial archetypes to non-mutating review guidance."""

from __future__ import annotations

from collections import defaultdict

from intelligence_common import base_artifact, deterministic_id


GUIDANCE = {
    "high_pressure_abstract_argument": {
        "risk": "Abstract claims may accumulate pressure without enough concrete support.",
        "action": "Review whether concrete examples, scoped claims, or bridge language would clarify the argument.",
        "avoid": "Do not flatten intentional abstraction or add unsupported examples.",
    },
    "compressed_rhetorical_escalation": {
        "risk": "Dense escalation can reduce pacing release and make transitions feel abrupt.",
        "action": "Review pacing release points and bridge transitions around escalation clusters.",
        "avoid": "Do not slow every fast section; preserve intentional momentum.",
    },
    "low_visual_reset_discourse_flow": {
        "risk": "Sustained visual flow with discourse pressure may need a reset or clearer chaptering.",
        "action": "Review whether a visual reset or chapter boundary would help comprehension.",
        "avoid": "Do not add visual resets where continuity is the editorial point.",
    },
    "visually_static_philosophical_riff": {
        "risk": "Static visuals can be intentional, but may weaken retention for long abstract passages.",
        "action": "Preserve if intentional; consider visual chaptering only if retention matters.",
        "avoid": "Do not treat visual stillness as a defect by default.",
    },
    "high_contradiction_pressure_sequence": {
        "risk": "Contradiction clusters under pressure can blur scope or claim boundaries.",
        "action": "Review contradiction clusters and clarify scope, definitions, or sequencing.",
        "avoid": "Do not remove productive tension without checking argument intent.",
    },
}


def build_archetype_remediation(editorial_archetypes: dict) -> dict:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in editorial_archetypes.get("archetype_matches") or []:
        grouped[row.get("archetype") or "unknown_archetype"].append(row)

    remediations = []
    for archetype, rows in sorted(grouped.items()):
        guide = GUIDANCE.get(archetype, {
            "risk": "Recurring editorial archetype may need a consistent review decision.",
            "action": "Review representative examples and decide whether the pattern is intentional.",
            "avoid": "Do not apply a uniform edit without segment-level evidence.",
        })
        evidence_refs = sorted(set(f"corpus/editorial_archetypes.json#{row.get('archetype_match_id')}" for row in rows if row.get("archetype_match_id")))
        videos = sorted(set(row.get("source_video") for row in rows if row.get("source_video")))
        remediations.append(
            {
                "archetype_id": deterministic_id("AREMED", archetype, videos, len(rows)),
                "archetype_label": archetype,
                "affected_videos": videos,
                "recurring_evidence": [{"archetype_match_id": row.get("archetype_match_id"), "match_score": row.get("match_score"), "source_video": row.get("source_video")} for row in rows],
                "likely_editorial_risk": guide["risk"],
                "suggested_review_action": guide["action"],
                "what_not_to_do": guide["avoid"],
                "mutation_safety": "review_only_no_media_or_timeline_mutation",
                "evidence_refs": evidence_refs,
            }
        )

    output = base_artifact(method="deterministic_archetype_remediation_v1")
    output.update(
        {
            "archetype_remediation_id": deterministic_id("AREMEDSET", [row["archetype_id"] for row in remediations]),
            "archetype_remediations": remediations,
            "summary": {
                "archetype_remediation_count": len(remediations),
                "recurring_archetype_count": sum(1 for row in remediations if len(row.get("affected_videos") or []) > 1),
            },
        }
    )
    return output

