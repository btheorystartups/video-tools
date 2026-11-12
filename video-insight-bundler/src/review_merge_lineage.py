"""Review merge lineage for imported reviewer state."""

from __future__ import annotations

from review_import_templates import IMPORT_LIMITATION
from review_operational_common import review_artifact
from stability import deterministic_id


def build_review_merge_lineage(import_registry: dict, merge_results: dict, conflicts: dict, reconciliation_registry: dict) -> dict:
    conflict_by_item = {}
    for conflict in conflicts.get("conflicts") or []:
        for item_id in conflict.get("conflicting_items") or []:
            conflict_by_item.setdefault(item_id, []).append(conflict.get("conflict_id"))
    pass_id = ((reconciliation_registry.get("reconciliation_passes") or [{}])[0]).get("reconciliation_pass_id")
    imports = {row.get("import_item_id"): row for row in import_registry.get("imported_items") or []}
    rows = []
    for result in merge_results.get("merge_results") or []:
        item = imports.get(result.get("import_item_id")) or {}
        rows.append({"lineage_id": deterministic_id("MLIN", result.get("merge_result_id"), pass_id), "source_import": item.get("import_batch_id"), "original_artifact": item.get("source_item_id"), "affected_review_items": [value for value in [item.get("source_item_id"), item.get("related_recommendation"), item.get("related_blocker")] if value], "reconciliation_pass": pass_id, "merge_outcome": result.get("reconciliation_outcome"), "resulting_operational_state": "unchanged_append_only_recorded", "unresolved_conflicts": conflict_by_item.get(result.get("import_item_id"), [])})
    artifact = review_artifact("deterministic_review_merge_lineage_v1")
    artifact["limitations"] = [IMPORT_LIMITATION]
    artifact.update({"review_merge_lineage_id": deterministic_id("MLINREG", [row["lineage_id"] for row in rows]), "lineage_entries": rows, "summary": {"lineage_entry_count": len(rows), "entries_with_unresolved_conflicts": sum(1 for row in rows if row["unresolved_conflicts"])}})
    return artifact
