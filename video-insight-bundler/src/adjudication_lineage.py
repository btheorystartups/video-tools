"""Append-only adjudication lineage."""

from __future__ import annotations

from reviewer_adjudication import adjudication_artifact
from review_operational_common import stable_timestamp
from stability import deterministic_id


def build_adjudication_lineage(import_registry: dict, reconciliation_registry: dict, conflicts: dict, reviewer_adjudication_registry: dict, consensus_workflow_registry: dict) -> dict:
    imports_by_item = {row.get("import_item_id"): row for row in import_registry.get("imported_items") or []}
    adjudications = {row.get("conflict_id"): row for row in reviewer_adjudication_registry.get("adjudications") or []}
    consensus = {row.get("conflict_id"): row for row in consensus_workflow_registry.get("consensus_workflows") or []}
    pass_id = ((reconciliation_registry.get("reconciliation_passes") or [{}])[0]).get("reconciliation_pass_id")
    rows = []
    for conflict in conflicts.get("conflicts") or []:
        imports = [imports_by_item.get(item_id) or {} for item_id in conflict.get("conflicting_items") or []]
        lineage_id = deterministic_id("ALIN", conflict.get("conflict_id"), pass_id)
        rows.append(
            {
                "lineage_id": lineage_id,
                "timestamp": stable_timestamp(lineage_id),
                "conflict_id": conflict.get("conflict_id"),
                "lineage_steps": [
                    {"step": "import", "refs": [item.get("import_item_id") for item in imports if item.get("import_item_id")]},
                    {"step": "reconciliation", "refs": [pass_id]},
                    {"step": "conflict", "refs": [conflict.get("conflict_id")]},
                    {"step": "adjudication", "refs": [(adjudications.get(conflict.get("conflict_id")) or {}).get("adjudication_id")]},
                    {"step": "consensus", "refs": [(consensus.get(conflict.get("conflict_id")) or {}).get("consensus_workflow_id")]},
                    {"step": "final_operational_state", "refs": ["unchanged_pending_human_resolution"]},
                ],
                "append_only": True,
                "lineage_mutated": False,
            }
        )
    artifact = adjudication_artifact("deterministic_adjudication_lineage_v1")
    artifact.update({"adjudication_lineage_id": deterministic_id("ALINREG", [row["lineage_id"] for row in rows]), "lineage_entries": rows, "summary": {"lineage_entry_count": len(rows), "append_only": True}})
    return artifact
