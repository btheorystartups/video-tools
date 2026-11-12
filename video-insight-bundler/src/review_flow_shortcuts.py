"""Static deterministic shortcuts that reduce review navigation friction."""

from __future__ import annotations

from intelligence_common import base_artifact, num
from stability import deterministic_id
from temporal_evidence_index import LIMITATION


def _shortcut(shortcut_id: str, label: str, target_path: str, target_anchor: str, why: str, value: str, next_action: str, evidence_refs: list[str]) -> dict:
    return {
        "shortcut_id": shortcut_id,
        "label": label,
        "target_path": target_path,
        "target_anchor": target_anchor,
        "why_this_shortcut_exists": why,
        "review_value": value,
        "expected_next_action": next_action,
        "evidence_refs": evidence_refs,
        "non_claim_limitation": LIMITATION,
    }


def build_review_flow_shortcuts(temporal_index: dict, traceability: dict, spikes: dict, gatekeeper: dict | None = None) -> dict:
    entries = sorted(temporal_index.get("temporal_evidence_entries") or [], key=lambda row: (-num((row.get("highest_severity_signal") or {}).get("score")), row.get("video_id") or "", row.get("segment_id") or ""))
    recs = sorted(traceability.get("traceability_entries") or [], key=lambda row: (-num(row.get("priority_score")), row.get("recommendation_id") or ""))
    spike_rows = sorted(spikes.get("metric_spikes") or [], key=lambda row: (-num(row.get("spike_score")), row.get("metric_spike_id") or ""))
    shortcuts = []
    if entries:
        entry = entries[0]
        path = f"visualizations/timeline/enhanced_video_timeline_{entry.get('video_id')}.html"
        shortcuts.append(_shortcut(deterministic_id("RFS", "highest_priority_segment", entry.get("segment_id")), "Open highest-priority segment", path, f"segment-{entry.get('segment_id')}", "Highest deterministic severity score in the temporal evidence index.", "Fastest route to the strongest current review signal.", "Inspect segment context and evidence preview.", entry.get("evidence_refs") or []))
        high = next((row for row in entries if row.get("blockers")), entry)
        shortcuts.append(_shortcut(deterministic_id("RFS", "first_tier1", high.get("segment_id")), "Open first Tier 1 blocker", f"visualizations/timeline/enhanced_video_timeline_{high.get('video_id')}.html", f"segment-{high.get('segment_id')}", "Blocker-linked regions should be reviewed before readiness changes.", "Keeps governance blockers visible in timeline context.", "Open governance diagnostics or decision intake if needed.", high.get("evidence_refs") or []))
    if recs:
        rec = recs[0]
        shortcuts.append(_shortcut(deterministic_id("RFS", "highest_impact_rec", rec.get("recommendation_id")), "Open highest-impact recommendation", "visualizations/recommendation_traceability.html", rec.get("recommendation_id"), "Top ranked recommendation by deterministic priority score.", "Shows evidence, lineage, and lowest-risk review path.", "Review drawer and source segment before changing anything.", rec.get("evidence_refs") or []))
        low = next((row for row in recs if "low" in str(row.get("effort_estimate")).lower()), rec)
        shortcuts.append(_shortcut(deterministic_id("RFS", "low_effort_high_benefit", low.get("recommendation_id")), "Open lowest-effort/highest-benefit action", "visualizations/recommendation_priority_dashboard.html", low.get("recommendation_id"), "Combines low effort wording with high priority ordering.", "Useful for triage without implying automatic edits.", "Check overcorrection risk and preserve-as-intentional option.", low.get("evidence_refs") or []))
    for metric, label in [("speech_pacing", "Open most severe pacing spike"), ("rhetorical_pressure", "Open most severe rhetorical pressure region")]:
        spike = next((row for row in spike_rows if row.get("metric_id") == metric), None)
        if spike:
            shortcuts.append(_shortcut(deterministic_id("RFS", metric, spike.get("metric_spike_id")), label, f"visualizations/timeline/enhanced_video_timeline_{spike.get('video_id')}.html", f"segment-{spike.get('segment_id')}", "Metric spike exceeds local review threshold.", "Jumps directly to a candidate issue region.", "Inspect the segment and neighboring context.", spike.get("evidence_refs") or []))
    shortcuts.extend(
        [
            _shortcut(deterministic_id("RFS", "compare"), "Open compare view for this video", "visualizations/workstation/compare_readability_index.html", "", "Compare readability pages use aligned local review scales.", "Supports side-by-side review without quality claims.", "Compare directional differences.", ["timeline/temporal_compare_registry.json"]),
            _shortcut(deterministic_id("RFS", "decision_intake"), "Open decision intake template", "visualizations/human_decision_intake.html", "", "Human decisions are required for blocker disposition.", "Keeps governance changes explicit and auditable.", "Record only schema-valid local decisions.", ["review_input/reviewer_decisions.template.json"]),
            _shortcut(deterministic_id("RFS", "governance"), "Open governance reassessment", "visualizations/reassessment_gatekeeper.html", "", "Readiness remains conservative until gatekeeper conditions pass.", "Shows operational blocker state.", "Review unresolved blockers.", ["governance/reassessment_gatekeeper.json"]),
        ]
    )
    output = base_artifact(method="deterministic_review_flow_shortcuts_v1")
    output.update({"review_flow_shortcuts_id": deterministic_id("RFSREG", [row["shortcut_id"] for row in shortcuts]), "shortcuts": shortcuts, "summary": {"shortcut_count": len(shortcuts)}, "limitations": [LIMITATION]})
    return output
