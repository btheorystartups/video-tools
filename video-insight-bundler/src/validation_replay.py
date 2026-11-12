"""Replayable validation index for corpus artifacts."""

from __future__ import annotations

from pathlib import Path

from intelligence_common import base_artifact, deterministic_id, read_json
from stability import STATUS_COMPLETE, STATUS_ERROR, write_json


def build_validation_replay(corpus_output_dir: Path, analysis_dirs: list[Path]) -> dict:
    validations = []
    for analysis_dir in analysis_dirs:
        for rel in [
            "validation_report.json",
            "verification_evidence/temporal_structure_validation.json",
            "verification_evidence/revision_simulation_validation.json",
            "verification_evidence/comparative_validation.json",
            "integrity/dashboard_coverage.json",
            "integrity/reference_validation.json",
        ]:
            data = read_json(analysis_dir / rel)
            validations.append(
                {
                    "validation_replay_id": deterministic_id("VREP", str(analysis_dir), rel),
                    "analysis_dir": str(analysis_dir),
                    "artifact": rel,
                    "validation_status": data.get("validation_status", "missing"),
                    "replay_command_or_function": f"read and validate {rel} using local schema/reference checks",
                }
            )
    corpus_checks = []
    for rel in ["corpus/corpus_index.json", "audit/audit_trail.json", "governance/readiness_arbitration.json"]:
        corpus_checks.append({"artifact": rel, "exists": (corpus_output_dir / rel).exists()})
    output = base_artifact(method="deterministic_validation_replay_v1")
    output.update(
        {
            "validation_replay_id": deterministic_id("VREPLAY", [row.get("validation_replay_id") for row in validations]),
            "validations_run": validations,
            "corpus_checks": corpus_checks,
            "json_parse_check": "replayable_via_python_json_load",
            "schema_check": "replayable_via_schema_validation.validate_against_schema",
            "reference_check": "replayable_via_reference_validation.validate_references",
            "dashboard_link_check": "replayable_via_artifact_integrity.validate_dashboard_coverage",
            "png_html_json_checks": "replayable_via corpus validation utilities",
            "summary": {
                "validation_count": len(validations),
                "missing_or_error_count": sum(1 for row in validations if row.get("validation_status") not in {STATUS_COMPLETE, "limited"}),
                "corpus_check_count": len(corpus_checks),
            },
        }
    )
    output["analysis_status"] = STATUS_COMPLETE if output["summary"]["missing_or_error_count"] == 0 else STATUS_ERROR
    write_json(corpus_output_dir / "audit" / "validation_replay.json", output)
    write_json(corpus_output_dir / "audit" / "artifact_replay_index.json", {"analysis_status": output["analysis_status"], "method": "deterministic_artifact_replay_index_v1", "artifacts": validations, "limitations": output["limitations"]})
    return output
