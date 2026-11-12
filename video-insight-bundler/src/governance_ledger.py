"""Deterministic local append-only governance ledger snapshots."""

from __future__ import annotations

from pathlib import Path

from intelligence_common import base_artifact, deterministic_id, read_json
from stability import canonical_json, sha256_text, utc_now_iso


def build_governance_ledger(output_dir: Path, run_manifest: dict, validated_human_decisions: dict, decision_reconciliation: dict, reassessment_gatekeeper: dict) -> dict:
    prior = read_json(output_dir / "governance" / "governance_ledger.json")
    prior_entries = prior.get("ledger_entries") or []
    entries = []
    rec_by_decision = {row.get("decision_id"): row for row in decision_reconciliation.get("reconciled_decisions") or [] if row.get("decision_id")}
    for decision in validated_human_decisions.get("validated_decisions") or []:
        rec = rec_by_decision.get(decision.get("decision_id"), {})
        entry = {
            "ledger_entry_id": deterministic_id("GLEDGER", run_manifest.get("corpus_run_id"), decision.get("decision_id"), rec.get("reconciliation_status")),
            "run_id": run_manifest.get("corpus_run_id"),
            "timestamp": run_manifest.get("generated_at_utc") or utc_now_iso(),
            "event_type": "human_decision_validated",
            "blocker_id": decision.get("blocker_id"),
            "decision_id": decision.get("decision_id"),
            "prior_state": rec.get("prior_disposition"),
            "new_state": rec.get("proposed_new_disposition"),
            "reviewer_name": decision.get("reviewer_name"),
            "evidence_refs": decision.get("evidence_refs") or [],
            "source_artifacts": ["review_input/reviewer_decisions.json", "governance/validated_human_decisions.json", "governance/decision_reconciliation.json"],
            "validation_status": decision.get("validation_status"),
            "reconciliation_status": rec.get("reconciliation_status"),
            "readiness_effect": rec.get("readiness_effect_candidate"),
        }
        entry["deterministic_hash"] = sha256_text(canonical_json(entry))
        entries.append(entry)
    if not entries:
        entry = {
            "ledger_entry_id": deterministic_id("GLEDGER", run_manifest.get("corpus_run_id"), "no_valid_human_decisions"),
            "run_id": run_manifest.get("corpus_run_id"),
            "timestamp": run_manifest.get("generated_at_utc") or utc_now_iso(),
            "event_type": "no_valid_human_decisions",
            "blocker_id": None,
            "decision_id": None,
            "prior_state": None,
            "new_state": None,
            "reviewer_name": None,
            "evidence_refs": [],
            "source_artifacts": ["review_input/reviewer_decisions.json", "governance/validated_human_decisions.json", "governance/reassessment_gatekeeper.json"],
            "validation_status": "no_valid_decisions",
            "reconciliation_status": "no_reconciliation_change",
            "readiness_effect": "cap_remains_active",
        }
        entry["deterministic_hash"] = sha256_text(canonical_json(entry))
        entries.append(entry)

    merged = _merge_entries(prior_entries, entries)
    ledger = base_artifact(method="deterministic_governance_ledger_v1")
    ledger.update(
        {
            "governance_ledger_id": deterministic_id("GLEDGERSET", [(row.get("ledger_entry_id"), row.get("deterministic_hash")) for row in merged]),
            "append_only_mode": "snapshot_preserving_merge",
            "replacement_behavior": "If a prior ledger exists in this output directory, entries are merged by deterministic ledger_entry_id. Force-rerun directory cleanup removes prior snapshots before this module runs.",
            "ledger_entries": merged,
            "summary": {
                "ledger_entry_count": len(merged),
                "new_entry_count": len(entries),
                "prior_entry_count": len(prior_entries),
                "readiness_can_change": reassessment_gatekeeper.get("readiness_can_change"),
            },
        }
    )
    index = base_artifact(method="deterministic_governance_ledger_index_v1")
    index.update(
        {
            "governance_ledger_index_id": deterministic_id("GLEDGERINDEX", [row.get("ledger_entry_id") for row in merged]),
            "ledger_ref": "governance/governance_ledger.json",
            "entries_by_blocker": _by_key(merged, "blocker_id"),
            "entries_by_decision": _by_key(merged, "decision_id"),
            "summary": {"ledger_entry_count": len(merged), "indexed_blocker_count": len(_by_key(merged, "blocker_id"))},
        }
    )
    return {"governance_ledger": ledger, "governance_ledger_index": index}


def _merge_entries(prior_entries: list[dict], entries: list[dict]) -> list[dict]:
    merged = {row.get("ledger_entry_id"): row for row in prior_entries if row.get("ledger_entry_id")}
    for row in entries:
        merged[row.get("ledger_entry_id")] = row
    return sorted(merged.values(), key=lambda row: row.get("ledger_entry_id") or "")


def _by_key(entries: list[dict], key: str) -> dict:
    grouped: dict[str, list[str]] = {}
    for row in entries:
        value = row.get(key)
        if value:
            grouped.setdefault(value, []).append(row.get("ledger_entry_id"))
    return {name: sorted(ids) for name, ids in sorted(grouped.items())}
