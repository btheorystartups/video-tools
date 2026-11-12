"""Human-readable longitudinal summaries for portable exports."""

from __future__ import annotations

from pathlib import Path

from stability import utc_now_iso, write_json
from trend_prioritization import build_trend_priority_registry


def build_longitudinal_summary(package_root: Path, change_report: dict, historical: dict | None) -> dict:
    priorities = build_trend_priority_registry(change_report)
    highlights = {
        "analysis_status": "complete",
        "method": "evolution_highlights_v77",
        "generated_at_utc": utc_now_iso(),
        "highlights": change_report.get("what_matters_most", []),
    }
    report = {
        "analysis_status": "complete",
        "method": "longitudinal_summary_engine_v77",
        "generated_at_utc": utc_now_iso(),
        "summary_questions": {
            "what_changed_since_last_export": change_report.get("what_changed_since_last_export", []),
            "what_matters_most": change_report.get("what_matters_most", []),
            "what_should_reviewers_focus_on": change_report.get("review_focus"),
        },
        "strongest_regressions": [row for row in change_report.get("meaningful_changes", []) if row.get("change_type") == "removed"][:5],
        "strongest_improvements": [row for row in change_report.get("meaningful_changes", []) if row.get("change_type") == "new"][:5],
        "trend_priorities": priorities.get("trend_priorities", [])[:10],
        "summary": {"trend_priority_count": priorities.get("summary", {}).get("trend_priority_count", 0)},
    }
    for rel, payload in [
        ("longitudinal_summary_report.json", report),
        ("trend_priority_registry.json", priorities),
        ("evolution_highlights.json", highlights),
    ]:
        write_json(package_root / rel, payload)
        write_json(package_root / "review" / rel, payload)
    return {"longitudinal_summary_report": report, "trend_priority_registry": priorities, "evolution_highlights": highlights}
