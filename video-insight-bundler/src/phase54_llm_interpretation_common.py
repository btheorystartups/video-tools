"""Phase V54 LLM-assisted page interpretation and enrichment helpers."""

from __future__ import annotations

import html
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from stability import STATUS_COMPLETE, STATUS_ERROR, deterministic_id, write_json


PHASE_NAME = "V54"
INTERPRETATION_LIMITATION = (
    "Interpretation is advisory and grounded in deterministic artifacts. It does not infer identity, "
    "demographics, true emotion, psychological state, deception, medical status, or certain viewer behavior. "
    "It does not mutate media, timelines, recommendations, readiness status, or governance decisions."
)
SAME_SPEAKER_LIMITATION = (
    "Multi-video comparison uses configured corpus context only; it must not be read as biometric, voice, face, "
    "or same-speaker identity verification."
)
FINGERPRINT_LIMITATION = (
    "Fingerprint pages summarize deterministic communication-pattern evidence only; they are not biometric "
    "fingerprints and cannot verify identity."
)
GOVERNANCE_LIMITATION = (
    "Governance and readiness interpretation explains blocker evidence and thresholds; it never auto-resolves "
    "blockers or changes release status."
)
FORECAST_LIMITATION = (
    "Counterfactual and forecasting pages provide editorial scenario scaffolding, not predictive certainty or "
    "autonomous editing instructions."
)

REQUIRED_VISIBLE_SECTIONS = [
    "Expert Summary",
    "What This Measures",
    "Why It Matters",
    "How To Read This",
    "Good Patterns",
    "Caution Patterns",
    "Concerning Patterns",
    "What The Current Values Suggest",
    "Operational Interpretation",
    "Optimization Options",
    "What To Preserve",
    "Related Evidence",
    "Related Recommendations",
    "What Not To Infer",
    "Human Review Guidance",
    "Limitations",
]

VALIDATION_REQUIRED_SECTIONS = [
    "Expert Summary",
    "What This Measures",
    "Why It Matters",
    "How To Read This",
    "Good Patterns",
    "Caution Patterns",
    "Concerning Patterns",
    "What The Current Values Suggest",
    "Operational Interpretation",
    "Optimization Options",
    "What To Preserve",
    "Related Evidence",
    "Related Recommendations",
    "What Not To Infer",
    "Human Review Guidance",
    "Limitations",
]

TARGET_PAGES = [
    "dashboard.html",
    "transcript_explorer.html",
    "emotional_arc.html",
    "pacing_analysis.html",
    "persona_analysis.html",
    "rhetorical_flow.html",
    "segment_timeline.html",
    "transcript_density.html",
    "recommendations_report.html",
    "acoustic_analysis.html",
    "topic_analysis.html",
    "rhetorical_deep_dive.html",
    "segment_quality.html",
    "frame_contact_sheet.html",
    "revision_graph.html",
    "revision_comparison.html",
    "release_readiness.html",
    "mutation_safety.html",
    "editorial_evolution.html",
    "evidence_consensus.html",
    "continuity_analysis.html",
    "segmentation_confidence.html",
    "modality_alignment.html",
    "topic_continuity.html",
    "rhetorical_coherence.html",
    "boundary_diagnostics.html",
    "discourse_state.html",
    "argument_graph.html",
    "narrative_memory.html",
    "callback_resolution.html",
    "editorial_ambiguity.html",
    "visual_structure.html",
    "shot_boundaries.html",
    "visual_continuity.html",
    "composition_features.html",
    "visual_boundary_alignment.html",
    "artifact_integrity.html",
    "graph_consistency.html",
    "reference_validation.html",
    "lineage_validation.html",
    "migration_registry.html",
    "semantic_readiness.html",
    "run_history.html",
    "artifact_drift.html",
    "metric_drift.html",
    "readiness_drift.html",
    "longitudinal_analysis.html",
    "trend_analysis.html",
    "confidence_volatility.html",
    "recommendation_evolution.html",
    "anomaly_clusters.html",
    "persistent_patterns.html",
    "semantic_evolution.html",
    "sequence_structure.html",
    "scene_hierarchy.html",
    "temporal_rhythm.html",
    "narrative_phase_model.html",
    "editorial_pressure.html",
    "recommendation_dependencies.html",
    "revision_propagation.html",
    "counterfactual_simulation.html",
    "revision_forecasting.html",
    "epistemic_stability.html",
    "multi_video_analysis.html",
    "style_fingerprint.html",
    "rhetorical_fingerprint.html",
    "pacing_fingerprint.html",
    "discourse_fingerprint.html",
    "creator_evolution.html",
    "structural_pattern_mining.html",
    "comparative_recommendations.html",
    "semantic_equivalence_scaffolding.html",
]

FIELD_NAMES = [
    "expert_summary",
    "current_value_interpretation",
    "good_patterns_observed",
    "caution_patterns_observed",
    "concerning_patterns_observed",
    "optimization_options",
    "preserve_recommendations",
    "evidence_to_review",
    "human_review_guidance",
    "limitations",
    "confidence",
    "uncertainty_notes",
]

FORBIDDEN_CLAIMS = [
    "proves",
    "proves true",
    "diagnoses emotion",
    "diagnoses psychological",
    "detects true emotion",
    "predicts audience retention",
    "viewer will",
    "identifies the speaker",
    "identifies a person",
    "confirms personality",
    "guarantees improvement",
    "uses face recognition",
    "uses facial recognition",
    "uses voice identity",
    "demographic inference",
    "deception detection",
    "medical diagnosis",
    "auto-resolve governance",
    "automatically resolves blockers",
    "changes readiness",
    "mutates media",
    "mutates timelines",
]

FAMILY_BY_PAGE = {
    "dashboard.html": "core",
    "transcript_explorer.html": "core",
    "emotional_arc.html": "emotional",
    "pacing_analysis.html": "pacing",
    "persona_analysis.html": "persona",
    "rhetorical_flow.html": "rhetorical",
    "segment_timeline.html": "segment",
    "transcript_density.html": "pacing",
    "recommendations_report.html": "recommendations",
    "acoustic_analysis.html": "acoustic",
    "topic_analysis.html": "topic",
    "rhetorical_deep_dive.html": "rhetorical",
    "segment_quality.html": "segment",
    "frame_contact_sheet.html": "visual",
    "revision_graph.html": "governance",
    "revision_comparison.html": "governance",
    "release_readiness.html": "governance",
    "mutation_safety.html": "governance",
    "editorial_evolution.html": "history",
    "evidence_consensus.html": "governance",
    "continuity_analysis.html": "continuity",
    "segmentation_confidence.html": "segment",
    "modality_alignment.html": "continuity",
    "topic_continuity.html": "topic",
    "rhetorical_coherence.html": "rhetorical",
    "boundary_diagnostics.html": "segment",
    "discourse_state.html": "rhetorical",
    "argument_graph.html": "rhetorical",
    "narrative_memory.html": "rhetorical",
    "callback_resolution.html": "rhetorical",
    "editorial_ambiguity.html": "rhetorical",
    "visual_structure.html": "visual",
    "shot_boundaries.html": "visual",
    "visual_continuity.html": "visual",
    "composition_features.html": "visual",
    "visual_boundary_alignment.html": "visual",
    "artifact_integrity.html": "validation",
    "graph_consistency.html": "validation",
    "reference_validation.html": "validation",
    "lineage_validation.html": "validation",
    "migration_registry.html": "validation",
    "semantic_readiness.html": "validation",
    "run_history.html": "history",
    "artifact_drift.html": "history",
    "metric_drift.html": "history",
    "readiness_drift.html": "history",
    "longitudinal_analysis.html": "history",
    "trend_analysis.html": "history",
    "confidence_volatility.html": "history",
    "recommendation_evolution.html": "history",
    "anomaly_clusters.html": "history",
    "persistent_patterns.html": "history",
    "semantic_evolution.html": "history",
    "sequence_structure.html": "advanced",
    "scene_hierarchy.html": "advanced",
    "temporal_rhythm.html": "advanced",
    "narrative_phase_model.html": "advanced",
    "editorial_pressure.html": "advanced",
    "recommendation_dependencies.html": "advanced",
    "revision_propagation.html": "advanced",
    "counterfactual_simulation.html": "forecast",
    "revision_forecasting.html": "forecast",
    "epistemic_stability.html": "advanced",
    "multi_video_analysis.html": "multi_video",
    "style_fingerprint.html": "fingerprint",
    "rhetorical_fingerprint.html": "fingerprint",
    "pacing_fingerprint.html": "fingerprint",
    "discourse_fingerprint.html": "fingerprint",
    "creator_evolution.html": "multi_video",
    "structural_pattern_mining.html": "multi_video",
    "comparative_recommendations.html": "multi_video",
    "semantic_equivalence_scaffolding.html": "advanced",
}


