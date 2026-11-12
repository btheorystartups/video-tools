"""Recommendation traceability and source evidence maps."""

from __future__ import annotations

from intelligence_common import base_artifact, num
from stability import deterministic_id
from temporal_evidence_index import LIMITATION


def build_recommendation_traceability(outputs: dict, temporal_index: dict) -> dict:
    entries = []
    by_video_segment = {}
    for entry in temporal_index.get("temporal_evidence_entries") or []:
        by_video_segment[(entry.get("source_video"), entry.get("segment_id"))] = entry
    effort_by_rank = {row.get("source_review_item_id"): row for row in (outputs.get("optimization_effort_estimates") or {}).get("effort_estimates") or []}
    for ranked in (outputs.get("recommendation_ranking") or {}).get("ranked_recommendations") or []:
        source_video = ranked.get("source_video")
        matched = [entry for (video, _), entry in by_video_segment.items() if video == source_video and ranked.get("recommendation_family") in " ".join(entry.get("recommendations") or [])]
        if not matched:
            matched = [entry for (video, _), entry in by_video_segment.items() if video == source_video][:2]
        rec_id = deterministic_id("RECTRC", ranked.get("source_review_item_id"), ranked.get("recommendation_rank_id"))
        effort = effort_by_rank.get(ranked.get("source_review_item_id"), {})
        entries.append(
            {
                "recommendation_id": rec_id,
                "source_review_item_id": ranked.get("source_review_item_id"),
                "title": ranked.get("recommendation_family") or "Timeline review recommendation",
                "affected_videos": sorted({entry.get("source_video") for entry in matched if entry.get("source_video")}),
                "affected_segments": [
                    {"video_id": entry.get("video_id"), "source_video": entry.get("source_video"), "segment_id": entry.get("segment_id"), "start_time": entry.get("timestamp_start"), "end_time": entry.get("timestamp_end")}
                    for entry in matched
                ],
                "source_metrics": sorted({signal.get("signal") for entry in matched for signal in (entry.get("strongest_signals") or []) if num(signal.get("score")) >= 0.45}),
                "triggering_thresholds": ["high>=0.75", "medium>=0.45"],
                "contributing_artifacts": sorted({ref for entry in matched for ref in (entry.get("evidence_refs") or [])}),
                "contributing_graphs": sorted({graph for entry in matched for graph in (entry.get("relevant_graphs") or [])}),
                "related_metric_cards": [],
                "related_timeline_overlays": [],
                "evidence_refs": ranked.get("evidence_refs") or sorted({ref for entry in matched for ref in (entry.get("evidence_refs") or [])}),
                "confidence": ranked.get("evidence_confidence"),
                "severity": ranked.get("severity"),
                "priority_score": ranked.get("priority_score"),
                "effort_estimate": ranked.get("effort_estimate"),
                "expected_benefit": ranked.get("likely_benefit"),
                "risk_of_overcorrection": ranked.get("risk_of_overcorrection"),
                "preserve_as_intentional_option": ranked.get("preserve_as_intentional_option"),
                "human_review_required": True,
                "mutation_required": False,
                "recommended_next_action": ranked.get("recommended_review_action"),
                "why_generated": "Generated from deterministic review queue priority, recurrence, governance tier, and linked segment evidence.",
                "what_evidence_supports_it": "See evidence refs, source metrics, affected segments, and timeline overlays.",
                "what_human_should_review": "Review the source segment in context before changing pacing, visual reset, rhetoric, or structure.",
                "lowest_risk_optimization_path": "Start with analysis-only review notes and preserve intentional patterns unless evidence remains strong after human review.",
                "what_should_not_be_inferred": "Do not infer identity, actual emotion, viewer behavior, personality, or causal production outcomes.",
                "non_claim_limitation": LIMITATION,
            }
        )
    output = base_artifact(method="deterministic_recommendation_traceability_v1")
    output.update({"recommendation_traceability_id": deterministic_id("RECTRCREG", [row["recommendation_id"] for row in entries]), "traceability_entries": entries, "summary": {"traceability_entry_count": len(entries)}, "limitations": [LIMITATION]})
    return output


def build_recommendation_evidence_map(traceability: dict) -> dict:
    rows = []
    for entry in traceability.get("traceability_entries") or []:
        rows.append({"recommendation_id": entry.get("recommendation_id"), "evidence_refs": entry.get("evidence_refs") or [], "affected_segments": entry.get("affected_segments") or [], "source_metrics": entry.get("source_metrics") or []})
    output = base_artifact(method="deterministic_recommendation_evidence_map_v1")
    output.update({"recommendation_evidence_map_id": deterministic_id("RECMAP", rows), "evidence_map": rows, "summary": {"evidence_map_count": len(rows)}, "limitations": [LIMITATION]})
    return output


def build_recommendation_source_segments(traceability: dict) -> dict:
    rows = [{"recommendation_id": entry.get("recommendation_id"), "source_segments": entry.get("affected_segments") or []} for entry in traceability.get("traceability_entries") or []]
    output = base_artifact(method="deterministic_recommendation_source_segments_v1")
    output.update({"recommendation_source_segments_id": deterministic_id("RECSSEG", rows), "source_segments": rows, "summary": {"source_segment_link_count": sum(len(row["source_segments"]) for row in rows)}, "limitations": [LIMITATION]})
    return output


def build_recommendation_optimization_paths(traceability: dict) -> dict:
    rows = [{"recommendation_id": entry.get("recommendation_id"), "lowest_risk_path": entry.get("lowest_risk_optimization_path"), "mutation_required": False, "human_review_required": True, "preserve_as_intentional_option": entry.get("preserve_as_intentional_option")} for entry in traceability.get("traceability_entries") or []]
    output = base_artifact(method="deterministic_recommendation_optimization_paths_v1")
    output.update({"recommendation_optimization_paths_id": deterministic_id("RECOPTP", rows), "optimization_paths": rows, "summary": {"optimization_path_count": len(rows)}, "limitations": [LIMITATION]})
    return output

