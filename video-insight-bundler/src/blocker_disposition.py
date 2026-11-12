"""Tier 1 blocker disposition and RC reassessment inputs."""

from __future__ import annotations

from collections import Counter

from intelligence_common import base_artifact, deterministic_id


ALLOWED_DISPOSITIONS = [
    "proposed",
    "confirmed_blocker",
    "externally_reviewed",
    "accepted_risk",
    "deferred",
    "resolved",
    "false_positive",
]

NON_BLOCKING_DISPOSITIONS = {"externally_reviewed", "accepted_risk", "resolved", "false_positive"}
UNRESOLVED_DISPOSITIONS = {"proposed", "confirmed_blocker", "deferred"}


def _decision_evidence(row: dict) -> list[str]:
    refs = row.get("decision_evidence_refs") or row.get("review_decision_evidence_refs") or []
    return sorted({ref for ref in refs if isinstance(ref, str) and ref})


def _is_valid_non_blocking(row: dict) -> bool:
    return row.get("disposition") in NON_BLOCKING_DISPOSITIONS and bool(_decision_evidence(row))


def disposition_is_unresolved(row: dict) -> bool:
    disposition = row.get("disposition") or row.get("default_disposition") or "proposed"
    return disposition in UNRESOLVED_DISPOSITIONS or (disposition in NON_BLOCKING_DISPOSITIONS and not _is_valid_non_blocking({**row, "disposition": disposition}))


def summarize_dispositions(tier_1_blocker_disposition: dict | None, blocker_analysis: dict | None = None) -> dict:
    rows = (tier_1_blocker_disposition or {}).get("blocker_dispositions") or []
    unresolved_rows = [row for row in rows if disposition_is_unresolved(row)]
    hard_rows = [row for row in (blocker_analysis or {}).get("blockers", []) if row.get("severity") == "high"]
    unresolved_hard_count = len(hard_rows)
    if rows and not unresolved_rows:
        unresolved_hard_count = 0
    return {
        "tier_1_blocker_count": len(rows),
        "unresolved_tier_1_blocker_count": len(unresolved_rows),
        "valid_non_blocking_tier_1_count": len(rows) - len(unresolved_rows),
        "hard_blocker_count": len(hard_rows),
        "unresolved_hard_blocker_count": unresolved_hard_count,
        "all_tier_1_dispositions_non_blocking": bool(rows) and not unresolved_rows,
    }