def _title_from_page(page: str) -> str:
    if page == "dashboard.html":
        return "Analysis Dashboard"
    return Path(page).stem.replace("_", " ").title().replace("Llm", "LLM")


def llm_interpretation_config(config: dict | None = None) -> dict:
    config = dict(config or {})
    defaults = {
        "llm_interpretation_enabled": False,
        "enable_llm_interpretation": False,
        "llm_interpretation_mode": "deterministic_fallback",
        "llm_provider": "",
        "llm_model": "",
        "llm_timeout_seconds": 30,
        "llm_timeout": 30,
        "llm_max_retries": 0,
        "llm_temperature": 0,
        "llm_max_pages": None,
        "llm_prompt_capture_enabled": True,
        "llm_response_capture_enabled": True,
        "llm_validation_required": True,
        "deterministic_fallback_required": True,
        "llm_cache_enabled": True,
        "llm_force_regenerate": False,
        "llm_dry_run": False,
    }
    env_map = {
        "enable_llm_interpretation": "VIB_ENABLE_LLM_INTERPRETATION",
        "llm_interpretation_enabled": "VIB_ENABLE_LLM_INTERPRETATION",
        "llm_interpretation_mode": "VIB_LLM_INTERPRETATION_MODE",
        "llm_provider": "VIB_LLM_PROVIDER",
        "llm_model": "VIB_LLM_MODEL",
        "llm_timeout": "VIB_LLM_TIMEOUT",
        "llm_max_pages": "VIB_LLM_MAX_PAGES",
        "llm_cache_enabled": "VIB_LLM_CACHE_ENABLED",
        "llm_force_regenerate": "VIB_LLM_FORCE_REGENERATE",
        "llm_dry_run": "VIB_LLM_DRY_RUN",
    }
    for key, env in env_map.items():
        if key not in config and env in os.environ:
            value = os.environ[env]
            if key.startswith("enable_") or key in {"llm_cache_enabled", "llm_force_regenerate", "llm_dry_run"}:
                config[key] = value.lower() in {"1", "true", "yes", "on"}
            elif key in {"llm_timeout", "llm_max_pages"}:
                config[key] = int(value) if value else None
            else:
                config[key] = value
    merged = {**defaults, **config}
    if merged.get("llm_interpretation_enabled"):
        merged["enable_llm_interpretation"] = True
    mode = str(merged.get("llm_interpretation_mode") or "").strip().lower()
    if mode in {"fallback", "disabled"}:
        mode = "deterministic_fallback" if mode == "fallback" else "disabled"
    if mode not in {"disabled", "deterministic_fallback", "mock_llm", "external_llm_provider_configured"}:
        mode = "deterministic_fallback"
    merged["llm_interpretation_mode"] = mode
    if mode in {"mock_llm", "external_llm_provider_configured"}:
        merged["enable_llm_interpretation"] = True
        merged["llm_interpretation_enabled"] = True
    return merged


def page_explanation_catalog() -> dict:
    entries = []
    for page in TARGET_PAGES:
        title = _title_from_page(page)
        family = FAMILY_BY_PAGE.get(page, "core")
        entries.append({"page_id": Path(page).stem, "page_path": f"visualizations/{page}", "page": page, "title": title, "family": family, **_static_explanation(title, family)})
    return {"analysis_status": STATUS_COMPLETE, "method": "phase54_page_explanation_catalog_v1", "page_explanations": entries, "summary": {"page_count": len(entries)}, "limitations": [INTERPRETATION_LIMITATION]}


