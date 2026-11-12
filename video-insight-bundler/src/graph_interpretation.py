"""Deterministic graph interpretation index for expert dashboard pages."""

from __future__ import annotations

from intelligence_common import base_artifact
from stability import deterministic_id


DETAIL_SPECS = [
    ("acoustic_energy", "Acoustic Energy", "acoustic", "corpus_pressure_heatmap.png", "acoustic_energy_detail.html", "acoustic_energy_variability"),
    ("speech_pacing", "Speech Pacing", "speech_pacing", "pacing_fingerprint_map.png", "speech_pacing_detail.html", "speech_rate_wpm"),
    ("silence_ratio", "Silence Ratio", "speech_pacing", "pacing_fingerprint_map.png", "silence_ratio_detail.html", "silence_ratio"),
    ("segment_timeline", "Segment Timeline", "segment_timeline", "review_priority_matrix.png", "segment_timeline_detail.html", "segment_duration"),
    ("topic_continuity", "Topic Continuity", "discourse", "discourse_signature_map.png", "topic_continuity_detail.html", "topic_drift"),
    ("rhetorical_flow", "Rhetorical Flow", "rhetorical", "rhetorical_signature_map.png", "rhetorical_flow_detail.html", "rhetorical_pressure"),
    ("claim_example_balance", "Claim/Example Balance", "rhetorical", "recommendation_convergence_graph.png", "claim_example_balance_detail.html", "claim_density"),
    ("abstract_concrete", "Abstract/Concrete Balance", "rhetorical", "recommendation_convergence_graph.png", "abstract_concrete_detail.html", "abstract_concrete_balance"),
    ("emotional_arc", "Heuristic Tonal Arc", "tonal_arc", "corpus_pressure_heatmap.png", "emotional_arc_detail.html", "acoustic_energy_variability"),
    ("persona_style", "Persona/Style", "style", "corpus_style_fingerprint_map.png", "persona_style_detail.html", "evidence_consensus_strength"),
    ("visual_structure", "Visual Structure", "visual", "corpus_style_fingerprint_map.png", "visual_structure_detail.html", "visual_reset_frequency"),
    ("shot_boundaries", "Shot Boundaries", "visual", "comparative_continuity_matrix.png", "shot_boundaries_detail.html", "shot_boundary_density"),
    ("boundary_diagnostics", "Boundary Diagnostics", "evidence", "validation_replay_status.png", "boundary_diagnostics_detail.html", "continuity_score"),
    ("evidence_consensus", "Evidence Consensus", "evidence", "validation_replay_status.png", "evidence_consensus_detail.html", "evidence_consensus_strength"),
    ("editorial_pressure", "Editorial Pressure", "editorial", "blocker_pressure_map.png", "editorial_pressure_detail.html", "rhetorical_pressure"),
    ("archetypes", "Recurring Archetypes", "editorial", "archetype_remediation_map.png", "archetypes_detail.html", "remediation_priority"),
    ("review_queue", "Review Queue", "editorial", "compressed_review_queue_matrix.png", "review_queue_detail.html", "review_queue_tier"),
    ("governance_readiness", "Governance Readiness", "governance", "governance_readiness_radar.png", "governance_readiness_detail.html", "readiness_score"),
    ("rc_thresholds", "RC Thresholds", "governance", "governance_threshold_gap_chart.png", "rc_thresholds_detail.html", "governance_threshold_gap"),
    ("remediation", "Remediation", "remediation", "remediation_priority_matrix.png", "remediation_detail.html", "remediation_priority"),
    ("reviewer_decision", "Reviewer Decision Support", "governance", "reviewer_focus_heatmap.png", "reviewer_decision_detail.html", "blocker_severity"),
]


def _metric_value(metric_id: str, outputs: dict) -> dict:
    corpus = outputs.get("corpus_summary") or {}
    index = outputs.get("corpus_index") or {}
    intelligence = outputs.get("corpus_intelligence") or {}
    diagnostics = outputs.get("governance_diagnostics") or {}
    compressed = outputs.get("compressed_review_queue") or {}
    if metric_id == "readiness_score":
        return {"value": corpus.get("corpus_readiness_score"), "source": "corpus/corpus_summary.json"}
    if metric_id == "rhetorical_pressure":
        return {"value": (intelligence.get("summary") or {}).get("mean_peak_pressure"), "source": "corpus/corpus_intelligence.json"}
    if metric_id == "governance_threshold_gap":
        return {"failed_threshold_count": (diagnostics.get("summary") or {}).get("failed_threshold_count", 0), "source": "governance/governance_diagnostics.json"}
    if metric_id in {"review_queue_tier", "blocker_severity"}:
        return {"tier_1_blocker_count": (compressed.get("summary") or {}).get("tier_1_blocker_count", 0), "source": "workbench/compressed_review_queue.json"}
    if metric_id == "continuity_score":
        return {"value": (index.get("summary") or {}).get("mean_structural_coherence_score"), "source": "corpus/corpus_index.json"}
    if metric_id == "remediation_priority":
        return {"count": ((outputs.get("remediation_tracker") or {}).get("summary") or {}).get("remediation_count", 0), "source": "remediation/remediation_tracker.json"}
    return {"qualitative": "review available when source artifact exists", "source": "dashboard/expert_metric_ranges.json"}


