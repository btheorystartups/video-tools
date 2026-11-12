"""Ingest Markdown review worksheets into deterministic import candidates."""

from __future__ import annotations

from operator_workflow_common import phase39_artifact, stable_row_id
from rich_review_worksheet_parser import parse_rich_review_worksheet


def build_markdown_review_ingestion(markdown_sources: list[dict] | None = None, outputs: dict | None = None) -> dict:
    if not markdown_sources:
        markdown_sources = [_default_source(outputs or {})]
    parsed = [parse_rich_review_worksheet(item.get("text") or "", item.get("source_name") or "worksheet.md") for item in markdown_sources]
    candidates = []
    for parse in parsed:
        metadata = {}
        for section in parse.get("sections") or []:
            if section.get("section_type") == "reviewer_metadata":
                metadata.update(section.get("structured_fields") or {})
        for section in parse.get("sections") or []:
            if section.get("section_type") == "reviewer_metadata":
                continue
            candidates.append({
                "markdown_import_candidate_id": stable_row_id("MDIMP", parse.get("source_name"), section.get("worksheet_section_id")),
                "source_name": parse.get("source_name"),
                "section_type": section.get("section_type"),
                "reviewer_id": metadata.get("reviewer_id") or metadata.get("reviewer") or "local_reviewer_placeholder",
                "source_item_id": (section.get("structured_fields") or {}).get("source_item_id"),
                "rationale_text": section.get("multiline_text"),
                "governance_sensitive": section.get("governance_sensitive"),
                "canonical_section_hash": section.get("canonical_hash"),
            })
    artifact = phase39_artifact("deterministic_markdown_review_ingestion_v1")
    artifact.update({
        "markdown_review_ingestion_id": stable_row_id("MDREVIEW", [row["markdown_import_candidate_id"] for row in candidates]),
        "parsed_worksheets": parsed,
        "import_candidates": candidates,
        "summary": {"worksheet_count": len(parsed), "candidate_count": len(candidates), "governance_sensitive_count": sum(1 for row in candidates if row["governance_sensitive"])},
    })
    return artifact


def _default_source(outputs: dict) -> dict:
    imported = (outputs.get("review_import_registry") or {}).get("imported_items") or []
    first = imported[0] if imported else {}
    text = "\n".join([
        "# Reviewer Metadata",
        "reviewer_id: local_reviewer_placeholder",
        "",
        "# Rationale",
        f"source_item_id: {first.get('source_item_id', 'sample_source_item')}",
        "This multiline rationale preserves reviewer-authored context.",
        "It remains advisory and requires human review.",
        "",
        "# Governance Commentary",
        "Governance review may be required for escalation-sensitive imported notes.",
        "",
        "| field | value |",
        "| --- | --- |",
        "| escalation_state | requested |",
    ])
    return {"source_name": "deterministic_phase39_fixture.md", "text": text}