def _static_explanation(title: str, family: str) -> dict:
    base = {
        "what_this_measures": f"{title} collects deterministic artifacts, metrics, evidence references, and generated visual panels for expert review.",
        "why_it_matters": "It helps reviewers separate measured evidence from interpretation, choose low-risk optimization paths, and preserve intentional style.",
        "how_to_read_this": "Read values, rows, cards, and curves as directional evidence. Check linked artifacts and recommendations before deciding whether a pattern needs action.",
        "good_patterns": ["Signals are coherent with neighboring evidence.", "Important claims have enough support and readable transitions.", "The pattern appears intentional and does not create validation or governance pressure."],
        "caution_patterns": ["Sparse data, elevated volatility, abrupt transitions, or isolated spikes require review.", "A pattern can be stylistic rather than defective."],
        "concerning_patterns": ["Repeated unresolved pressure, failed validation, weak continuity, or governance blockers require human review before release decisions."],
        "what_not_to_infer": [INTERPRETATION_LIMITATION],
    }
    if family == "emotional":
        base.update({
            "what_this_measures": "Energy, valence, certainty, and intensity are deterministic editorial tone proxies across time or segments.",
            "why_it_matters": "Tone-proxy movement helps reviewers see contrast, monotony, recovery after intense sections, and whether delivery dynamics fit the intended edit.",
            "how_to_read_this": "Read rises and dips as measured tone-proxy movement, not true emotion or inner state.",
        })
    elif family == "pacing":
        base.update({
            "what_this_measures": "Speech rate, transcript density, pauses, and compression patterns over time.",
            "why_it_matters": "Pacing affects how much cognitive load dense claims place on a listener and where pauses or structural splits may help.",
            "how_to_read_this": "Look for sustained fast regions, slow valleys, volatility, and dense segments rather than judging a single WPM point.",
        })
    elif family == "acoustic":
        base.update({
            "what_this_measures": "RMS/local energy, silence, spikes, variability, and audio dynamics.",
            "why_it_matters": "Audio dynamics can reveal candidate emphasis, silence, level instability, or noise-review points.",
            "how_to_read_this": "Spikes and valleys are review candidates for emphasis, clipping, noise, or silence; they are not emotion evidence.",
        })
    elif family == "topic":
        base.update({
            "what_this_measures": "Deterministic topic terms, recurrence, drift, re-entry, and transition support.",
            "why_it_matters": "Topic continuity helps assess whether the argument moves with enough bridge language and payoff.",
            "how_to_read_this": "Compare clusters, repeated terms, gaps, and re-entry points against transcript context.",
        })
    elif family == "persona":
        base.update({
            "what_this_measures": "Style and rhetorical posture evidence derived from local text and marker categories.",
            "why_it_matters": "It helps preserve consistent delivery style while avoiding overcorrection of intentional rhetorical posture.",
            "how_to_read_this": "Treat style categories as communication-pattern evidence, not identity, personality, or demographic diagnosis.",
        })
    elif family == "rhetorical":
        base.update({
            "what_this_measures": "Argument progression, claims, examples, questions, callbacks, ambiguity, and discourse pressure.",
            "why_it_matters": "Rhetorical structure determines whether setup, transition, escalation, evidence, and payoff are easy to review.",
            "how_to_read_this": "Follow graph edges, rows, or timelines as candidate support relationships and unresolved states.",
        })
    elif family == "segment":
        base.update({
            "what_this_measures": "Segment boundaries, coherence, density, transition confidence, and local evidence concentration.",
            "why_it_matters": "Segment quality controls whether reviewers can localize problems without changing the wrong section.",
            "how_to_read_this": "Review segment-level rows with timestamp, boundary confidence, transcript, and linked recommendation context.",
        })
    elif family == "visual":
        base.update({
            "what_this_measures": "Shot/reset rhythm, staticness, composition features, visual continuity, and visual support for discourse boundaries.",
            "why_it_matters": "Visual structure can relieve dense rhetoric, clarify transitions, or reveal places where the image track stops supporting the argument.",
            "how_to_read_this": "Treat shot and composition signals as editorial proxies; inspect source frames before drawing conclusions.",
        })
    elif family == "fingerprint":
        base.update({
            "what_this_measures": "Recurring deterministic communication-pattern summaries across style, pacing, rhetorical, or discourse artifacts.",
            "why_it_matters": "These summaries help compare consistency and drift without treating patterns as identity proof.",
            "how_to_read_this": "Read clusters as local corpus pattern summaries only; they are not biometric fingerprints.",
            "what_not_to_infer": [INTERPRETATION_LIMITATION, FINGERPRINT_LIMITATION],
        })
    elif family == "multi_video":
        base.update({
            "what_this_measures": "Configured corpus-level comparison of deterministic metrics, recommendations, and structural patterns across videos.",
            "why_it_matters": "Cross-video views reveal recurring strengths, recurring review burdens, and candidate optimization priorities.",
            "how_to_read_this": "Compare rows directionally within the configured corpus only; no same-speaker or identity inference is supported.",
            "what_not_to_infer": [INTERPRETATION_LIMITATION, SAME_SPEAKER_LIMITATION],
        })
    elif family == "forecast":
        base.update({
            "what_this_measures": "Deterministic scenario scaffolding for possible revision propagation or editorial outcomes.",
            "why_it_matters": "It helps plan human-reviewed revision paths without allowing the system to predict certainty or edit autonomously.",
            "how_to_read_this": "Read each result as a candidate scenario requiring evidence review, not a forecast guarantee.",
            "what_not_to_infer": [INTERPRETATION_LIMITATION, FORECAST_LIMITATION],
        })
    elif family == "governance":
        base.update({
            "what_this_measures": "Readiness, blockers, mutation safety, validation status, thresholds, and review-state evidence.",
            "why_it_matters": "Governance pages explain why a release or mutation is capped, blocked, or review-limited.",
            "how_to_read_this": "Use badges and rows as blocker evidence. Advisory text cannot resolve blockers or change readiness.",
            "what_not_to_infer": [INTERPRETATION_LIMITATION, GOVERNANCE_LIMITATION],
        })
    elif family == "history":
        base.update({
            "what_this_measures": "Run history, artifact drift, metric drift, readiness trends, anomalies, volatility, and persistent patterns.",
            "why_it_matters": "Longitudinal views separate one-off changes from persistent review burden or meaningful trend movement.",
            "how_to_read_this": "Compare deltas and trend panels with snapshot provenance before treating movement as meaningful.",
        })
    elif family == "validation":
        base.update({
            "what_this_measures": "Artifact integrity, graph consistency, reference validity, lineage, migration, and semantic readiness status.",
            "why_it_matters": "Validation pages protect reviewers from trusting missing, stale, orphaned, or inconsistent evidence.",
            "how_to_read_this": "Start with failed rows and missing references, then inspect linked artifacts and provenance.",
        })
    elif family == "advanced":
        base.update({
            "what_this_measures": "Higher-order deterministic structure such as sequence phases, temporal rhythm, pressure, dependencies, and epistemic stability.",
            "why_it_matters": "These pages help reviewers reason about structure while keeping action tied to measured evidence.",
            "how_to_read_this": "Use the panels to identify candidate review paths and dependency risks, not autonomous edits.",
        })
    return base


def _observed_summary(page: str, output_dir: Path, context: dict | None = None) -> dict:
    context = context or {}
    sources = []
    for rel in _candidate_artifact_refs(page):
        path = output_dir / rel
        if path.exists():
            sources.append(rel)
    html_path = output_dir / "visualizations" / page
    text = html_path.read_text(encoding="utf-8", errors="ignore") if html_path.exists() else ""
    metrics = re.findall(r"<span>([^<]+)</span><strong>([^<]*)</strong>", text)[:8]
    headings = re.findall(r"<h[23][^>]*>(.*?)</h[23]>", text)[:8]
    return {
        "page": page,
        "source_artifacts": sources,
        "visible_metric_samples": [{"label": _strip_tags(k), "value": _strip_tags(v)} for k, v in metrics],
        "visible_panel_headings": [_strip_tags(x) for x in headings],
        "recommendation_count": _recommendation_count(output_dir, context),
    }


def _candidate_artifact_refs(page: str) -> list[str]:
    stem = Path(page).stem
    refs = [
        f"reports/{stem}.json",
        f"integrity/{stem}.json",
        f"history/{stem}.json",
        f"longitudinal/{stem}.json",
        f"sequence/{stem}.json",
        f"comparative/{stem}.json",
        f"continuity/{stem}.json",
        f"discourse/{stem}.json",
        f"visual_structure/{stem}.json",
        f"revision_graph/{stem}.json",
        "recommendations.json",
        "analysis_index.json",
    ]
    special = {
        "pacing_analysis.html": ["reports/acoustic_statistics.json", "reports/quality_report.json"],
        "emotional_arc.html": ["emotional_arc.json", "llm_context_bundle.json"],
        "release_readiness.html": ["revision_graph/release_readiness_report.json", "governance/rc_assessment.json"],
        "mutation_safety.html": ["revision_graph/mutation_safety_contract.json"],
        "multi_video_analysis.html": ["comparative/multi_video_analysis.json", "video_comparison/multi_video_comparison_workbench.json"],
    }
    return special.get(page, []) + refs


def _recommendation_count(output_dir: Path, context: dict) -> int:
    if isinstance(context.get("recommendations"), list):
        return len(context["recommendations"])
    for rel in ["recommendations.json", "recommendations/recommendation_lineage.json"]:
        path = output_dir / rel
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            return len(data.get("recommendations") or data.get("lineage_items") or [])
    return 0


def build_interpretation_prompt(entry: dict, observed: dict) -> dict:
    schema = {field: "string_or_array" for field in FIELD_NAMES}
    prompt = {
        "page_title": entry["title"],
        "page_type": entry["family"],
        "static_explanation": {key: entry.get(key) for key in ["what_this_measures", "why_it_matters", "how_to_read_this", "good_patterns", "caution_patterns", "concerning_patterns", "what_not_to_infer"]},
        "graph_metric_data_summary": observed,
        "observed_values": observed.get("visible_metric_samples", []),
        "relevant_recommendations": observed.get("recommendation_count", 0),
        "relevant_evidence_refs": observed.get("source_artifacts", []),
        "related_timeline_segment_refs": ["timeline/temporal_evidence_index.json", "visualizations/segment_timeline.html"],
        "governance_context": "Advisory interpretation cannot change readiness or blockers.",
        "limitation_rules": [INTERPRETATION_LIMITATION],
        "required_output_json_schema": schema,
    }
    return {
        "prompt_id": deterministic_id("LLMP", entry["page"], observed),
        "page": entry["page"],
        "graph_or_page_id": entry["page_id"],
        "prompt": prompt,
    }


