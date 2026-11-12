"""Guided deterministic review journeys."""

from __future__ import annotations

from intelligence_common import base_artifact
from stability import deterministic_id
from temporal_evidence_index import LIMITATION


JOURNEYS = [
    ("quick_executive_review", "Quick executive review", "10-15 minutes"),
    ("pacing_optimization_review", "Pacing optimization review", "20-30 minutes"),
    ("rhetorical_clarity_review", "Rhetorical clarity review", "25-35 minutes"),
    ("visual_reset_review", "Visual reset review", "15-25 minutes"),
    ("governance_blocker_review", "Governance blocker review", "30-45 minutes"),
    ("recommendation_implementation_review", "Recommendation implementation review", "30-45 minutes"),
    ("segment_level_deep_dive", "Segment-level deep dive", "45-60 minutes"),
    ("rc_readiness_review", "RC readiness review", "30-45 minutes"),
]


def build_review_journey_index(outputs: dict) -> dict:
    rows = []
    for jid, title, estimate in JOURNEYS:
        rows.append(
            {
                "journey_id": jid,
                "title": title,
                "estimated_review_time": estimate,
                "steps": ["Open corpus overview", "Open timeline review", "Inspect highest-severity segment evidence", "Review linked recommendation traceability", "Record human decision if needed"],
                "linked_pages": ["visualizations/corpus_dashboard.html", "visualizations/timeline_review_index.html", "visualizations/temporal_evidence_index.html", "visualizations/recommendation_traceability.html"],
                "required_artifacts": ["timeline/temporal_evidence_index.json", "recommendations/recommendation_traceability.json"],
                "review_questions": ["Which segments require human review?", "Which recommendation has the clearest evidence lineage?", "What should be preserved as intentional?"],
                "expected_decisions": ["review", "defer", "preserve", "prepare non-mutating optimization note"],
                "completion_criteria": "Reviewer can identify source segment evidence and next action without inferring identity, emotion, or viewer behavior.",
                "next_best_action": "Open linked timeline segment context panel.",
                "non_claim_limitation": LIMITATION,
            }
        )
    output = base_artifact(method="deterministic_review_journey_builder_v1")
    output.update({"review_journey_index_id": deterministic_id("RJREG", [row["journey_id"] for row in rows]), "journeys": rows, "summary": {"journey_count": len(rows)}, "limitations": [LIMITATION]})
    return output

