"""Provenance reconstruction for corpus readiness and recommendations."""

from __future__ import annotations

from pathlib import Path

from intelligence_common import base_artifact, deterministic_id, read_json
from stability import write_json


def build_provenance_reconstruction(corpus_output_dir: Path, analysis_dirs: list[Path], corpus_outputs: dict) -> dict:
    readiness_links = []
    recommendation_links = []
    for analysis_dir in analysis_dirs:
        readiness = read_json(analysis_dir / "revision_graph" / "release_readiness_report.json")
        recommendations = read_json(analysis_dir / "recommendations.json")
        readiness_links.append(
            {
                "provenance_id": deterministic_id("PROV", str(analysis_dir), "readiness"),
                "analysis_dir": str(analysis_dir),
                "readiness_artifact": "revision_graph/release_readiness_report.json",
                "evidence_artifacts": ["consensus/evidence_consensus.json", "sequence/sequence_summary.json", "comparative/comparative_summary.json", "integrity/artifact_integrity.json"],
                "readiness_score": readiness.get("release_readiness_score"),
                "readiness_class": readiness.get("release_readiness_class"),
            }
        )
        for rec in recommendations.get("recommendations", [])[:50]:
            recommendation_links.append(
                {
                    "provenance_id": deterministic_id("PROVREC", str(analysis_dir), rec.get("issue_type"), rec.get("affected_segment_ids")),
                    "analysis_dir": str(analysis_dir),
                    "issue_type": rec.get("issue_type"),
                    "segment_ids": rec.get("affected_segment_ids") or [],
                    "evidence_references": rec.get("evidence") or [],
                    "artifact_path": "recommendations.json",
                }
            )
    governance = corpus_outputs.get("governance_summary") or {}
    output = base_artifact(method="deterministic_provenance_reconstruction_v1")
    output.update(
        {
            "provenance_reconstruction_id": deterministic_id("PROVSET", [row.get("provenance_id") for row in readiness_links], governance.get("classification")),
            "readiness_to_evidence": readiness_links,
            "recommendation_to_evidence": recommendation_links,
            "corpus_recommendation_to_video_evidence": [
                {
                    "issue_type": row.get("issue_type"),
                    "occurrence_count": row.get("occurrence_count"),
                    "source_artifact": "corpus/corpus_recommendations.json",
                }
                for row in (corpus_outputs.get("corpus_recommendations") or {}).get("recommendations", [])
            ],
            "governance_decision_to_evidence": {
                "classification": governance.get("classification"),
                "evidence_artifacts": ["governance/readiness_arbitration.json", "governance/rc_assessment.json", "audit/audit_trail.json", "verification_evidence/governance_validation.json"],
            },
            "summary": {
                "readiness_link_count": len(readiness_links),
                "recommendation_link_count": len(recommendation_links),
                "provenance_coverage_score": 1.0 if readiness_links else 0.0,
            },
        }
    )
    write_json(corpus_output_dir / "audit" / "provenance_reconstruction.json", output)
    write_json(corpus_output_dir / "audit" / "evidence_traceability.json", {"analysis_status": output["analysis_status"], "method": "deterministic_evidence_traceability_v1", "readiness_to_evidence": readiness_links, "recommendation_to_evidence": recommendation_links, "limitations": output["limitations"]})
    return output