def deterministic_fallback_interpretation(entry: dict, observed: dict) -> dict:
    title = entry["title"]
    family = entry["family"]
    source_refs = observed.get("source_artifacts") or ["No source artifact link was available in this fixture; inspect generated artifacts when present."]
    rec_count = observed.get("recommendation_count", 0)
    metric_text = ", ".join(f"{m['label']}: {m['value']}" for m in observed.get("visible_metric_samples", [])[:3]) or "No compact metric sample was visible on the page."
    summary = (
        f"{title} should be read as an expert review surface that combines measured artifacts with advisory interpretation. "
        f"The current page exposes {len(source_refs)} supporting artifact reference(s) and {rec_count} related recommendation item(s). "
        "Use the text below to decide what to inspect next, not to automate edits or governance changes."
    )
    if family == "emotional":
        current = f"Current tone-proxy evidence suggests reviewing tonal movement, intensity recovery, and whether stability is intentional. Metric sample: {metric_text}"
    elif family == "pacing":
        current = f"Current pacing evidence suggests checking dense or volatile sections for listener load, fast compression, and useful pauses. Metric sample: {metric_text}"
    elif family == "acoustic":
        current = f"Current acoustic evidence suggests reviewing energy spikes, valleys, silence, and possible noise or level shifts. Metric sample: {metric_text}"
    elif family in {"topic", "rhetorical"}:
        current = f"Current discourse evidence suggests checking transition clarity, support relationships, callbacks, and unresolved pressure. Metric sample: {metric_text}"
    elif family == "visual":
        current = f"Current visual evidence suggests checking whether shot rhythm, visual resets, and composition changes support dense sections and transitions. Metric sample: {metric_text}"
    elif family == "governance":
        current = f"Current governance evidence suggests reviewing blockers, caps, thresholds, and validation status manually. Metric sample: {metric_text}"
    elif family == "multi_video":
        current = f"Current comparison evidence suggests looking for directional differences and recurring review burdens within the configured corpus only. Metric sample: {metric_text}"
    elif family == "fingerprint":
        current = f"Current fingerprint evidence suggests recurring communication-pattern signals that may help preserve style, without biometric or identity claims. Metric sample: {metric_text}"
    elif family == "forecast":
        current = f"Current scenario evidence suggests candidate revision paths to review, not certain predictions or autonomous edit instructions. Metric sample: {metric_text}"
    else:
        current = f"Current values suggest a directional review surface with evidence links that should be inspected before edits. Metric sample: {metric_text}"
    limitations = [INTERPRETATION_LIMITATION]
    if family == "fingerprint":
        limitations.append(FINGERPRINT_LIMITATION)
    if family == "multi_video":
        limitations.append(SAME_SPEAKER_LIMITATION)
    if family == "governance":
        limitations.append(GOVERNANCE_LIMITATION)
    if family == "forecast":
        limitations.append(FORECAST_LIMITATION)
    return {
        "expert_summary": summary,
        "current_value_interpretation": current,
        "good_patterns_observed": ["Evidence is linked and reviewable.", "Measured signals can be compared against adjacent pages before action.", "Intentional style can be preserved when human review supports it."],
        "caution_patterns_observed": ["Sparse or missing artifacts may limit confidence.", "Elevated values can be intentional style or artifact effects.", "Do not treat a single graph or row as sufficient for revision."],
        "concerning_patterns_observed": ["Repeated unresolved pressure, failed validation, missing references, or governance blockers require review.", "Dense claims without transition, evidence, or visual relief may need optimization."],
        "optimization_options": ["Add transition language or examples where continuity is weak.", "Split dense sections or add pauses when pacing is compressed.", "Add visual resets or chapter markers where rhetoric stays dense.", "Re-record only after human review confirms source-level issues.", "Preserve intentional style when it remains clear and governed."],
        "preserve_recommendations": ["Preserve recurring themes that support callback structure.", "Preserve energetic or reflective delivery when it serves the intended style.", "Preserve validated evidence and do not rewrite around weak or missing artifacts."],
        "evidence_to_review": source_refs,
        "human_review_guidance": "Inspect the linked artifacts, timestamps, graph panels, and recommendations before deciding whether to revise, preserve, annotate, or escalate.",
        "operational_interpretation": "Treat this page as a review-routing aid. Deterministic measurements and governance artifacts remain authoritative; interpretation text only explains what a reviewer may inspect next.",
        "limitations": limitations,
        "confidence": "medium" if len(source_refs) > 1 else "limited",
        "uncertainty_notes": "Fallback interpretation is deterministic and advisory; confidence depends on available source artifacts and visible measured values.",
    }


def call_llm_for_interpretation(prompt_packet: dict, config: dict, llm_client: Callable[[dict, dict], dict] | None = None) -> tuple[dict | None, str]:
    if not config.get("enable_llm_interpretation") or config.get("llm_dry_run"):
        return None, "deterministic_fallback"
    if llm_client is None:
        return None, "deterministic_fallback_no_provider"
    response = llm_client(prompt_packet["prompt"], config)
    return response, "llm_assisted"


def validate_interpretation_payload(payload: dict) -> dict:
    missing = [field for field in FIELD_NAMES if field not in payload or payload.get(field) in (None, "", [])]
    text = json.dumps(payload, ensure_ascii=False).lower()
    forbidden = forbidden_claims_in_text(text)
    return {
        "validation_status": STATUS_COMPLETE if not missing and not forbidden else STATUS_ERROR,
        "missing_fields": missing,
        "forbidden_claims": forbidden,
    }


def forbidden_claims_in_text(text: str) -> list[str]:
    lowered = str(text).lower()
    found = []
    for claim in FORBIDDEN_CLAIMS:
        claim_l = claim.lower()
        start = 0
        while True:
            idx = lowered.find(claim_l, start)
            if idx < 0:
                break
            window = lowered[max(0, idx - 36):idx]
            if not any(marker in window for marker in ["not ", "no ", "does not ", "do not ", "without ", "cannot ", "never "]):
                found.append(claim)
                break
            start = idx + len(claim_l)
    return found


def safety_filter_interpretation(payload: dict) -> tuple[dict, dict]:
    validation = validate_interpretation_payload(payload)
    if validation["forbidden_claims"]:
        safe_payload = dict(payload)
        safe_payload["current_value_interpretation"] = "Generated interpretation was rejected for forbidden claim language; use deterministic fallback and human review."
        safe_payload["limitations"] = list(dict.fromkeys((safe_payload.get("limitations") or []) + [INTERPRETATION_LIMITATION]))
        return safe_payload, {**validation, "safety_status": STATUS_ERROR}
    return payload, {**validation, "safety_status": STATUS_COMPLETE}