def build_blocker_disposition_system(compressed_review_queue: dict, blocker_analysis: dict, remediation_tracker: dict) -> dict:
    tier_1_items = [row for row in compressed_review_queue.get("compressed_items", []) if row.get("tier") == 1]
    hard_blockers = [row for row in blocker_analysis.get("blockers", []) if row.get("severity") == "high"]
    hard_by_video = {}
    for row in hard_blockers:
        for video in row.get("affected_videos") or ["__corpus__"]:
            hard_by_video.setdefault(video, []).append(row)

    dispositions = []
    for item in tier_1_items:
        affected_videos = sorted(set(item.get("affected_videos") or []))
        associated_hard = []
        for video in affected_videos or ["__corpus__"]:
            associated_hard.extend(hard_by_video.get(video, []))
        associated_hard = sorted({row["blocker_id"]: row for row in associated_hard if row.get("blocker_id")}.values(), key=lambda row: row["blocker_id"])
        blocker_id = deterministic_id("T1BLOCK", item.get("compressed_item_id"), item.get("issue_family"), affected_videos, item.get("original_item_refs"))
        dispositions.append(
            {
                "blocker_id": blocker_id,
                "source_compressed_item_id": item.get("compressed_item_id"),
                "blocker_family": item.get("issue_family") or "unknown",
                "affected_videos": affected_videos,
                "affected_segments": sorted(set(item.get("affected_segments") or [])),
                "evidence_refs": sorted(set(item.get("evidence_refs") or [])),
                "original_item_refs": sorted(set(item.get("original_item_refs") or [])),
                "why_it_blocks_rc": "Tier 1 compressed review queue item remains unresolved and participates in the RC hardening cap.",
                "minimum_human_decision_needed": "Choose an allowed disposition and attach decision evidence before treating this blocker as non-blocking.",
                "recommended_disposition": "externally_reviewed",
                "allowed_dispositions": ALLOWED_DISPOSITIONS,
                "default_disposition": "proposed",
                "disposition": "proposed",
                "decision_evidence_refs": [],
                "readiness_effect_if_resolved": "Can remove this specific Tier 1 hardening cap only after evidence-backed disposition validation.",
                "readiness_effect_if_deferred": "Keeps readiness capped at not_ready for this blocker.",
                "mutation_required": False,
                "human_review_required": True,
                "code_change_required": False,
                "editorial_change_required": False,
                "validation_required_after_decision": True,
                "associated_hard_blocker_ids": [row["blocker_id"] for row in associated_hard],
                "hard_blocker_refs": [
                    {
                        "blocker_id": row.get("blocker_id"),
                        "blocker_type": row.get("blocker_type"),
                        "blocker_label": row.get("blocker_label"),
                        "readiness_impact": row.get("readiness_impact"),
                        "evidence_refs": row.get("evidence_refs") or [],
                    }
                    for row in associated_hard
                ],
            }
        )

    disposition_counts = Counter(row["disposition"] for row in dispositions)
    unresolved = [row for row in dispositions if disposition_is_unresolved(row)]
    tier_1_disposition = base_artifact(method="deterministic_tier_1_blocker_disposition_v1")
    tier_1_disposition.update(
        {
            "tier_1_blocker_disposition_id": deterministic_id("T1DISPSET", [(row["source_compressed_item_id"], row["blocker_id"], row["disposition"]) for row in dispositions]),
            "source_compressed_review_queue_ref": "workbench/compressed_review_queue.json",
            "source_blocker_analysis_ref": "governance/blocker_analysis.json",
            "blocker_dispositions": dispositions,
            "summary": {
                "tier_1_blocker_count": len(dispositions),
                "unresolved_tier_1_blocker_count": len(unresolved),
                "resolved_or_non_blocking_count": len(dispositions) - len(unresolved),
                "default_disposition": "proposed",
                "disposition_counts": dict(sorted(disposition_counts.items())),
                "readiness_cap_lifted": False,
            },
        }
    )

    hard_plan_rows = []
    for row in hard_blockers:
        related = [
            item
            for item in dispositions
            if row.get("blocker_id") in (item.get("associated_hard_blocker_ids") or [])
            or set(row.get("affected_videos") or []) & set(item.get("affected_videos") or [])
            or row.get("blocker_label") == item.get("blocker_family")
        ]
        hard_plan_rows.append(
            {
                "hard_blocker_id": row.get("blocker_id"),
                "blocker_type": row.get("blocker_type"),
                "blocker_family": row.get("blocker_label"),
                "severity": row.get("severity"),
                "affected_videos": row.get("affected_videos") or [],
                "evidence_refs": row.get("evidence_refs") or [],
                "recommended_action": row.get("recommended_action"),
                "related_tier_1_blocker_ids": [item["blocker_id"] for item in related],
                "allowed_resolution_dispositions": ALLOWED_DISPOSITIONS,
                "current_resolution_status": "proposed",
                "minimum_evidence_required": "Decision log entry plus evidence reference for each non-blocking disposition.",
                "rerun_required_after_decision": True,
            }
        )
    hard_plan = base_artifact(method="deterministic_hard_blocker_resolution_plan_v1")
    hard_plan.update(
        {
            "hard_blocker_resolution_plan_id": deterministic_id("HBPLAN", [(row.get("hard_blocker_id"), row.get("blocker_family")) for row in hard_plan_rows]),
            "source_blocker_analysis_ref": "governance/blocker_analysis.json",
            "source_tier_1_disposition_ref": "governance/tier_1_blocker_disposition.json",
            "hard_blocker_resolution_items": hard_plan_rows,
            "summary": {
                "hard_blocker_count": len(hard_plan_rows),
                "unresolved_hard_blocker_count": len(hard_plan_rows),
                "resolution_ready_count": 0,
                "readiness_cap_lifted": False,
            },
        }
    )

    matrix_rows = []
    for item in dispositions:
        matrix_rows.append(
            {
                "blocker_id": item["blocker_id"],
                "source_compressed_item_id": item["source_compressed_item_id"],
                "blocker_family": item["blocker_family"],
                "current_disposition": item["disposition"],
                "decision_evidence_valid": False,
                "readiness_cap_status": "capped",
                "human_review_required": item["human_review_required"],
                "code_change_required": item["code_change_required"],
                "editorial_change_required": item["editorial_change_required"],
                "validation_required_after_decision": item["validation_required_after_decision"],
                "original_item_refs": item["original_item_refs"],
                "evidence_refs": item["evidence_refs"],
            }
        )
    matrix = base_artifact(method="deterministic_rc_blocker_review_matrix_v1")
    matrix.update(
        {
            "rc_blocker_review_matrix_id": deterministic_id("RCMATRIX", [(row["blocker_id"], row["current_disposition"]) for row in matrix_rows]),
            "review_rows": matrix_rows,
            "summary": {
                "review_row_count": len(matrix_rows),
                "capped_row_count": len(matrix_rows),
                "human_review_required_count": sum(1 for row in matrix_rows if row["human_review_required"]),
                "code_change_required_count": sum(1 for row in matrix_rows if row["code_change_required"]),
            },
        }
    )

    reassessment = _build_reassessment_inputs(tier_1_disposition, hard_plan, matrix, remediation_tracker)
    tracker = _build_blocker_disposition_tracker(tier_1_disposition)
    decision_template = _build_decision_log_template(tier_1_disposition)
    summary = _build_resolution_summary(tier_1_disposition, hard_plan)
    packet = _build_review_packet(tier_1_disposition, hard_plan, matrix)
    packet_summary = _build_review_packet_summary(packet)
    return {
        "tier_1_blocker_disposition": tier_1_disposition,
        "hard_blocker_resolution_plan": hard_plan,
        "rc_blocker_review_matrix": matrix,
        "rc_reassessment_inputs": reassessment,
        "blocker_disposition_tracker": tracker,
        "human_review_decision_log_template": decision_template,
        "blocker_resolution_summary": summary,
        "tier_1_review_packet": packet,
        "tier_1_review_packet_summary": packet_summary,
    }


