"""Provenance records for imported reviewer content."""

from __future__ import annotations

from review_import_templates import IMPORT_LIMITATION
from review_operational_common import review_artifact, stable_timestamp
from stability import deterministic_id


def build_review_import_provenance(import_registry: dict, reconciliation_registry: dict) -> dict:
    pass_id = ((reconciliation_registry.get("reconciliation_passes") or [{}])[0]).get("reconciliation_pass_id")
    rows = []
    for item in import_registry.get("imported_items") or []:
        rows.append({"provenance_id": deterministic_id("IPROV", item.get("import_item_id"), item.get("canonical_hash")), "import_item_id": item.get("import_item_id"), "import_source": "local_reviewer_template", "import_timestamp": item.get("import_timestamp"), "template_version": item.get("template_version"), "import_batch": item.get("import_batch_id"), "reviewer_identifier_placeholder": item.get("reviewer_id"), "imported_artifact_hash": item.get("canonical_hash"), "reconciliation_pass_id": pass_id, "affected_artifacts": ["review_imports/review_import_registry.json", "reconciliation/review_merge_lineage.json"]})
    artifact = review_artifact("deterministic_review_import_provenance_v1")
    artifact["limitations"] = [IMPORT_LIMITATION]
    artifact.update({"review_import_provenance_id": deterministic_id("IPROVREG", [row["provenance_id"] for row in rows]), "provenance_records": rows, "summary": {"provenance_record_count": len(rows)}})
    return artifact
