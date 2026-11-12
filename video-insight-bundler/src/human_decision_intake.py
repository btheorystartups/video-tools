"""Create and load deterministic local human decision intake files."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from blocker_disposition import ALLOWED_DISPOSITIONS
from intelligence_common import base_artifact, deterministic_id, read_json
from stability import STATUS_COMPLETE, write_json


DECISION_FIELDS = [
    "decision_id",
    "blocker_id",
    "source_compressed_item_id",
    "disposition",
    "reviewer_name",
    "review_date",
    "decision_confidence",
    "evidence_note",
    "evidence_refs",
    "rationale",
    "follow_up_required",
    "external_review_reference",
    "accepted_risk_reason",
    "false_positive_reason",
    "resolved_reason",
    "deferred_reason",
    "governance_notes",
]


def process_human_decision_intake(output_dir: Path, tier_1_blocker_disposition: dict) -> dict:
    review_dir = output_dir / "review_input"
    review_dir.mkdir(parents=True, exist_ok=True)
    template = build_reviewer_decisions_template(tier_1_blocker_disposition)
    write_json(review_dir / "reviewer_decisions.template.json", template)
    _write_csv_template(review_dir / "reviewer_decisions.template.csv", template)
    _write_md_template(review_dir / "reviewer_decisions.template.md", template)
    _write_readme(review_dir / "reviewer_decisions_readme.md")

    canonical_path = review_dir / "reviewer_decisions.json"
    reviewer_decisions = read_json(canonical_path)
    reviewer_decisions_exists = canonical_path.exists()
    if not reviewer_decisions:
        reviewer_decisions = {
            "analysis_status": STATUS_COMPLETE,
            "method": "deterministic_reviewer_decisions_absent_v1",
            "decisions": [],
            "summary": {"decision_count": 0},
        }
    intake_status = base_artifact(method="deterministic_human_decision_intake_status_v1")
    intake_status.update(
        {
            "human_decision_intake_status_id": deterministic_id("HDI", template.get("reviewer_decisions_template_id"), reviewer_decisions_exists, len(reviewer_decisions.get("decisions") or [])),
            "canonical_reviewer_decisions_ref": "review_input/reviewer_decisions.json",
            "reviewer_decisions_json_exists": reviewer_decisions_exists,
            "template_refs": [
                "review_input/reviewer_decisions.template.json",
                "review_input/reviewer_decisions.template.csv",
                "review_input/reviewer_decisions.template.md",
                "review_input/reviewer_decisions_readme.md",
            ],
            "decision_count": len(reviewer_decisions.get("decisions") or []),
            "status": "loaded_canonical_decisions" if reviewer_decisions_exists else "no_canonical_decisions_found",
            "summary": {
                "reviewer_decisions_json_exists": reviewer_decisions_exists,
                "template_decision_count": len(template.get("decisions") or []),
                "loaded_decision_count": len(reviewer_decisions.get("decisions") or []),
            },
        }
    )
    return {"reviewer_decisions_template": template, "reviewer_decisions": reviewer_decisions, "decision_intake_status": intake_status}


def build_reviewer_decisions_template(tier_1_blocker_disposition: dict) -> dict:
    rows = []
    for blocker in tier_1_blocker_disposition.get("blocker_dispositions", []):
        rows.append(
            {
                "decision_id": deterministic_id("HDEC_TEMPLATE", blocker.get("blocker_id"), blocker.get("source_compressed_item_id")),
                "blocker_id": blocker.get("blocker_id") or "",
                "source_compressed_item_id": blocker.get("source_compressed_item_id") or "",
                "disposition": "proposed",
                "reviewer_name": "",
                "review_date": "",
                "decision_confidence": "",
                "evidence_note": "",
                "evidence_refs": [],
                "rationale": "",
                "follow_up_required": False,
                "external_review_reference": "",
                "accepted_risk_reason": "",
                "false_positive_reason": "",
                "resolved_reason": "",
                "deferred_reason": "",
                "governance_notes": "",
                "template_entry": True,
                "template_note": "Copy this entry into reviewer_decisions.json and replace blanks. Template entries are not valid decisions.",
            }
        )
    artifact = base_artifact(method="deterministic_reviewer_decisions_template_v1")
    artifact.update(
        {
            "reviewer_decisions_template_id": deterministic_id("RDT", [(row.get("blocker_id"), row.get("source_compressed_item_id")) for row in rows]),
            "allowed_dispositions": ALLOWED_DISPOSITIONS,
            "canonical_input_ref": "review_input/reviewer_decisions.json",
            "decisions": rows,
            "summary": {"template_decision_count": len(rows), "template_entries_are_valid_decisions": False},
        }
    )
    return artifact


def _write_csv_template(path: Path, template: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DECISION_FIELDS)
        writer.writeheader()
        for row in template.get("decisions") or []:
            writer.writerow({field: json.dumps(row.get(field)) if field == "evidence_refs" else row.get(field, "") for field in DECISION_FIELDS})


def _write_md_template(path: Path, template: dict) -> None:
    lines = ["# Reviewer Decisions Template", "", "Template entries are not valid decisions until copied to `reviewer_decisions.json` and completed.", ""]
    for row in template.get("decisions") or []:
        lines.extend([f"## {row.get('blocker_id')}", "", f"- source_compressed_item_id: `{row.get('source_compressed_item_id')}`", "- disposition: `proposed`", "- reviewer_name:", "- review_date:", "- rationale:", "- evidence_refs:", ""])
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _write_readme(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Reviewer Decision Intake",
                "",
                "`reviewer_decisions.json` is the only canonical automated intake file.",
                "CSV and Markdown files are deterministic templates for human review convenience.",
                "Human decision intake artifacts are deterministic local governance-review artifacts. They do not apply edits, mutate media, accept risk automatically, classify false positives automatically, or make autonomous release decisions. Only explicit, schema-valid human decisions can influence reassessment.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
