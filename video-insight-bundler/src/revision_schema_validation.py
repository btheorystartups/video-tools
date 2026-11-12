"""Formal schema validation for revision and consensus artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from schema_validation import validate_against_schema
from stability import STATUS_COMPLETE, STATUS_ERROR, STATUS_LIMITED, write_json


ARTIFACT_SCHEMAS = {
    "revision_graph/revision_graph.json": "revision_graph.schema.json",
    "revision_graph/revision_candidates.json": "revision_candidates.schema.json",
    "revision_graph/revision_deltas.json": "revision_deltas.schema.json",
    "revision_graph/editorial_constraints.json": "editorial_constraints.schema.json",
    "revision_graph/release_readiness_report.json": "release_readiness_report.schema.json",
    "revision_graph/mutation_safety_contract.json": "mutation_safety_contract.schema.json",
    "revision_graph/branch_comparison_report.json": "branch_comparison_report.schema.json",
    "consensus/evidence_consensus.json": "evidence_consensus.schema.json",
    "consensus/transition_confidence.json": "transition_confidence.schema.json",
}

ID_PATTERNS = {
    "revision_id": re.compile(r"^REV_[a-f0-9]{16}$"),
    "candidate_id": re.compile(r"^CAND_[a-f0-9]{16}$"),
    "delta_id": re.compile(r"^DELTA_[a-f0-9]{16}$"),
    "transition_id": re.compile(r"^TRN_[a-f0-9]{16}$"),
}
CONSENSUS_CLASSES = {"strong_agreement", "moderate_agreement", "weak_agreement", "disagreement", "insufficient_evidence"}
CONFIDENCE_CLASSES = {"high", "moderate", "weak", "ambiguous"}
RELEASE_CLASSES = {"not_ready", "review_ready", "dry_run_ready", "release_candidate"}
MUTATION_CLASSES = {
    "SAFE_ANALYSIS_ONLY",
    "SAFE_METADATA_ONLY",
    "SAFE_REPORT_ONLY",
    "REQUIRES_HUMAN_REVIEW",
    "REQUIRES_RERENDER",
    "REQUIRES_REINSERTION",
    "REQUIRES_TIMELINE_MUTATION",
    "UNSAFE_WITHOUT_BACKUP",
}


def _load_json(path: Path) -> tuple[dict | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:
        return None, str(exc)


def _pattern_error(errors: list[dict], path: str, key: str, value: Any) -> None:
    pattern = ID_PATTERNS.get(key)
    if pattern and value is not None and not pattern.match(str(value)):
        errors.append({"path": path, "message": f"{key} does not match deterministic ID pattern: {value!r}."})


def _custom_checks(rel_path: str, data: dict) -> list[dict]:
    errors: list[dict] = []
    if rel_path.endswith("revision_graph.json") and data.get("status") == "complete":
        root = data.get("root_revision_id")
        _pattern_error(errors, "$.root_revision_id", "revision_id", root)
        state_ids = set()
        for index, state in enumerate(data.get("revision_states") or []):
            rid = state.get("revision_id")
            state_ids.add(rid)
            _pattern_error(errors, f"$.revision_states[{index}].revision_id", "revision_id", rid)
            parent = state.get("parent_revision_id")
            if parent is not None:
                _pattern_error(errors, f"$.revision_states[{index}].parent_revision_id", "revision_id", parent)
            if state.get("root_revision_id") != root:
                errors.append({"path": f"$.revision_states[{index}].root_revision_id", "message": "State root_revision_id does not match graph root."})
        for index, candidate in enumerate(data.get("revision_candidates") or []):
            _pattern_error(errors, f"$.revision_candidates[{index}].candidate_id", "candidate_id", candidate.get("candidate_id"))
            _pattern_error(errors, f"$.revision_candidates[{index}].simulated_revision_id", "revision_id", candidate.get("simulated_revision_id"))
            if candidate.get("proposal_status") != "proposed":
                errors.append({"path": f"$.revision_candidates[{index}].proposal_status", "message": "Candidate must remain proposed."})
            if candidate.get("mutation_safety_class") not in MUTATION_CLASSES:
                errors.append({"path": f"$.revision_candidates[{index}].mutation_safety_class", "message": "Unknown mutation safety class."})
        for index, delta in enumerate(data.get("revision_deltas") or []):
            _pattern_error(errors, f"$.revision_deltas[{index}].delta_id", "delta_id", delta.get("delta_id"))
    if rel_path.endswith("revision_candidates.json"):
        for index, candidate in enumerate(data.get("revision_candidates") or []):
            _pattern_error(errors, f"$.revision_candidates[{index}].candidate_id", "candidate_id", candidate.get("candidate_id"))
            if candidate.get("proposal_status") not in {"proposed", "rejected", "accepted_for_review"}:
                errors.append({"path": f"$.revision_candidates[{index}].proposal_status", "message": "Invalid candidate status."})
            if candidate.get("mutation_safety_class") not in MUTATION_CLASSES:
                errors.append({"path": f"$.revision_candidates[{index}].mutation_safety_class", "message": "Invalid mutation safety enum."})
    if rel_path.endswith("revision_deltas.json"):
        for index, delta in enumerate(data.get("deltas") or []):
            _pattern_error(errors, f"$.deltas[{index}].delta_id", "delta_id", delta.get("delta_id"))
    if rel_path.endswith("release_readiness_report.json"):
        if data.get("release_readiness_class") not in RELEASE_CLASSES:
            errors.append({"path": "$.release_readiness_class", "message": "Invalid release readiness class."})
    if rel_path.endswith("mutation_safety_contract.json"):
        for index, row in enumerate(data.get("candidate_contracts") or []):
            if row.get("mutation_safety_class") not in MUTATION_CLASSES:
                errors.append({"path": f"$.candidate_contracts[{index}].mutation_safety_class", "message": "Invalid mutation safety enum."})
    if rel_path.endswith("evidence_consensus.json"):
        for index, row in enumerate(data.get("consensus_items") or []):
            _pattern_error(errors, f"$.consensus_items[{index}].transition_id", "transition_id", row.get("transition_id"))
            if row.get("consensus_class") not in CONSENSUS_CLASSES:
                errors.append({"path": f"$.consensus_items[{index}].consensus_class", "message": "Invalid consensus class."})
    if rel_path.endswith("transition_confidence.json"):
        for index, row in enumerate(data.get("transitions") or []):
            _pattern_error(errors, f"$.transitions[{index}].transition_id", "transition_id", row.get("transition_id"))
            if row.get("confidence_class") not in CONFIDENCE_CLASSES:
                errors.append({"path": f"$.transitions[{index}].confidence_class", "message": "Invalid confidence class."})
    if rel_path.endswith("editorial_constraints.json"):
        for index, row in enumerate(data.get("constraints") or []):
            if row.get("status") not in {"pass", "warn", "fail", "unavailable"}:
                errors.append({"path": f"$.constraints[{index}].status", "message": "Invalid constraint status."})
    return errors


def validate_revision_artifacts(output_dir: Path, schema_dir: Path) -> dict:
    """Validate revision and consensus artifacts, preserving graceful degradation."""

    results = []
    for rel_path, schema_name in ARTIFACT_SCHEMAS.items():
        artifact_path = output_dir / rel_path
        schema_path = schema_dir / schema_name
        if not artifact_path.exists():
            results.append(
                {
                    "artifact": rel_path,
                    "schema": schema_name,
                    "validation_status": STATUS_LIMITED,
                    "error_count": 1,
                    "errors": [{"path": "$", "message": "Artifact is missing."}],
                }
            )
            continue
        data, load_error = _load_json(artifact_path)
        if load_error or data is None:
            results.append(
                {
                    "artifact": rel_path,
                    "schema": schema_name,
                    "validation_status": STATUS_ERROR,
                    "error_count": 1,
                    "errors": [{"path": "$", "message": f"JSON parse failed: {load_error}"}],
                }
            )
            continue
        if not schema_path.exists():
            schema_report = {
                "validation_status": STATUS_LIMITED,
                "schema_path": str(schema_path),
                "error_count": 1,
                "errors": [{"path": "$", "message": "Schema file is missing."}],
            }
        else:
            schema_report = validate_against_schema(data, schema_path)
        custom_errors = _custom_checks(rel_path, data)
        errors = list(schema_report.get("errors") or []) + custom_errors
        results.append(
            {
                "artifact": rel_path,
                "schema": schema_name,
                "validation_status": STATUS_COMPLETE if not errors else STATUS_ERROR,
                "error_count": len(errors),
                "errors": errors,
            }
        )

    error_count = sum(row["error_count"] for row in results)
    report = {
        "validation_status": STATUS_COMPLETE if error_count == 0 else STATUS_ERROR,
        "artifact_count": len(results),
        "error_count": error_count,
        "results": results,
        "limitations": [
            "Validation uses the bundled standalone JSON Schema subset plus deterministic custom integrity checks.",
            "Missing optional revision artifacts degrade explicitly instead of failing silently.",
        ],
    }
    evidence_dir = output_dir / "verification_evidence"
    evidence_dir.mkdir(exist_ok=True)
    write_json(evidence_dir / "revision_schema_validation.json", report)
    consensus_report = {
        "validation_status": STATUS_COMPLETE if all(row["validation_status"] == STATUS_COMPLETE for row in results if row["artifact"].startswith("consensus/")) else STATUS_ERROR,
        "results": [row for row in results if row["artifact"].startswith("consensus/")],
    }
    write_json(evidence_dir / "consensus_validation.json", consensus_report)
    return report
