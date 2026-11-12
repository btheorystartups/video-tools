"""Export deterministic reviewer worksheets in JSON, CSV, and Markdown."""

from __future__ import annotations

import csv
import io

from review_import_templates import build_template, template_fields
from review_operational_common import review_artifact
from stability import deterministic_id


def _example_from_annotation(row: dict, kind: str) -> dict:
    base = {
        "import_item_id": "",
        "reviewer_id": "local_reviewer_placeholder",
        "source_item_id": row.get("annotation_id"),
        "related_video": row.get("related_video"),
        "related_segment": row.get("related_segment"),
        "related_recommendation": row.get("related_recommendation"),
        "related_blocker": row.get("related_blocker"),
        "reviewer_notes": "",
    }
    if kind == "decision":
        base.update({"decision": "", "decision_rationale": "", "governance_relevance": "review_context_only", "escalation_state": "none", "checkpoint_reference": row.get("related_checkpoint")})
    elif kind == "followup":
        base.update({"followup_state": "open", "required_action": "", "owner_placeholder": "", "escalation_state": "none", "checkpoint_reference": row.get("related_checkpoint")})
    elif kind == "rationale":
        base.update({"rationale_type": row.get("annotation_type"), "rationale_text": "", "governance_relevance": "review_context_only", "checkpoint_reference": row.get("related_checkpoint")})
    else:
        base.update({"annotation_type": row.get("annotation_type"), "severity": row.get("severity"), "review_state": row.get("review_status"), "followup_required": row.get("followup_required"), "escalation_state": "requested" if row.get("escalation_required") else "none", "checkpoint_reference": row.get("related_checkpoint")})
    return base


def render_csv_template(template: dict) -> str:
    output = io.StringIO()
    fields = template.get("fields") or []
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in template.get("examples") or []:
        writer.writerow({field: row.get(field, "") for field in fields})
    return output.getvalue()


def render_markdown_template(template: dict) -> str:
    fields = template.get("fields") or []
    lines = [f"# Reviewer {template.get('template_type', 'response').title()} Template", "", "## Instructions"]
    lines.extend(f"- {item}" for item in template.get("instructions") or [])
    lines.extend(["", "## Fields", ""])
    lines.append("| Field | Value |")
    lines.append("| --- | --- |")
    example = (template.get("examples") or [{}])[0]
    for field in fields:
        lines.append(f"| {field} | {example.get(field, '')} |")
    lines.extend(["", "## Governance Notes"])
    lines.extend(f"- {item}" for item in template.get("governance_notes") or [])
    return "\n".join(str(line) for line in lines) + "\n"


def build_reviewer_worksheet_exports(annotations: dict) -> dict:
    source_rows = (annotations.get("annotations") or [])[:8]
    templates = {}
    for kind in ["annotation", "decision", "followup", "rationale", "escalation"]:
        examples = [_example_from_annotation(row, kind) for row in source_rows[:3]]
        templates[kind] = build_template(kind, examples)
    exports = []
    for kind, template in templates.items():
        exports.append({"template_type": kind, "json_path": f"templates/reviewer_{kind}_template.json", "csv_path": f"templates/reviewer_{kind}_template.csv", "markdown_path": f"templates/reviewer_{kind}_template.md", "field_count": len(template.get("fields") or [])})
    artifact = review_artifact("deterministic_reviewer_worksheet_export_v1")
    artifact.update({"reviewer_worksheet_export_id": deterministic_id("RWX", [row["template_type"] for row in exports]), "templates": templates, "exports": exports, "summary": {"template_count": len(exports)}})
    return artifact
