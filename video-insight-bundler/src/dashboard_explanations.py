"""Page-level explanations for expert dashboard pages."""

from __future__ import annotations

from intelligence_common import base_artifact
from stability import deterministic_id


PAGE_SPECS = [
    ("corpus_dashboard", "Corpus Dashboard", "visualizations/corpus_dashboard.html", "corpus", ["What is the corpus status?", "Which review area matters first?"]),
    ("editorial_workbench", "Editorial Workbench", "visualizations/editorial_workbench.html", "editorial", ["Which items require human review?", "Where are the recurring production issues?"]),
    ("compressed_review_queue", "Compressed Review Queue", "visualizations/compressed_review_queue.html", "editorial", ["Which review clusters block progress?", "Which raw items are represented?"]),
    ("next_best_human_actions", "Next Best Human Actions", "visualizations/next_best_human_actions.html", "editorial", ["What should the reviewer do next?"]),
    ("governance_diagnostics", "Governance Diagnostics", "visualizations/governance_diagnostics.html", "governance", ["Which thresholds failed?", "What blocks promotion?"]),
    ("rc_threshold_analysis", "RC Threshold Analysis", "visualizations/rc_threshold_analysis.html", "governance", ["Which gaps remain?", "What is the promotion path?"]),
    ("blocker_analysis", "Blocker Analysis", "visualizations/blocker_analysis.html", "governance", ["Which blockers recur?", "What evidence supports them?"]),
    ("remediation_tracker", "Remediation Tracker", "visualizations/remediation_tracker.html", "remediation", ["What remediation is proposed?", "What requires review?"]),
    ("archetype_remediation", "Archetype Remediation", "visualizations/archetype_remediation.html", "remediation", ["Which recurring archetypes need attention?"]),
    ("governance_review_session", "Governance Review Session", "visualizations/governance_review_session.html", "governance", ["What is the current review session state?"]),
    ("governance_reassessment", "Governance Reassessment", "visualizations/governance_reassessment.html", "governance", ["Did validated decisions change readiness?"]),
    ("governance_reassessment_delta", "Governance Reassessment Delta", "visualizations/governance_reassessment_delta.html", "governance", ["Why did readiness change or remain capped?"]),
    ("reviewer_decision_support", "Reviewer Decision Support", "visualizations/reviewer_decision_support.html", "governance", ["Which dispositions are plausible?", "What evidence is needed?"]),
    ("review_navigation_index", "Review Navigation Index", "visualizations/review_navigation_index.html", "workbench", ["Where should reviewers click next?"]),
    ("human_decision_intake", "Human Decision Intake", "visualizations/human_decision_intake.html", "governance", ["Were local decisions loaded?"]),
    ("decision_validation", "Decision Validation", "visualizations/decision_validation.html", "governance", ["Which human decisions are schema-valid?"]),
    ("decision_reconciliation", "Decision Reconciliation", "visualizations/decision_reconciliation.html", "governance", ["Which valid decisions affect blockers?"]),
    ("governance_ledger", "Governance Ledger", "visualizations/governance_ledger.html", "governance", ["What decision events are auditable?"]),
    ("reassessment_gatekeeper", "Reassessment Gatekeeper", "visualizations/reassessment_gatekeeper.html", "governance", ["Can reassessment proceed?"]),
]


def build_dashboard_explanation_catalog(graph_index: dict | None = None) -> dict:
    details = [row.get("detail_page_path") for row in (graph_index or {}).get("graph_interpretations", [])]
    pages = []
    for page_id, title, path, subsystem, questions in PAGE_SPECS:
        pages.append({
            "page_id": page_id,
            "page_title": title,
            "page_path": path,
            "subsystem": subsystem,
            "purpose": f"Explain and prioritize deterministic {subsystem} review artifacts for expert human review.",
            "primary_questions_answered": questions,
            "key_metrics": ["readiness_score", "review_queue_tier", "governance_threshold_gap"] if subsystem == "governance" else ["rhetorical_pressure", "topic_drift", "visual_reset_frequency"],
            "how_to_use_this_page": ["Read the status summary first.", "Open detail pages for graph interpretation.", "Use evidence links before making production or editing changes."],
            "good_signs": ["Stable evidence, low unresolved blocker count, and clear linked artifacts."],
            "warning_signs": ["Tier 1 blockers, failed thresholds, high pressure, or weak continuity evidence."],
            "expert_review_tips": ["Separate deterministic evidence from creative judgment.", "Document false positives or accepted risk in the local intake files."],
            "linked_detail_pages": details[:8] if page_id in {"corpus_dashboard", "editorial_workbench"} else details,
            "limitations": ["This page is a deterministic editorial-review aid. It does not mutate media, predict viewer behavior, infer identity, recognize faces, or diagnose emotion."],
            "evidence_refs": ["dashboard/graph_interpretation_index.json", "dashboard/visualization_catalog.json"],
        })
    output = base_artifact(method="deterministic_dashboard_explanations_v1")
    output.update({
        "dashboard_explanation_catalog_id": deterministic_id("DEXP", [row["page_id"] for row in pages]),
        "page_explanations": pages,
        "facial_identity_limitation": "The system does not perform face recognition, identity analysis, demographic inference, gaze tracking, or facial emotion recognition. Visual analysis is limited to deterministic frame, shot, composition, motion, and continuity proxies.",
        "summary": {"page_explanation_count": len(pages)},
    })
    return output
