"""Plan concise next-best human review actions."""

from __future__ import annotations

from intelligence_common import base_artifact, deterministic_id


def build_next_best_human_actions(compressed_review_queue: dict, blocker_analysis: dict, remediation_tracker: dict, archetype_remediation: dict, rc_threshold_analysis: dict) -> dict:
    compressed = compressed_review_queue.get("compressed_items") or []
    blockers = blocker_analysis.get("blockers") or []
    remediations = remediation_tracker.get("remediations") or []
    archetypes = archetype_remediation.get("archetype_remediations") or []
    failed = rc_threshold_analysis.get("failed_checks") or []

    corpus_actions = _actions_from_blockers(blockers)[:5]
    video_actions = _actions_from_compressed([row for row in compressed if row.get("affected_videos")])[:5]
    low_effort = _low_effort_actions(remediations)[:5]
    not_recommended = _not_recommended_actions(rc_threshold_analysis, failed)[:5]
    suggested_order = [row["action_id"] for row in corpus_actions + video_actions + low_effort][:12]

    output = base_artifact(method="deterministic_next_best_human_actions_v1")
    output.update(
        {
            "next_best_human_actions_id": deterministic_id("NBA", [row.get("action_id") for row in corpus_actions + video_actions + low_effort + not_recommended]),
            "top_5_corpus_actions": corpus_actions,
            "top_5_video_specific_actions": video_actions,
            "top_5_low_effort_high_impact_actions": low_effort,
            "top_5_actions_not_recommended_yet": not_recommended,
            "suggested_review_order": suggested_order,
            "rationale": "Prioritize hard governance blockers, then compressed high-impact video issues, then low-effort proposed reviews. Do not treat proposed remediation as completed readiness work.",
            "evidence_refs": sorted(set(ref for row in corpus_actions + video_actions + low_effort for ref in (row.get("evidence_refs") or []))),
            "summary": {
                "corpus_action_count": len(corpus_actions),
                "video_action_count": len(video_actions),
                "low_effort_action_count": len(low_effort),
                "not_recommended_count": len(not_recommended),
                "archetype_guidance_count": len(archetypes),
            },
        }
    )
    return output


def _actions_from_blockers(blockers: list[dict]) -> list[dict]:
    rows = []
    for blocker in blockers:
        rows.append(
            {
                "action_id": deterministic_id("HACT", "blocker", blocker.get("blocker_id")),
                "source_ref": blocker.get("blocker_id"),
                "action": blocker.get("recommended_action"),
                "rationale": blocker.get("readiness_impact"),
                "affected_videos": blocker.get("affected_videos") or [],
                "evidence_refs": blocker.get("evidence_refs") or [],
                "priority": "high" if blocker.get("severity") == "high" else "medium",
            }
        )
    return rows


def _actions_from_compressed(items: list[dict]) -> list[dict]:
    rows = []
    for item in sorted(items, key=lambda row: (row.get("tier") or 9, -(row.get("priority_score") or 0.0))):
        rows.append(
            {
                "action_id": deterministic_id("HACT", "compressed", item.get("compressed_item_id")),
                "source_ref": item.get("compressed_item_id"),
                "action": item.get("suggested_human_action"),
                "rationale": item.get("expected_readiness_effect"),
                "affected_videos": item.get("affected_videos") or [],
                "affected_segments": item.get("affected_segments") or [],
                "evidence_refs": item.get("evidence_refs") or [],
                "priority": f"tier_{item.get('tier')}",
            }
        )
    return rows


def _low_effort_actions(remediations: list[dict]) -> list[dict]:
    rows = []
    for item in [row for row in remediations if row.get("risk") == "low"]:
        rows.append(
            {
                "action_id": deterministic_id("HACT", "low_effort", item.get("remediation_id")),
                "source_ref": item.get("remediation_id"),
                "action": item.get("suggested_action"),
                "rationale": item.get("expected_effect"),
                "affected_videos": item.get("affected_videos") or [],
                "affected_segments": item.get("affected_segments") or [],
                "evidence_refs": item.get("evidence_refs") or [],
                "priority": "low_effort_high_impact",
            }
        )
    return rows


def _not_recommended_actions(rc_threshold_analysis: dict, failed_checks: list[dict]) -> list[dict]:
    rows = []
    for shortcut in rc_threshold_analysis.get("not_recommended_shortcuts") or []:
        rows.append(
            {
                "action_id": deterministic_id("HACTNO", shortcut),
                "action": shortcut,
                "rationale": "Would bypass conservative governance evidence or confuse proposed remediation with completed work.",
                "evidence_refs": ["governance/rc_threshold_analysis.json"],
                "priority": "do_not_do_yet",
            }
        )
    for check in failed_checks:
        rows.append(
            {
                "action_id": deterministic_id("HACTNO", check.get("check_id")),
                "action": f"Promote while RC check still fails: {check.get('check')}",
                "rationale": "Promotion should wait for the failed check to pass or be explicitly explained by governance.",
                "evidence_refs": ["governance/rc_assessment.json"],
                "priority": "do_not_do_yet",
            }
        )
    return rows

