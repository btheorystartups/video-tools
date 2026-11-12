"""Revision and artifact lineage validation."""

from __future__ import annotations

from pathlib import Path

from reference_validation import read_json
from stability import STATUS_COMPLETE, STATUS_ERROR, utc_now_iso, write_json


def validate_lineage(output_dir: Path) -> dict:
    root = Path(output_dir)
    graph = read_json(root / "revision_graph" / "revision_graph.json")
    states = graph.get("revision_states") or []
    candidates = graph.get("revision_candidates") or []
    known = {row.get("revision_id") for row in states if row.get("revision_id")}
    root_revision_id = graph.get("root_revision_id")
    issues = []
    roots = [row for row in states if not row.get("parent_revision_id")]
    if len(roots) != 1:
        issues.append({"kind": "root_revision", "reason": "Expected exactly one root revision.", "count": len(roots)})
    elif roots[0].get("revision_id") != root_revision_id:
        issues.append({"kind": "root_revision", "reason": "Root revision ID does not match graph root_revision_id."})
    for state in states:
        parent = state.get("parent_revision_id")
        if parent and parent not in known:
            issues.append({"kind": "parent_revision", "revision_id": state.get("revision_id"), "parent_revision_id": parent, "reason": "Parent revision is missing."})
        if state.get("root_revision_id") and state.get("root_revision_id") != root_revision_id:
            issues.append({"kind": "root_consistency", "revision_id": state.get("revision_id"), "reason": "State root_revision_id differs from graph root."})
        for artifact in state.get("inherited_artifacts") or []:
            if artifact not in (state.get("input_artifact_hashes") or {}):
                issues.append({"kind": "artifact_inheritance", "revision_id": state.get("revision_id"), "artifact": artifact, "reason": "Inherited artifact lacks input hash."})
    candidate_revision_ids = {row.get("simulated_revision_id") for row in candidates}
    state_ids = {row.get("revision_id") for row in states}
    for candidate in candidates:
        if candidate.get("parent_revision_id") != root_revision_id:
            issues.append({"kind": "candidate_parent", "candidate_id": candidate.get("candidate_id"), "reason": "Candidate parent does not match root revision."})
        if candidate.get("simulated_revision_id") not in state_ids:
            issues.append({"kind": "candidate_state", "candidate_id": candidate.get("candidate_id"), "reason": "Candidate simulated revision has no matching state."})
    missing_candidate_states = sorted(candidate_revision_ids - state_ids)
    for revision_id in missing_candidate_states:
        issues.append({"kind": "candidate_state", "revision_id": revision_id, "reason": "Simulated revision ID is not in revision_states."})
    score = round(max(0.0, 1.0 - len(issues) / max(len(states) + len(candidates), 1)), 3)
    report = {
        "validation_status": STATUS_COMPLETE if not issues else STATUS_ERROR,
        "generated_at_utc": utc_now_iso(),
        "lineage_consistency_score": score,
        "root_revision_id": root_revision_id,
        "revision_state_count": len(states),
        "candidate_count": len(candidates),
        "lineage_issues": issues,
        "deterministic_id_stability": {
            "revision_ids_present": sorted(value for value in known if value),
            "candidate_ids_present": sorted(row.get("candidate_id") for row in candidates if row.get("candidate_id")),
            "status": "stable_within_artifact_set" if not issues else "inconsistent_references_detected",
        },
        "migration_compatibility": "Lineage uses explicit versioned artifacts and non-destructive migration scaffolding.",
        "limitations": [
            "ID stability is validated within the generated artifact set; historical run comparison requires retained prior manifests.",
            "Lineage validation does not apply or simulate edits.",
        ],
    }
    integrity = root / "integrity"
    integrity.mkdir(exist_ok=True)
    write_json(integrity / "lineage_validation.json", report)
    return report


def write_lineage_report(output_dir: Path, report: dict) -> None:
    reports = Path(output_dir) / "reports"
    reports.mkdir(exist_ok=True)
    lines = [
        "# Lineage Validation Report",
        "",
        f"- Score: `{report.get('lineage_consistency_score')}`",
        f"- Root revision: `{report.get('root_revision_id')}`",
        f"- Revision states: `{report.get('revision_state_count')}`",
        f"- Candidates: `{report.get('candidate_count')}`",
        "",
        "## Issues",
        "",
    ]
    if report.get("lineage_issues"):
        for issue in report["lineage_issues"][:50]:
            lines.append(f"- `{issue.get('kind')}`: {issue.get('reason')}")
    else:
        lines.append("- No lineage consistency issues detected.")
    (reports / "lineage_validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