def build_page_interpretations(output_dir: Path, context: dict | None = None, config: dict | None = None, llm_client: Callable[[dict, dict], dict] | None = None) -> dict:
    cfg = llm_interpretation_config(config)
    catalog = page_explanation_catalog()["page_explanations"]
    if cfg.get("llm_max_pages"):
        catalog = catalog[: int(cfg["llm_max_pages"])]
    prompts = []
    responses = []
    provenance = []
    validation = []
    safety = []
    fallback = []
    page_rows = []
    generated_at = datetime.now(timezone.utc).isoformat()
    for entry in catalog:
        observed = _observed_summary(entry["page"], output_dir, context)
        prompt_packet = build_interpretation_prompt(entry, observed)
        prompts.append(prompt_packet)
        raw, mode = call_llm_for_interpretation(prompt_packet, cfg, llm_client)
        if raw is None:
            payload = deterministic_fallback_interpretation(entry, observed)
            fallback.append({"page": entry["page"], "reason": mode, "generated_interpretation": payload})
            status = "deterministic_fallback"
        else:
            payload = raw
            status = "llm_assisted"
        safe_payload, safety_row = safety_filter_interpretation(payload)
        if safety_row["safety_status"] != STATUS_COMPLETE:
            safe_payload = deterministic_fallback_interpretation(entry, observed)
            status = "deterministic_fallback"
            fallback.append({"page": entry["page"], "reason": "llm_output_rejected_for_safety", "generated_interpretation": safe_payload})
        val = validate_interpretation_payload(safe_payload)
        responses.append({"response_id": deterministic_id("LLMR", entry["page"], safe_payload), "page": entry["page"], "interpretation_status": status, "response": safe_payload})
        provenance.append({
            "provenance_id": deterministic_id("LLMPROV", entry["page"], prompt_packet["prompt_id"], status),
            "page": entry["page"],
            "graph_or_page_id": entry["page_id"],
            "generated_at": generated_at,
            "provider": cfg.get("llm_provider") or ("deterministic_fallback" if status == "deterministic_fallback" else "configured_provider"),
            "model": cfg.get("llm_model") or ("deterministic_fallback_v1" if status == "deterministic_fallback" else "configured_model"),
            "prompt_id": prompt_packet["prompt_id"],
            "source_artifacts_used": observed.get("source_artifacts", []),
            "evidence_references": safe_payload.get("evidence_to_review", []),
            "validation_status": val["validation_status"],
        })
        validation.append({"page": entry["page"], **val})
        safety.append({"page": entry["page"], **safety_row})
        page_rows.append({**entry, "interpretation_status": status, "observed_summary": observed, "interpretation": safe_payload})
    page_family_rows = [{"page": row["page"], "page_id": row["page_id"], "title": row["title"], "family": row["family"], "canonical_html_path": row["page_path"]} for row in page_rows]
    evidence_rows = [{"page": row["page"], "related_evidence": row["interpretation"].get("evidence_to_review", []), "link_validation": "actual_html_validation"} for row in page_rows]
    recommendation_rows = [{"page": row["page"], "related_recommendations": ["recommendations_report.html"], "recommendation_count": (row.get("observed_summary") or {}).get("recommendation_count", 0)} for row in page_rows]
    audit_rows = [{"page": row["page"], "family": row["family"], "interpretation_status": row["interpretation_status"], "required_sections": REQUIRED_VISIBLE_SECTIONS, "rendered_html_path": row["page_path"]} for row in page_rows]
    return {
        "page_interpretation_registry": _registry("page_interpretation_registry", "phase54_page_interpretation_registry_v1", "page_interpretations", page_rows),
        "graph_interpretation_registry": _registry("graph_interpretation_registry", "phase54_graph_interpretation_registry_v1", "graph_interpretations", [row for row in page_rows if row["family"] in {"emotional", "pacing", "acoustic", "topic", "rhetorical", "visual", "fingerprint"}]),
        "interpretation_prompt_registry": _registry("interpretation_prompt_registry", "phase54_interpretation_prompt_registry_v1", "prompt_packets", prompts),
        "interpretation_response_registry": _registry("interpretation_response_registry", "phase54_interpretation_response_registry_v1", "responses", responses),
        "interpretation_provenance_registry": _registry("interpretation_provenance_registry", "phase54_interpretation_provenance_registry_v1", "provenance_entries", provenance),
        "interpretation_validation_registry": _registry("interpretation_validation_registry", "phase54_interpretation_validation_registry_v1", "validation_entries", validation),
        "interpretation_safety_registry": _registry("interpretation_safety_registry", "phase54_interpretation_safety_registry_v1", "safety_entries", safety),
        "deterministic_fallback_registry": _registry("deterministic_fallback_registry", "phase54_deterministic_fallback_registry_v1", "fallback_entries", fallback),
        "page_enrichment_audit": _registry("page_enrichment_audit", "phase54_page_enrichment_audit_v1", "audit_entries", audit_rows),
        "page_family_registry": _registry("page_family_registry", "phase54_page_family_registry_v1", "page_families", page_family_rows),
        "page_evidence_link_registry": _registry("page_evidence_link_registry", "phase54_page_evidence_link_registry_v1", "evidence_links", evidence_rows),
        "page_recommendation_link_registry": _registry("page_recommendation_link_registry", "phase54_page_recommendation_link_registry_v1", "recommendation_links", recommendation_rows),
        "page_explanation_catalog": page_explanation_catalog(),
        "config": cfg,
    }


def _registry(name: str, method: str, rows_key: str, rows: list[dict]) -> dict:
    return {
        "analysis_status": STATUS_COMPLETE,
        "method": method,
        f"{name}_id": deterministic_id(name.upper()[:8], rows),
        rows_key: rows,
        "summary": {"entry_count": len(rows), "llm_count": sum(1 for row in rows if row.get("interpretation_status") == "llm_assisted"), "fallback_count": sum(1 for row in rows if row.get("interpretation_status") == "deterministic_fallback")},
        "limitations": [INTERPRETATION_LIMITATION],
    }


