"""Recurring readiness and review blocker analysis."""

from __future__ import annotations

from collections import Counter

from intelligence_common import base_artifact, clamp, deterministic_id


def build_blocker_analysis(corpus_intelligence: dict, editorial_archetypes: dict, compressed_review_queue: dict, governance_diagnostics: dict, validation_replay: dict, provenance: dict) -> dict:
    blockers = []

    def add(blocker_type: str, label: str, affected_videos: list[str], affected_artifacts: list[str], severity: str, recurrence_count: int, impact: str, evidence_refs: list[str], action: str) -> None:
        blockers.append(
            {
                "blocker_id": deterministic_id("BLOCK", blocker_type, label, affected_videos, affected_artifacts, recurrence_count),
                "blocker_type": blocker_type,
                "blocker_label": label,
                "affected_videos": sorted(set(affected_videos)),
                "affected_artifacts": sorted(set(affected_artifacts)),
                "severity": severity,
                "recurrence_count": recurrence_count,
                "readiness_impact": impact,
                "evidence_refs": sorted(set(evidence_refs)),
                "recommended_action": action,
            }
        )

    for row in (compressed_review_queue.get("compressed_items") or []):
        if row.get("tier") <= 2:
            add(
                "review_queue_blocker",
                row.get("issue_family") or "review_queue",
                row.get("affected_videos") or [],
                ["workbench/compressed_review_queue.json"],
                "high" if row.get("tier") == 1 else "medium",
                len(row.get("original_item_refs") or []),
                row.get("expected_readiness_effect") or "Readiness impact requires review.",
                row.get("evidence_refs") or [],
                row.get("suggested_human_action") or "Review compressed queue item.",
            )

    for row in (corpus_intelligence.get("recurring_pressure_patterns") or []):
        if (row.get("high_count") or 0) > 0:
            add("pressure_blocker", row.get("pattern") or "pressure", [], ["corpus/corpus_intelligence.json"], "medium", row.get("high_count") or 1, "Recurring pressure can suppress corpus readiness.", ["corpus/corpus_intelligence.json"], "Review high-pressure segments across videos before planning edits.")

    for row in (editorial_archetypes.get("dominant_archetypes") or []):
        if (row.get("count") or 0) > 1:
            add("archetype_blocker", row.get("archetype") or "archetype", [], ["corpus/editorial_archetypes.json"], "medium", row.get("count") or 1, "Recurring archetype may require consistent human decision policy.", ["corpus/editorial_archetypes.json"], "Review archetype remediation guidance and decide whether pattern is intentional.")

    for row in (governance_diagnostics.get("failed_thresholds") or []):
        add("governance_threshold_blocker", row.get("threshold_id") or "threshold", [], row.get("evidence_refs") or ["governance/governance_diagnostics.json"], "high" if row.get("blocking_status") == "blocking" else "medium", 1, "Failed governance threshold blocks RC promotion.", row.get("evidence_refs") or [], row.get("suggested_remediation") or "Resolve failed governance threshold.")

    validation_errors = (validation_replay.get("summary") or {}).get("missing_or_error_count") or 0
    if validation_errors:
        add("validation_blocker", "validation_errors", [], ["audit/validation_replay.json"], "high", validation_errors, "Validation errors block conservative promotion.", ["audit/validation_replay.json"], "Fix missing or errored validation evidence and rerun.")

    if ((provenance.get("summary") or {}).get("provenance_coverage_score") or 0.0) < 0.85:
        add("provenance_blocker", "low_provenance_coverage", [], ["audit/provenance_reconstruction.json"], "high", 1, "Low provenance coverage blocks auditability.", ["audit/provenance_reconstruction.json"], "Restore evidence links for readiness and recommendation decisions.")

    blockers = sorted(blockers, key=lambda row: ({"high": 0, "medium": 1, "low": 2}.get(row["severity"], 3), row["blocker_type"], row["blocker_label"]))
    output = base_artifact(method="deterministic_blocker_analysis_v1")
    output.update(
        {
            "blocker_analysis_id": deterministic_id("BLOCKSET", [(row["blocker_type"], row["blocker_label"], row["severity"], row["recurrence_count"]) for row in blockers]),
            "blockers": blockers,
            "summary": {
                "blocker_count": len(blockers),
                "hard_blocker_count": sum(1 for row in blockers if row["severity"] == "high"),
                "pressure_blocker_count": sum(1 for row in blockers if row["blocker_type"] == "pressure_blocker"),
                "archetype_blocker_count": sum(1 for row in blockers if row["blocker_type"] == "archetype_blocker"),
            },
        }
    )
    return output