def _build_reassessment_inputs(tier_1_disposition: dict, hard_plan: dict, matrix: dict, remediation_tracker: dict) -> dict:
    tier_summary = tier_1_disposition.get("summary") or {}
    hard_summary = hard_plan.get("summary") or {}
    output = base_artifact(method="deterministic_rc_reassessment_inputs_v1")
    output.update(
        {
            "rc_reassessment_inputs_id": deterministic_id("RCREASSESS", tier_summary, hard_summary),
            "source_tier_1_disposition_ref": "governance/tier_1_blocker_disposition.json",
            "source_hard_blocker_plan_ref": "governance/hard_blocker_resolution_plan.json",
            "source_review_matrix_ref": "governance/rc_blocker_review_matrix.json",
            "readiness_reassessment_policy": {
                "proposed_remediation_can_raise_readiness": False,
                "non_blocking_dispositions_require_evidence": True,
                "unresolved_tier_1_blockers_cap_readiness": True,
                "allowed_non_blocking_dispositions": sorted(NON_BLOCKING_DISPOSITIONS),
            },
            "reassessment_inputs": {
                "tier_1_blocker_count": tier_summary.get("tier_1_blocker_count", 0),
                "unresolved_tier_1_blocker_count": tier_summary.get("unresolved_tier_1_blocker_count", 0),
                "hard_blocker_count": hard_summary.get("hard_blocker_count", 0),
                "unresolved_hard_blocker_count": hard_summary.get("unresolved_hard_blocker_count", 0),
                "proposed_remediation_count": (remediation_tracker.get("summary") or {}).get("proposed_count", 0),
                "review_matrix_ref": "governance/rc_blocker_review_matrix.json",
            },
            "classification_floor": "not_ready",
            "classification_cap_reason": "Tier 1 and hard blocker dispositions are proposed only.",
            "summary": {
                "ready_for_rc_reassessment": False,
                "readiness_remains_capped": True,
                "proposed_remediation_counted_as_resolution": False,
            },
        }
    )
    return output


