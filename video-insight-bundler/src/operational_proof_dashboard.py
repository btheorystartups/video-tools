"""Deterministic operational proof registry and dashboard."""

from __future__ import annotations

from phase47_replay_common import phase47_artifact, render_replay_page, stable_row_id


def build_operational_proof_registry(outputs: dict) -> dict:
    proof_sources = [
        ("replay", "deterministic_replay_registry"),
        ("continuity", "continuity_integrity_registry"),
        ("coverage", "replay_coverage_registry"),
        ("accessibility", "accessibility_semantic_registry"),
        ("navigation", "deterministic_navigation_registry"),
    ]
    rows = []
    for proof_type, key in proof_sources:
        registry = outputs.get(key) or {}
        summary = registry.get("summary") or {}
        rows.append(
            {
                "operational_proof_id": stable_row_id("OPR", proof_type, key, summary),
                "proof_type": proof_type,
                "registry_ref": key,
                "summary_ref": summary,
                "proof_status": "available" if registry else "review",
                "human_review_required": True,
            }
        )
    artifact = phase47_artifact("deterministic_operational_continuity_proof_dashboard_v1")
    artifact.update({"operational_proof_registry_id": stable_row_id("OPRREG", [row["operational_proof_id"] for row in rows]), "operational_proof_entries": rows, "summary": {"operational_proof_entry_count": len(rows)}})
    return artifact


def render_operational_proof_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("operational_proof_registry") or {}).get("operational_proof_entries") or []
    return render_replay_page("Operational Proof Dashboard", "operational_proof_dashboard.html", rows, ["proof_type", "registry_ref", "proof_status"], "operational_proof_id", [("Operational proofs", len(rows))])
