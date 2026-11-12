"""Deterministic continuity integrity proofing."""

from __future__ import annotations

from phase47_replay_common import continuity_chain_rows, phase47_artifact, render_replay_page, stable_row_id


def build_continuity_integrity_registry(outputs: dict) -> dict:
    rows = []
    for chain in continuity_chain_rows(outputs, 120):
        rows.append(
            {
                "continuity_integrity_id": stable_row_id("CIP", chain.get("chain_id")),
                "chain_id": chain.get("chain_id"),
                "proof_basis": chain.get("proof_basis"),
                "from_node_id": chain.get("from_node_id"),
                "to_node_id": chain.get("to_node_id"),
                "integrity_proof_status": "proved" if chain.get("continuity_status") == "provable" else "review",
                "human_review_required": True,
            }
        )
    artifact = phase47_artifact("deterministic_continuity_integrity_proof_v1")
    artifact.update({"continuity_integrity_registry_id": stable_row_id("CIPREG", [row["continuity_integrity_id"] for row in rows]), "continuity_integrity_entries": rows, "summary": {"continuity_integrity_entry_count": len(rows), "proved_integrity_count": sum(1 for row in rows if row["integrity_proof_status"] == "proved")}})
    return artifact


def render_continuity_integrity_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("continuity_integrity_registry") or {}).get("continuity_integrity_entries") or []
    return render_replay_page("Continuity Integrity Dashboard", "continuity_integrity_dashboard.html", rows, ["chain_id", "proof_basis", "from_node_id", "to_node_id", "integrity_proof_status"], "continuity_integrity_id", [("Integrity proofs", len(rows))])