def _build_blocker_disposition_tracker(tier_1_disposition: dict) -> dict:
    rows = [
        {
            "tracker_id": deterministic_id("BDTRACK", row["blocker_id"], row["source_compressed_item_id"]),
            "blocker_id": row["blocker_id"],
            "source_compressed_item_id": row["source_compressed_item_id"],
            "current_disposition": row["disposition"],
            "decision_evidence_refs": row.get("decision_evidence_refs") or [],
            "status": "unresolved" if disposition_is_unresolved(row) else "non_blocking_with_evidence",
            "next_required_action": row["minimum_human_decision_needed"],
        }
        for row in tier_1_disposition.get("blocker_dispositions", [])
    ]
    output = base_artifact(method="deterministic_blocker_disposition_tracker_v1")
    output.update(
        {
            "blocker_disposition_tracker_id": deterministic_id("BDTRACKSET", [(row["blocker_id"], row["current_disposition"]) for row in rows]),
            "tracked_blockers": rows,
            "summary": {
                "tracked_blocker_count": len(rows),
                "unresolved_count": sum(1 for row in rows if row["status"] == "unresolved"),
                "human_review_required_count": len(rows),
            },
        }
    )
    return output


def _build_decision_log_template(tier_1_disposition: dict) -> dict:
    rows = [
        {
            "blocker_id": row["blocker_id"],
            "source_compressed_item_id": row["source_compressed_item_id"],
            "selected_disposition": "proposed",
            "decision_evidence_refs": [],
            "reviewer": "",
            "reviewed_at_utc": "",
            "decision_notes": "",
            "validation_rerun_required": True,
        }
        for row in tier_1_disposition.get("blocker_dispositions", [])
    ]
    output = base_artifact(method="deterministic_human_review_decision_log_template_v1")
    output.update(
        {
            "human_review_decision_log_template_id": deterministic_id("HRDLT", [row["blocker_id"] for row in rows]),
            "allowed_dispositions": ALLOWED_DISPOSITIONS,
            "decision_rows": rows,
            "summary": {"template_row_count": len(rows)},
        }
    )
    return output


def _build_resolution_summary(tier_1_disposition: dict, hard_plan: dict) -> dict:
    output = base_artifact(method="deterministic_blocker_resolution_summary_v1")
    output.update(
        {
            "blocker_resolution_summary_id": deterministic_id("BRSUM", tier_1_disposition.get("tier_1_blocker_disposition_id"), hard_plan.get("hard_blocker_resolution_plan_id")),
            "tier_1_summary": tier_1_disposition.get("summary") or {},
            "hard_blocker_summary": hard_plan.get("summary") or {},
            "readiness_position": "not_ready_cap_preserved",
            "summary": {
                "readiness_remains_capped": True,
                "resolved_count": 0,
                "unresolved_count": (tier_1_disposition.get("summary") or {}).get("unresolved_tier_1_blocker_count", 0),
            },
        }
    )
    return output


def _build_review_packet(tier_1_disposition: dict, hard_plan: dict, matrix: dict) -> dict:
    output = base_artifact(method="deterministic_tier_1_review_packet_v1")
    output.update(
        {
            "tier_1_review_packet_id": deterministic_id("T1PACKET", tier_1_disposition.get("tier_1_blocker_disposition_id"), hard_plan.get("hard_blocker_resolution_plan_id")),
            "tier_1_blocker_dispositions": tier_1_disposition.get("blocker_dispositions", []),
            "hard_blocker_resolution_items": hard_plan.get("hard_blocker_resolution_items", []),
            "review_matrix_ref": "governance/rc_blocker_review_matrix.json",
            "summary": {
                "tier_1_blocker_count": (tier_1_disposition.get("summary") or {}).get("tier_1_blocker_count", 0),
                "hard_blocker_count": (hard_plan.get("summary") or {}).get("hard_blocker_count", 0),
                "human_review_required": True,
            },
        }
    )
    return output


def _build_review_packet_summary(packet: dict) -> dict:
    rows = packet.get("tier_1_blocker_dispositions") or []
    output = base_artifact(method="deterministic_tier_1_review_packet_summary_v1")
    output.update(
        {
            "tier_1_review_packet_summary_id": deterministic_id("T1PACKSUM", packet.get("tier_1_review_packet_id")),
            "blocker_ids": [row.get("blocker_id") for row in rows],
            "compressed_item_refs": [row.get("source_compressed_item_id") for row in rows],
            "human_review_required_blockers": [row.get("blocker_id") for row in rows if row.get("human_review_required")],
            "code_change_required_blockers": [row.get("blocker_id") for row in rows if row.get("code_change_required")],
            "summary": {
                "tier_1_blocker_count": len(rows),
                "human_review_required_count": sum(1 for row in rows if row.get("human_review_required")),
                "code_change_required_count": sum(1 for row in rows if row.get("code_change_required")),
            },
        }
    )
    return output
