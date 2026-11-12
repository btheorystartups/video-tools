"""Semantic-layer readiness scaffolding without semantic inference."""

from __future__ import annotations

from pathlib import Path

from stability import STATUS_COMPLETE, utc_now_iso, write_json


def build_semantic_readiness(output_dir: Path) -> dict:
    report = {
        "validation_status": STATUS_COMPLETE,
        "generated_at_utc": utc_now_iso(),
        "semantic_readiness_version": "1.0",
        "semantic_ready_components": [
            "transcript segments with deterministic segment IDs",
            "argument graph nodes and edges",
            "recommendations with affected segment IDs",
            "revision candidates with proposal-only lineage",
            "evidence consensus summaries",
        ],
        "nonsemantic_authority_components": [
            "scene_segments.json",
            "consensus/transition_confidence.json",
            "revision_graph/revision_graph.json",
            "integrity/reference_validation.json",
            "integrity/graph_consistency.json",
        ],
        "future_embedding_hook_points": [
            {"artifact": "transcript.json", "unit": "transcript_segment", "status": "interface_placeholder_only"},
            {"artifact": "scene_segments.json", "unit": "scene_segment", "status": "interface_placeholder_only"},
            {"artifact": "discourse/argument_graph.json", "unit": "argument_node", "status": "interface_placeholder_only"},
            {"artifact": "recommendations.json", "unit": "recommendation", "status": "interface_placeholder_only"},
        ],
        "future_paraphrase_hook_points": [
            {"artifact": "reports/*.md", "purpose": "future human-readable summaries", "status": "not_implemented"},
            {"artifact": "discourse/narrative_memory.json", "purpose": "future theme paraphrase grouping", "status": "not_implemented"},
        ],
        "semantic_risk_summary": [
            "Future semantic systems must never override deterministic IDs or lineage without explicit provenance.",
            "Semantic scores must be advisory evidence, not source-of-truth graph structure.",
            "Embedding/vector artifacts must remain optional and regenerable.",
        ],
        "semantic_boundary_rules": {
            "deterministic_authority": "IDs, graph edges, artifact hashes, schema validation, and revision lineage remain deterministic.",
            "semantic_advisory_only": "Future embeddings may suggest similarity or grouping but cannot silently rewrite artifacts.",
            "evidence_precedence": [
                "source media metadata and hashes",
                "explicit transcript timings and segment IDs",
                "schema-valid deterministic artifacts",
                "cross-artifact integrity validators",
                "optional future semantic annotations",
            ],
            "override_policy": "Semantic annotations require explicit provenance, confidence, and non-destructive sidecar artifacts.",
        },
        "limitations": [
            "Semantic readiness outputs do not perform semantic inference. They define future extension boundaries and evidence-precedence rules for optional future semantic systems.",
            "No embeddings, vector databases, CLIP, LLM calls, or cloud APIs are used.",
        ],
    }
    integrity = Path(output_dir) / "integrity"
    integrity.mkdir(exist_ok=True)
    write_json(integrity / "semantic_readiness.json", report)
    return report


def write_semantic_readiness_report(output_dir: Path, report: dict) -> None:
    reports = Path(output_dir) / "reports"
    reports.mkdir(exist_ok=True)
    lines = [
        "# Semantic Readiness Report",
        "",
        "Semantic readiness outputs do not perform semantic inference. They define future extension boundaries and evidence-precedence rules for optional future semantic systems.",
        "",
        f"- Ready components: `{len(report.get('semantic_ready_components') or [])}`",
        f"- Future embedding hook points: `{len(report.get('future_embedding_hook_points') or [])}`",
        f"- Future paraphrase hook points: `{len(report.get('future_paraphrase_hook_points') or [])}`",
        "",
        "## Boundary Rules",
        "",
    ]
    for key, value in (report.get("semantic_boundary_rules") or {}).items():
        lines.append(f"- `{key}`: {value}")
    (reports / "semantic_readiness_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
