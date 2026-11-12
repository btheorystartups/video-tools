"""Non-mutating remediation tracking for human review."""

from __future__ import annotations

from intelligence_common import base_artifact, deterministic_id


def build_remediation_tracking(blocker_analysis: dict, compressed_review_queue: dict) -> dict:
    remediations = []

    def add(source_id: str, videos: list[str], segments: list[str], action_type: str, action: str, refs: list[str], effect: str, risk: str = "low", dependencies: list[str] | None = None) -> None:
        remediations.append(
            {
                "remediation_id": deterministic_id("REMED", source_id, action_type, videos, segments, action),
                "source_issue_id": source_id,
                "affected_videos": sorted(set(videos)),
                "affected_segments": sorted(set(segments)),
                "action_type": action_type,
                "suggested_action": action,
                "evidence_refs": sorted(set(refs)),
                "expected_effect": effect,
                "dependency_on_other_actions": dependencies or [],
                "risk": risk,
                "mutation_required": False,
                "human_review_required": True,
                "status": "proposed",
            }
        )

    for row in (compressed_review_queue.get("compressed_items") or []):
        if row.get("tier") <= 4:
            add(
                row.get("compressed_item_id"),
                row.get("affected_videos") or [],
                row.get("affected_segments") or [],
                _action_type(row.get("issue_family") or ""),
                row.get("suggested_human_action") or "Review grouped evidence.",
                row.get("evidence_refs") or [],
                row.get("expected_readiness_effect") or "Clarifies readiness evidence.",
                "medium" if row.get("tier") <= 2 else "low",
            )

    for row in (blocker_analysis.get("blockers") or []):
        add(
            row.get("blocker_id"),
            row.get("affected_videos") or [],
            [],
            "blocker_review",
            row.get("recommended_action") or "Review blocker evidence.",
            row.get("evidence_refs") or [],
            row.get("readiness_impact") or "May reduce blocker count.",
            "medium" if row.get("severity") == "high" else "low",
        )

    remediations = _dedupe(remediations)
    recurring_pressure = [row for row in remediations if row["action_type"] == "pressure_review"]
    readiness_blockers = [row for row in remediations if row["action_type"] in {"readiness_review", "blocker_review"}]

    tracker = base_artifact(method="deterministic_remediation_tracker_v1")
    tracker.update(
        {
            "remediation_tracker_id": deterministic_id("REMEDSET", [row["remediation_id"] for row in remediations]),
            "remediations": remediations,
            "summary": {
                "remediation_count": len(remediations),
                "proposed_count": sum(1 for row in remediations if row["status"] == "proposed"),
                "mutation_required_count": sum(1 for row in remediations if row["mutation_required"]),
                "human_review_required_count": sum(1 for row in remediations if row["human_review_required"]),
            },
        }
    )
    pressure = base_artifact(method="deterministic_recurring_pressure_remediation_v1")
    pressure.update({"recurring_pressure_remediation_id": deterministic_id("RPREMED", [row["remediation_id"] for row in recurring_pressure]), "remediations": recurring_pressure, "summary": {"remediation_count": len(recurring_pressure)}})
    readiness = base_artifact(method="deterministic_readiness_blocker_remediation_v1")
    readiness.update({"readiness_blocker_remediation_id": deterministic_id("RBREMED", [row["remediation_id"] for row in readiness_blockers]), "remediations": readiness_blockers, "summary": {"remediation_count": len(readiness_blockers)}})
    summary = base_artifact(method="deterministic_remediation_summary_v1")
    summary.update(
        {
            "remediation_summary_id": deterministic_id("REMEDSUM", tracker["remediation_tracker_id"]),
            "remediation_count": len(remediations),
            "status_counts": {"proposed": len(remediations), "reviewed_external": 0, "deferred": 0, "rejected": 0},
            "non_mutation_policy": "Remediation items are proposed human-review actions only. They do not apply edits, mutate media, or change timelines.",
            "summary": tracker["summary"],
        }
    )
    return {
        "remediation_tracker": tracker,
        "recurring_pressure_remediation": pressure,
        "readiness_blocker_remediation": readiness,
        "remediation_summary": summary,
    }


def _action_type(family: str) -> str:
    if "pressure" in family:
        return "pressure_review"
    if "readiness" in family:
        return "readiness_review"
    if "continuity" in family:
        return "continuity_review"
    if "archetype" in family:
        return "archetype_review"
    return "editorial_review"


def _dedupe(rows: list[dict]) -> list[dict]:
    seen = set()
    output = []
    for row in sorted(rows, key=lambda item: (item["risk"], item["source_issue_id"], item["remediation_id"])):
        key = (row["source_issue_id"], row["action_type"], tuple(row["affected_videos"]), tuple(row["affected_segments"]))
        if key in seen:
            continue
        seen.add(key)
        output.append(row)
    return sorted(output, key=lambda item: ({"medium": 0, "low": 1, "high": 0}.get(item["risk"], 2), item["action_type"], item["remediation_id"]))