def _status(metric_id: str, observed: dict) -> str:
    value = observed.get("value")
    if metric_id == "readiness_score":
        return "concern" if (value or 0) < 0.68 else "caution" if value < 0.82 else "good"
    if metric_id == "rhetorical_pressure":
        return "concern" if (value or 0) >= 0.7 else "caution" if (value or 0) >= 0.45 else "good"
    if metric_id == "governance_threshold_gap":
        return "concern" if observed.get("failed_threshold_count") else "good"
    if metric_id in {"review_queue_tier", "blocker_severity"}:
        return "concern" if observed.get("tier_1_blocker_count") else "good"
    if metric_id == "continuity_score":
        return "concern" if (value or 0) < 0.5 else "caution" if (value or 0) < 0.7 else "good"
    return "review"


def _action(metric_id: str, status: str) -> str:
    if status == "good":
        return "preserve as-is unless human review identifies a context-specific issue"
    actions = {
        "speech_rate_wpm": "edit pacing or re-record compressed phrasing after review",
        "silence_ratio": "add transition or breathing room where it supports meaning",
        "rhetorical_pressure": "clarify argument, add example, or add visual reset",
        "abstract_concrete_balance": "add concrete example or visual support",
        "visual_reset_frequency": "add visual reset, B-roll, title card, or transition",
        "topic_drift": "clarify bridge language and review topic continuity",
        "governance_threshold_gap": "resolve blocking thresholds through evidence-backed human review",
        "readiness_score": "work threshold gaps and Tier 1 review items before promotion",
        "review_queue_tier": "review manually and document disposition",
        "blocker_severity": "review manually and document disposition",
    }
    return actions.get(metric_id, "review manually before changing production or edit decisions")


def build_graph_interpretation_index(outputs: dict) -> dict:
    rows = []
    for graph_id, title, subsystem, graph, detail, metric in DETAIL_SPECS:
        observed = _metric_value(metric, outputs)
        status = _status(metric, observed)
        rows.append({
            "graph_id": graph_id,
            "graph_title": title,
            "graph_path": f"graphs/{graph}",
            "related_artifact_paths": [observed.get("source") or "dashboard/expert_metric_ranges.json"],
            "subsystem": subsystem,
            "metric_id": metric,
            "status": status,
            "what_it_measures": f"{title} summarizes deterministic local signals for the {subsystem} review area.",
            "why_it_matters": "It helps a reviewer decide whether the video structure supports clarity, pacing, and governed release readiness.",
            "how_to_read": "Use the graph as a directional review aid. Compare the current value or pattern with the good, caution, and concern guidance.",
            "good_patterns": ["Stable or balanced values that match the intended style.", "No unresolved Tier 1 or high-pressure review signals for governance pages."],
            "caution_patterns": ["Elevated, sparse, or inconsistent patterns that may deserve human review."],
            "concerning_patterns": ["High pressure, unresolved blockers, failed thresholds, or weak continuity evidence."],
            "current_observed_values": observed,
            "current_interpretation": f"Current status is {status}. This is a deterministic editorial heuristic, not a factual claim about audience behavior or intent.",
            "optimization_actions": [_action(metric, status)],
            "what_not_to_infer": [
                "Do not infer viewer retention, truth, intent, identity, demographics, clinical state, or actual emotion.",
                "Do not treat this graph as an autonomous edit instruction.",
            ],
            "evidence_refs": [observed.get("source") or "dashboard/expert_metric_ranges.json"],
            "detail_page_path": f"visualizations/detail/{detail}",
        })
    output = base_artifact(method="deterministic_graph_interpretation_v1")
    output.update({
        "graph_interpretation_index_id": deterministic_id("GINT", [(row["graph_id"], row["status"]) for row in rows]),
        "graph_interpretations": rows,
        "summary": {"graph_interpretation_count": len(rows)},
    })
    return output
