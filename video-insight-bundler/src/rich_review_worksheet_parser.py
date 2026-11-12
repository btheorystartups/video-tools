"""Parse richer human review worksheets into deterministic JSON."""

from __future__ import annotations

from operator_workflow_common import PHASE39_LIMITATION, phase39_artifact, stable_row_id
from stability import canonical_json, sha256_text

SECTION_ALIASES = {
    "reviewer metadata": "reviewer_metadata",
    "metadata": "reviewer_metadata",
    "annotation": "annotations",
    "annotations": "annotations",
    "decision": "decisions",
    "decisions": "decisions",
    "rationale": "rationale",
    "governance commentary": "governance_commentary",
    "escalation commentary": "escalation_commentary",
    "follow-up commentary": "followup_commentary",
    "followup commentary": "followup_commentary",
}


def parse_rich_review_worksheet(text: str, source_name: str = "local_markdown_worksheet") -> dict:
    sections: dict[str, list[str]] = {}
    current = "unsectioned"
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("#"):
            heading = line.lstrip("#").strip().lower()
            current = SECTION_ALIASES.get(heading, heading.replace(" ", "_") or "unsectioned")
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    rows = []
    for section, lines in sorted(sections.items()):
        content = "\n".join(lines).strip()
        if not content:
            continue
        tables = _extract_tables(lines)
        fields = _extract_fields(lines)
        row = {
            "worksheet_section_id": stable_row_id("WSEC", source_name, section, content),
            "source_name": source_name,
            "section_type": section,
            "multiline_text": content,
            "structured_fields": fields,
            "markdown_tables": tables,
            "governance_sensitive": section in {"governance_commentary", "escalation_commentary"} or "governance" in content.lower() or "escalation" in content.lower(),
            "canonical_hash": sha256_text(canonical_json({"section": section, "content": content, "fields": fields, "tables": tables})),
        }
        rows.append(row)
    artifact = phase39_artifact("deterministic_rich_review_worksheet_parser_v1")
    artifact.update({
        "rich_review_worksheet_parse_id": stable_row_id("WRICH", source_name, [row["canonical_hash"] for row in rows]),
        "source_name": source_name,
        "sections": rows,
        "summary": {
            "section_count": len(rows),
            "table_count": sum(len(row["markdown_tables"]) for row in rows),
            "governance_sensitive_section_count": sum(1 for row in rows if row["governance_sensitive"]),
        },
        "limitations": [PHASE39_LIMITATION],
    })
    return artifact


def _extract_fields(lines: list[str]) -> dict:
    fields = {}
    for line in lines:
        stripped = line.strip().lstrip("-").strip()
        if ":" in stripped and not stripped.startswith("|"):
            key, value = stripped.split(":", 1)
            key = key.strip().lower().replace(" ", "_")
            if key:
                fields[key] = value.strip()
    return dict(sorted(fields.items()))


def _extract_tables(lines: list[str]) -> list[dict]:
    tables = []
    current = []
    for line in lines + [""]:
        if line.strip().startswith("|") and line.strip().endswith("|"):
            current.append(line.strip())
            continue
        if current:
            parsed = _parse_table(current)
            if parsed:
                tables.append(parsed)
            current = []
    return tables


def _parse_table(lines: list[str]) -> dict | None:
    if len(lines) < 2:
        return None
    header = [cell.strip() for cell in lines[0].strip("|").split("|")]
    rows = []
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        rows.append({header[index]: cells[index] if index < len(cells) else "" for index in range(len(header))})
    return {"columns": header, "rows": rows}