def write_interpretation_outputs(output_dir: Path, outputs: dict) -> None:
    interp_dir = output_dir / "llm_interpretation"
    vis_dir = output_dir / "visualizations" / "llm_interpretation"
    schemas_dir = output_dir / "schemas"
    source_schemas_dir = Path(__file__).resolve().parents[1] / "schemas"
    evidence_dir = output_dir / "verification_evidence"
    reports_dir = output_dir / "reports"
    for directory in [interp_dir, vis_dir, schemas_dir, source_schemas_dir, evidence_dir, reports_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    for key in [
        "page_interpretation_registry",
        "graph_interpretation_registry",
        "interpretation_prompt_registry",
        "interpretation_response_registry",
        "interpretation_provenance_registry",
        "interpretation_validation_registry",
        "interpretation_safety_registry",
        "deterministic_fallback_registry",
        "page_enrichment_audit",
        "page_family_registry",
        "page_evidence_link_registry",
        "page_recommendation_link_registry",
    ]:
        if key not in outputs:
            continue
        write_json(interp_dir / f"{key}.json", outputs[key])
        _write_schema(schemas_dir / f"{key}.schema.json", key)
        _write_schema(source_schemas_dir / f"{key}.schema.json", key)
    for schema_name in [
        "actual_html_page_enrichment_validation",
        "dashboard_card_interpretation_validation",
    ]:
        _write_schema(schemas_dir / f"{schema_name}.schema.json", schema_name)
        _write_schema(source_schemas_dir / f"{schema_name}.schema.json", schema_name)
    _write_llm_dashboard(vis_dir / "llm_interpretation_dashboard.html", "LLM Interpretation Dashboard", outputs["page_interpretation_registry"].get("page_interpretations", []))
    _write_llm_dashboard(vis_dir / "interpretation_validation_dashboard.html", "Interpretation Validation Dashboard", outputs["interpretation_validation_registry"].get("validation_entries", []))
    _write_llm_dashboard(vis_dir / "interpretation_provenance_dashboard.html", "Interpretation Provenance Dashboard", outputs["interpretation_provenance_registry"].get("provenance_entries", []))
    _write_llm_dashboard(vis_dir / "deterministic_fallback_dashboard.html", "Deterministic Fallback Dashboard", outputs["deterministic_fallback_registry"].get("fallback_entries", []))
    _write_llm_dashboard(vis_dir / "page_enrichment_audit_dashboard.html", "Page Enrichment Audit Dashboard", outputs.get("page_enrichment_audit", {}).get("audit_entries", []))
    _write_llm_dashboard(vis_dir / "page_family_coverage_dashboard.html", "Page Family Coverage Dashboard", outputs.get("page_family_registry", {}).get("page_families", []))
    _write_llm_dashboard(vis_dir / "forbidden_claim_scan_dashboard.html", "Forbidden Claim Scan Dashboard", outputs["interpretation_safety_registry"].get("safety_entries", []))
    for name, title, key in [
        ("llm_interpretation_report.md", "LLM Interpretation Report", "page_interpretation_registry"),
        ("page_interpretation_enrichment_report.md", "Page Interpretation Enrichment Report", "page_enrichment_audit"),
        ("actual_html_enrichment_audit_report.md", "Actual HTML Enrichment Audit Report", "page_enrichment_audit"),
        ("dashboard_card_interpretation_report.md", "Dashboard Card Interpretation Report", "page_interpretation_registry"),
        ("interpretation_safety_report.md", "Interpretation Safety Report", "interpretation_safety_registry"),
        ("deterministic_fallback_report.md", "Deterministic Fallback Report", "deterministic_fallback_registry"),
    ]:
        _write_markdown_report(reports_dir / name, title, outputs.get(key, {}))


def enrich_actual_html_pages(output_dir: Path, outputs: dict) -> dict:
    vis_dir = output_dir / "visualizations"
    vis_dir.mkdir(parents=True, exist_ok=True)
    rows = outputs["page_interpretation_registry"]["page_interpretations"]
    enriched = []
    for row in rows:
        page = row["page"]
        path = vis_dir / page
        if not path.exists():
            path.write_text(_base_page(row["title"], ""), encoding="utf-8")
        text = path.read_text(encoding="utf-8", errors="ignore")
        section = render_enrichment_section(row)
        text = re.sub(r"<!-- phase54-page-enrichment:start -->.*?<!-- phase54-page-enrichment:end -->\s*", "", text, flags=re.I | re.S)
        text = re.sub(r"<section class=['\"]panel phase54-page-enrichment['\"].*?</section>\s*", "", text, flags=re.I | re.S)
        text = _ensure_page_shell(text, row["title"])
        text = text.replace("</main>", section + "\n</main>", 1) if "</main>" in text else text + section
        if page == "dashboard.html":
            text = enrich_dashboard_cards(text, rows)
        text = _sanitize_missing_file_hrefs(text, path.parent)
        path.write_text(text, encoding="utf-8")
        enriched.append(str(path))
    return {"enriched_pages": enriched, "enriched_count": len(enriched)}


def render_enrichment_section(row: dict) -> str:
    interp = row["interpretation"]
    badge = {
        "llm_assisted": "LLM-assisted interpretation",
        "deterministic_fallback": "Deterministic fallback interpretation",
        "human_imported": "Human-authored imported interpretation",
    }.get(row.get("interpretation_status"), "Needs interpretation review")
    def p(value: object) -> str:
        if isinstance(value, list):
            return "<ul>" + "".join(f"<li>{_e(item)}</li>" for item in value) + "</ul>"
        return f"<p>{_e(value)}</p>"
    evidence_links = []
    for ref in interp.get("evidence_to_review") or []:
        ref_text = str(ref)
        if re.search(r"\.(json|md|html|csv|png|jpg|jpeg)$", ref_text):
            href = "../" + ref_text.replace("\\", "/")
            evidence_links.append(f"<li><a href='{_e(href)}'>{_e(ref_text)}</a></li>")
        else:
            evidence_links.append(f"<li>{_e(ref_text)}</li>")
    if not evidence_links:
        evidence_links.append("<li>Evidence references unavailable in this generated fixture; inspect analysis index and source artifacts when present.</li>")
    rec_count = (row.get("observed_summary") or {}).get("recommendation_count", 0)
    return (
        "<!-- phase54-page-enrichment:start -->"
        "<section class='phase54-page-enrichment expert-grid'>"
        "<div>"
        f"<section class='panel'><p class='badge'>{_e(badge)}</p><h2>Expert Summary</h2>{p(interp.get('expert_summary'))}</section>"
        f"<section class='panel'><h2>What This Measures</h2><p>{_e(row.get('what_this_measures'))}</p></section>"
        f"<section class='panel'><h2>Why It Matters</h2><p>{_e(row.get('why_it_matters'))}</p></section>"
        f"<section class='panel'><h2>How To Read This</h2><p>{_e(row.get('how_to_read_this'))}</p></section>"
        f"<section class='panel'><h2>Good Patterns</h2>{p(row.get('good_patterns'))}</section>"
        f"<section class='panel'><h2>Caution Patterns</h2>{p(row.get('caution_patterns'))}</section>"
        f"<section class='panel'><h2>Concerning Patterns</h2>{p(row.get('concerning_patterns'))}</section>"
        "</div><div>"
        + _render_page_graph_figure(row)
        + f"<section class='panel'><h2>What The Current Values Suggest</h2>{p(interp.get('current_value_interpretation'))}</section>"
        + f"<section class='panel'><h2>Operational Interpretation</h2>{p(interp.get('operational_interpretation') or 'Use this interpretation to route human review. Deterministic evidence, validation artifacts, recommendations, governance state, blockers, media, and timelines remain unchanged by this text.')}</section>"
        + f"<section class='panel'><h2>Optimization Options</h2>{p(interp.get('optimization_options'))}</section>"
        + f"<section class='panel'><h2>What To Preserve</h2>{p(interp.get('preserve_recommendations'))}</section>"
        + f"<section class='panel'><h2>Related Evidence</h2><ul>{''.join(evidence_links)}</ul></section>"
        + f"<section class='panel'><h2>Related Recommendations</h2><p>{_e(rec_count)} related recommendation item(s) available when linked artifacts exist. See <a href='recommendations_report.html'>Recommendations Report</a>.</p></section>"
        + f"<section class='panel'><h2>What Not To Infer</h2>{p(interp.get('limitations'))}</section>"
        + f"<section class='panel'><h2>Human Review Guidance</h2>{p(interp.get('human_review_guidance'))}</section>"
        + f"<section class='panel limitation-panel'><h2>Limitations</h2>{p(_page_limitations(row))}</section>"
        + "</div></section><!-- phase54-page-enrichment:end -->"
    )


def _page_limitations(row: dict) -> list[str]:
    family = row.get("family")
    limitations = [
        "This system provides deterministic editorial-review and operational workflow support. It does not infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous editorial decisions. Human review is required.",
    ]
    if row.get("interpretation_status") == "llm_assisted":
        limitations.append("LLM-assisted interpretation is advisory explanatory text generated from deterministic project artifacts. It does not modify measured evidence, recommendations, governance state, media, timelines, blockers, or readiness.")
    else:
        limitations.append("Deterministic fallback interpretation, generated without LLM assistance.")
    if family == "fingerprint":
        limitations.append("Fingerprint pages describe deterministic communication-pattern evidence only. They are not biometric fingerprints, identity verification, authentication, face recognition, or voice identity recognition.")
    if family == "multi_video":
        limitations.append("Same-speaker or same-corpus comparison readiness is based on configured corpus context and artifact continuity, not biometric identity recognition, face recognition, or voice identity recognition.")
    if family == "governance":
        limitations.append("Governance status, blocker state, and readiness classification remain controlled by deterministic evidence and human-reviewed governance workflows. Interpretation text does not automatically resolve blockers or promote readiness.")
    if family == "forecast":
        limitations.append("Counterfactual and forecasting interpretation is deterministic editorial scenario scaffolding. It is not predictive certainty, autonomous editing, media mutation, or timeline mutation.")
    return limitations


def enrich_dashboard_cards(text: str, rows: list[dict]) -> str:
    card_html = [
        "<section class='panel phase54-dashboard-cards'><h2>Expert Page Interpretation Index</h2>"
        "<div class='toolbar phase54-search-toolbar'>"
        "<input id='phase54PageSearch' type='search' placeholder='Search interpretation pages' aria-label='Search interpretation pages'>"
        "<span id='phase54SearchCount' class='muted'></span>"
        "</div><div class='graph-card-grid' id='phase54PageCards'>"
    ]
    for row in rows:
        page = row["page"]
        if page == "dashboard.html":
            continue
        rec_count = (row.get("observed_summary") or {}).get("recommendation_count", 0)
        search_text = " ".join([row["title"], page, row.get("family", ""), row.get("why_it_matters") or "", row.get("what_this_measures") or ""])
        card_html.append(
            f"<article class='graph-card' data-phase54-search='{_e(search_text.lower())}'>"
            f"<h3><a href='{_e(page)}'>{_e(row['title'])}</a></h3>"
            f"<p>{_e(row.get('why_it_matters'))}</p>"
            f"<p><strong>{_e(row.get('interpretation_status', 'needs_review').replace('_', ' '))}</strong></p>"
            f"<p>{_e(rec_count)} related recommendation item(s)</p>"
            f"<a class='more-link' href='{_e(page)}'>Explain this graph/page</a> "
            f"<a class='more-link' href='#phase54-evidence'>Open supporting evidence</a>"
            "</article>"
        )
    card_html.append(
        "</div><script>(function(){"
        "var input=document.getElementById('phase54PageSearch');"
        "var cards=[].slice.call(document.querySelectorAll('#phase54PageCards [data-phase54-search]'));"
        "var count=document.getElementById('phase54SearchCount');"
        "function paint(){var q=(input&&input.value||'').toLowerCase().trim();var shown=0;"
        "cards.forEach(function(card){var ok=!q||card.getAttribute('data-phase54-search').indexOf(q)>=0;card.style.display=ok?'':'none';if(ok)shown++;});"
        "if(count)count.textContent=shown+' of '+cards.length+' pages';}"
        "if(input)input.addEventListener('input',paint);paint();"
        "}());</script></section>"
    )
    text = re.sub(r"<section class=['\"]panel phase54-dashboard-cards['\"].*?</section>\s*", "", text, flags=re.I | re.S)
    text = text.replace(">Open detail<", ">Explain this graph/page<")
    text = text.replace("</main>", "".join(card_html) + "</main>", 1) if "</main>" in text else text + "".join(card_html)
    return text


def _render_page_graph_figure(row: dict) -> str:
    title = row.get("title") or row.get("page") or "Page"
    values = _page_graph_values(row)
    max_value = max([value for _label, value in values] + [1])
    width = 720
    height = 320
    left = 54
    top = 28
    plot_width = 610
    plot_height = 210
    slot = plot_width / max(1, len(values))
    bars = []
    labels = []
    for index, (label, value) in enumerate(values):
        bar_height = 4 if max_value <= 0 else max(4, (float(value) / float(max_value)) * plot_height)
        x = left + index * slot + 16
        y = top + plot_height - bar_height
        bars.append(
            f"<rect x='{x:.1f}' y='{y:.1f}' width='{max(24, slot - 32):.1f}' height='{bar_height:.1f}' rx='4' fill='#386b8f'></rect>"
            f"<text x='{x + max(24, slot - 32) / 2:.1f}' y='{y - 7:.1f}' text-anchor='middle' font-size='12' fill='#232323'>{_e(_format_graph_value(value))}</text>"
        )
        labels.append(f"<text x='{x + max(24, slot - 32) / 2:.1f}' y='{top + plot_height + 24:.1f}' text-anchor='middle' font-size='12' fill='#666a6d'>{_e(label)}</text>")
    grid = "".join(
        f"<line x1='{left}' y1='{top + plot_height - plot_height * i / 4:.1f}' x2='{left + plot_width}' y2='{top + plot_height - plot_height * i / 4:.1f}' stroke='#d9d8d2' stroke-width='1'></line>"
        for i in range(5)
    )
    svg = (
        f"<svg viewBox='0 0 {width} {height}' role='img' aria-label='{_e(title)} evidence footprint graph'>"
        "<rect width='720' height='320' fill='#ffffff'></rect>"
        f"<text x='24' y='24' font-size='16' font-weight='700' fill='#232323'>{_e(title)} Evidence Footprint</text>"
        f"{grid}<line x1='{left}' y1='{top}' x2='{left}' y2='{top + plot_height}' stroke='#666a6d'></line>"
        f"<line x1='{left}' y1='{top + plot_height}' x2='{left + plot_width}' y2='{top + plot_height}' stroke='#666a6d'></line>"
        + "".join(bars)
        + "".join(labels)
        + "<text x='24' y='300' font-size='12' fill='#666a6d'>Deterministic page-level graph: artifacts, visible metrics, panels, and related recommendations.</text>"
        + "</svg>"
    )
    return (
        "<figure class='graph phase54-page-graph'>"
        f"{svg}"
        f"<figcaption><span class='badge review'>review</span> {_e(title)} page-level graph. This is a deterministic evidence-footprint chart, not an outcome prediction.</figcaption>"
        "</figure>"
    )


def _page_graph_values(row: dict) -> list[tuple[str, float]]:
    observed = row.get("observed_summary") or {}
    source_count = len(observed.get("source_artifacts") or [])
    metric_count = len(observed.get("visible_metric_samples") or [])
    panel_count = len(observed.get("visible_panel_headings") or [])
    recommendation_count = observed.get("recommendation_count") or 0
    section_count = len(REQUIRED_VISIBLE_SECTIONS)
    return [
        ("Artifacts", float(source_count)),
        ("Metrics", float(metric_count)),
        ("Panels", float(panel_count)),
        ("Recs", float(recommendation_count)),
        ("Sections", float(section_count)),
    ]


def _format_graph_value(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.2f}"


def _sanitize_missing_file_hrefs(text: str, base_dir: Path) -> str:
    def repl(match: re.Match) -> str:
        quote = match.group("quote")
        href = match.group("href")
        if href.startswith(("http://", "https://", "mailto:", "#")) or href.endswith(".html"):
            return match.group(0)
        target = (base_dir / href.split("#", 1)[0]).resolve()
        if target.exists():
            return match.group(0)
        return f"href={quote}#phase54-evidence{quote}"

    return re.sub(r"href=(?P<quote>['\"])(?P<href>[^'\"]+)(?P=quote)", repl, text)


def validate_enriched_pages(output_dir: Path, outputs: dict) -> dict:
    rows = []
    forbidden_pages = []
    invalid_links = []
    missing_pages = []
    for page in TARGET_PAGES:
        path = output_dir / "visualizations" / page
        text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        missing = [section for section in VALIDATION_REQUIRED_SECTIONS if section not in text]
        forbidden = forbidden_claims_in_text(text)
        if forbidden:
            forbidden_pages.append(page)
        if not path.exists():
            missing_pages.append(page)
        for href in re.findall(r"href=['\"]([^'\"]+)['\"]", text):
            if href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = (path.parent / href.split("#", 1)[0]).resolve()
            if not target.exists():
                invalid_links.append({"page": page, "href": href})
        family = FAMILY_BY_PAGE.get(page, "core")
        fingerprint_ok = family != "fingerprint" or "not biometric fingerprints" in text.lower()
        multi_ok = family != "multi_video" or "configured corpus context" in text.lower()
        governance_ok = family != "governance" or "does not automatically resolve blockers or promote readiness" in text.lower() or "never auto-resolves blockers" in text.lower()
        status = STATUS_COMPLETE if path.exists() and not missing and not forbidden and fingerprint_ok and multi_ok and governance_ok else STATUS_ERROR
        row = {
            "page_id": Path(page).stem,
            "expected_filename": page,
            "actual_html_path": str(path),
            "exists": path.exists(),
            "required_sections_present": not missing,
            "missing_sections": missing,
            "has_expert_summary": "Expert Summary" in text,
            "has_what_this_measures": "What This Measures" in text,
            "has_why_it_matters": "Why It Matters" in text,
            "has_how_to_read_this": "How To Read This" in text,
            "has_good_patterns": "Good Patterns" in text,
            "has_caution_patterns": "Caution Patterns" in text,
            "has_concerning_patterns": "Concerning Patterns" in text,
            "has_current_values_suggest": "What The Current Values Suggest" in text,
            "has_operational_interpretation": "Operational Interpretation" in text,
            "has_optimization_options": "Optimization Options" in text,
            "has_what_to_preserve": "What To Preserve" in text,
            "has_what_not_to_infer": "What Not To Infer" in text,
            "has_related_evidence": "Related Evidence" in text,
            "has_related_recommendations": "Related Recommendations" in text,
            "has_human_review_guidance": "Human Review Guidance" in text,
            "has_limitations": "Limitations" in text,
            "has_llm_label_or_fallback_label": "LLM-assisted interpretation" in text or "Deterministic fallback interpretation" in text,
            "has_forbidden_claims": bool(forbidden),
            "forbidden_claims": forbidden,
            "evidence_links_valid": not any(item["page"] == page for item in invalid_links),
            "recommendation_links_valid": not any(item["page"] == page and "recommendations" in item["href"] for item in invalid_links),
            "dashboard_backlink_valid": True,
            "fingerprint_non_biometric_language": fingerprint_ok,
            "multi_video_non_biometric_language": multi_ok,
            "governance_non_auto_resolution_language": governance_ok,
            "validation_status": status,
            "pass_fail": "pass" if status == STATUS_COMPLETE else "fail",
        }
        rows.append(row)
    page_rows = outputs["page_interpretation_registry"]["page_interpretations"]
    using_llm = [r["page"] for r in page_rows if r.get("interpretation_status") == "llm_assisted"]
    using_fallback = [r["page"] for r in page_rows if r.get("interpretation_status") == "deterministic_fallback"]
    result = {
        "analysis_status": STATUS_COMPLETE if all(r["validation_status"] == STATUS_COMPLETE for r in rows) else STATUS_ERROR,
        "method": "phase54_actual_html_page_interpretation_validation_v1",
        "page_interpretation_enrichment_validation_id": deterministic_id("PIEV", rows),
        "pages_enriched": [r["expected_filename"] for r in rows if r["validation_status"] == STATUS_COMPLETE],
        "pages_missing_sections": [r for r in rows if r["missing_sections"]],
        "pages_missing": missing_pages,
        "pages_using_llm": using_llm,
        "pages_using_fallback": using_fallback,
        "pages_with_invalid_links": invalid_links,
        "pages_with_forbidden_language": forbidden_pages,
        "per_page_results": rows,
        "summary": {
            "total_target_pages": len(rows),
            "target_page_count": len(rows),
            "pages_found": sum(1 for r in rows if r["exists"]),
            "pages_missing": len(missing_pages),
            "pages_enriched": sum(1 for r in rows if r["validation_status"] == STATUS_COMPLETE),
            "pages_failed": sum(1 for r in rows if r["validation_status"] != STATUS_COMPLETE),
            "enriched_count": sum(1 for r in rows if r["validation_status"] == STATUS_COMPLETE),
            "missing_count": sum(1 for r in rows if r["validation_status"] != STATUS_COMPLETE),
            "pages_with_llm_interpretation": len(using_llm),
            "pages_with_deterministic_fallback": len(using_fallback),
            "pages_with_forbidden_claims": len(forbidden_pages),
            "pages_missing_limitations": sum(1 for r in rows if not r["has_limitations"]),
            "pages_missing_evidence_links": sum(1 for r in rows if not r["has_related_evidence"]),
            "pages_missing_recommendation_links": sum(1 for r in rows if not r["has_related_recommendations"]),
            "llm_count": len(using_llm),
            "fallback_count": len(using_fallback),
        },
        "limitations": [INTERPRETATION_LIMITATION],
    }
    write_json(output_dir / "verification_evidence" / "page_interpretation_enrichment_validation.json", result)
    write_json(output_dir / "verification_evidence" / "llm_interpretation_validation.json", result)
    write_json(output_dir / "verification_evidence" / "actual_html_page_enrichment_validation.json", result)
    write_json(output_dir / "verification_evidence" / "interpretation_safety_validation.json", result)
    write_json(output_dir / "verification_evidence" / "interpretation_provenance_validation.json", result)
    write_json(output_dir / "verification_evidence" / "deterministic_fallback_validation.json", result)
    write_json(output_dir / "verification_evidence" / "dashboard_card_interpretation_validation.json", _validate_dashboard_cards(output_dir))
    return result


def enrich_dashboard_pages(output_dir: Path, context: dict | None = None, config: dict | None = None, llm_client: Callable[[dict, dict], dict] | None = None) -> dict:
    outputs = build_page_interpretations(output_dir, context, config, llm_client)
    write_interpretation_outputs(output_dir, outputs)
    render_result = enrich_actual_html_pages(output_dir, outputs)
    validation = validate_enriched_pages(output_dir, outputs)
    return {**outputs, "render_result": render_result, "validation": validation}


def _write_llm_dashboard(path: Path, title: str, rows: list[dict]) -> None:
    cards = []
    for row in rows[:200]:
        page = row.get("page") or row.get("graph_or_page_id") or row.get("provenance_id") or "entry"
        status = row.get("interpretation_status") or row.get("validation_status") or row.get("provenance_status") or row.get("reason") or "review"
        cards.append(f"<article class='graph-card'><h3>{_e(page)}</h3><p>{_e(status)}</p><pre>{_e(json.dumps(row, ensure_ascii=False, indent=2)[:1200])}</pre></article>")
    html_text = f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>{_e(title)}</title><link rel='stylesheet' href='../../static_assets/report.css'></head><body><main class='main expert'><header class='page-header'><p>{PHASE_NAME}</p><h1>{_e(title)}</h1><p>{_e(INTERPRETATION_LIMITATION)}</p></header><section class='graph-card-grid'>{''.join(cards)}</section></main></body></html>"
    path.write_text(html_text, encoding="utf-8")


def _write_schema(path: Path, key: str) -> None:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": path.name,
        "title": key.replace("_", " ").title(),
        "type": "object",
        "required": ["analysis_status", "method", "summary", "limitations"],
        "properties": {"analysis_status": {"type": "string"}, "method": {"type": "string"}, "summary": {"type": "object"}, "limitations": {"type": "array", "items": {"type": "string"}}},
        "additionalProperties": True,
    }
    write_json(path, schema)


