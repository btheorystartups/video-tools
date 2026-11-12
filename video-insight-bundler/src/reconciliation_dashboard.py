"""Static dashboard rendering for human review reconciliation."""

from __future__ import annotations

from dashboard_layout import e
from review_import_templates import IMPORT_LIMITATION
from review_operational_common import card_grid, compact_metrics, review_artifact, simple_review_page
from stability import deterministic_id


def build_reconciliation_dashboard_summary(outputs: dict) -> dict:
    merge = outputs.get("review_import_merge_results") or {}
    conflicts = outputs.get("reconciliation_conflicts") or {}
    queue = outputs.get("unresolved_conflict_queue") or {}
    artifact = review_artifact("deterministic_reconciliation_dashboard_v1")
    artifact["limitations"] = [IMPORT_LIMITATION]
    artifact.update({"reconciliation_dashboard_id": deterministic_id("RDASH", merge.get("review_import_merge_results_id"), conflicts.get("reconciliation_conflicts_id")), "metrics": {"imports_processed": (outputs.get("review_import_registry", {}).get("summary") or {}).get("imported_item_count", 0), "imports_rejected": (outputs.get("review_import_validation", {}).get("summary") or {}).get("invalid_import_count", 0), "conflicts_detected": (conflicts.get("summary") or {}).get("conflict_count", 0), "unresolved_conflicts": (queue.get("summary") or {}).get("queue_item_count", 0), "merge_lineage_entries": (outputs.get("review_merge_lineage", {}).get("summary") or {}).get("lineage_entry_count", 0)}, "next_required_manual_review": [row.get("conflict_id") for row in conflicts.get("conflicts") or []], "summary": {"dashboard_pages": 6}})
    return artifact


def render_reconciliation_dashboards(outputs: dict) -> dict[str, str]:
    links = [
        ("Dashboard", "../dashboard.html"),
        ("Review", "../review/review_session_dashboard.html"),
        ("Reconciliation", "reconciliation_dashboard.html"),
        ("Conflicts", "unresolved_conflict_dashboard.html"),
        ("Imported", "imported_review_dashboard.html"),
        ("Diff", "imported_vs_existing_review_diff.html"),
        ("Audit", "reconciliation_audit_dashboard.html"),
        ("Lineage", "review_merge_lineage_dashboard.html"),
    ]
    summary = outputs.get("reconciliation_dashboard") or {}
    metrics = summary.get("metrics") or {}
    limitation_panel = f"<section class='panel'><p>{e(IMPORT_LIMITATION)}</p></section>"
    return {
        "reconciliation_dashboard.html": simple_review_page("Reconciliation Dashboard", "Human Review Import", "reconciliation_dashboard.html", limitation_panel + compact_metrics([(k.replace("_", " ").title(), v) for k, v in metrics.items()]), links),
        "unresolved_conflict_dashboard.html": simple_review_page("Unresolved Conflict Dashboard", "Conflict Queue", "unresolved_conflict_dashboard.html", limitation_panel + card_grid((outputs.get("unresolved_conflict_queue") or {}).get("queue_items") or [], ["conflict_id", "severity", "governance_relevance", "suggested_next_action"], "queue_id"), links),
        "imported_review_dashboard.html": simple_review_page("Imported Review Dashboard", "Import Summary", "imported_review_dashboard.html", limitation_panel + card_grid((outputs.get("review_import_registry") or {}).get("imported_items") or [], ["import_type", "source_item_id", "review_state", "decision", "escalation_state", "reviewer_notes"], "import_item_id"), links),
        "imported_vs_existing_review_diff.html": simple_review_page("Imported Vs Existing Review Diff", "Review Diff", "imported_vs_existing_review_diff.html", limitation_panel + card_grid((outputs.get("imported_vs_existing_review_diff") or {}).get("diffs") or [], ["source_item_id", "existing_review_status", "imported_review_state", "existing_escalation_required", "imported_escalation_state", "change_requires_manual_review"], "diff_id"), links),
        "reconciliation_audit_dashboard.html": simple_review_page("Reconciliation Audit Dashboard", "Merge Audit", "reconciliation_audit_dashboard.html", limitation_panel + card_grid((outputs.get("reconciliation_audit_log") or {}).get("audit_events") or [], ["action_type", "import_item_id", "conflict_id", "merge_outcome", "operational_state_mutated", "audit_note"], "audit_id"), links),
        "review_merge_lineage_dashboard.html": simple_review_page("Review Merge Lineage Dashboard", "Merge Lineage", "review_merge_lineage_dashboard.html", limitation_panel + card_grid((outputs.get("review_merge_lineage") or {}).get("lineage_entries") or [], ["source_import", "original_artifact", "reconciliation_pass", "merge_outcome", "resulting_operational_state", "unresolved_conflicts"], "lineage_id"), links),
    }