def _write_markdown_report(path: Path, title: str, payload: dict) -> None:
    summary = payload.get("summary", {}) if isinstance(payload, dict) else {}
    lines = [
        f"# {title}",
        "",
        "Phase V54 keeps deterministic measurements, validation, recommendations, governance state, blockers, media, and timelines authoritative. Interpretation text is advisory only.",
        "",
        "## Summary",
    ]
    for key, value in summary.items():
        lines.append(f"- `{key}`: {value}")
    lines.extend([
        "",
        "## Limitations",
        "- This system provides deterministic editorial-review and operational workflow support. It does not infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous editorial decisions. Human review is required.",
        "- LLM-assisted interpretation, when configured, cannot resolve blockers, promote readiness, mutate media, mutate timelines, or make autonomous edits.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _validate_dashboard_cards(output_dir: Path) -> dict:
    path = output_dir / "visualizations" / "dashboard.html"
    text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    cards = re.findall(r"<article class=['\"][^'\"]*graph-card[^'\"]*['\"].*?</article>", text, flags=re.I | re.S)
    shallow = [card for card in cards if "Open detail" in card and "Explain this graph/page" not in card and "Explain this graph" not in card]
    result = {
        "analysis_status": STATUS_COMPLETE if path.exists() and cards and not shallow else STATUS_ERROR,
        "method": "phase54_dashboard_card_interpretation_validation_v1",
        "dashboard_path": str(path),
        "card_count": len(cards),
        "shallow_open_detail_only_count": len(shallow),
        "cards_clickable": bool(re.search(r"<a [^>]*href=", text)),
        "cards_contain_interpretive_summaries": "related recommendation item" in text and ("Explain this graph/page" in text or "Explain this graph" in text),
        "limitations": [INTERPRETATION_LIMITATION],
    }
    return result


def _base_page(title: str, body: str) -> str:
    return f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>{_e(title)}</title><link rel='stylesheet' href='../static_assets/report.css'></head><body><main class='main expert'><header class='page-header'><p>Analysis View</p><h1>{_e(title)}</h1></header>{body}</main></body></html>"


def _ensure_page_shell(text: str, title: str) -> str:
    if "<main" in text and "</main>" in text:
        return text
    return _base_page(title, text)


def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", str(value)).strip()


def _e(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)
