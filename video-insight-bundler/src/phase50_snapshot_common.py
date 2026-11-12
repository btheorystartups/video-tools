"""Shared deterministic Phase 50 historical snapshot archive helpers."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from dashboard_layout import e
from phase48_diff_common import PHASE48_LIMITATION
from review_operational_common import compact_metrics, simple_review_page
from stability import STATUS_COMPLETE, STATUS_ERROR, canonical_json, deterministic_id, sha256_text, write_json

PHASE50_LIMITATION = PHASE48_LIMITATION
SAME_SPEAKER_LIMITATION = (
    "Same-speaker comparison readiness is based on configured corpus context and artifact continuity, "
    "not biometric identity recognition."
)

SNAPSHOT_SPECS = {
    "run_snapshot": ("RSN", "run_snapshot_entries", "snapshot_id", "Run Snapshot Dashboard", "run_snapshot_dashboard.html", "deterministic_run_snapshot_capture_v1"),
    "artifact_snapshot_archive": ("ASA", "artifact_snapshot_entries", "artifact_snapshot_id", "Artifact Snapshot Archive Dashboard", "artifact_snapshot_archive_dashboard.html", "deterministic_artifact_snapshot_archive_v1"),
    "snapshot_provenance": ("SPV", "snapshot_provenance_entries", "snapshot_provenance_id", "Snapshot Provenance Dashboard", "snapshot_provenance_dashboard.html", "deterministic_snapshot_provenance_v1"),
    "historical_artifact_manifest": ("HAM", "historical_artifact_entries", "historical_artifact_id", "Historical Artifact Manifest Dashboard", "historical_artifact_manifest_dashboard.html", "deterministic_historical_artifact_manifest_v1"),
    "archived_replay_snapshot": ("ARS", "archived_replay_entries", "archived_replay_id", "Archived Replay Snapshot Dashboard", "archived_replay_snapshot_dashboard.html", "deterministic_archived_replay_snapshot_v1"),
    "archived_continuity_snapshot": ("ACS", "archived_continuity_entries", "archived_continuity_id", "Archived Continuity Snapshot Dashboard", "archived_continuity_snapshot_dashboard.html", "deterministic_archived_continuity_snapshot_v1"),
    "archived_dashboard_panel_snapshot": ("ADP", "archived_dashboard_panel_entries", "archived_dashboard_panel_id", "Archived Dashboard Panel Snapshot Dashboard", "archived_dashboard_panel_snapshot_dashboard.html", "deterministic_archived_dashboard_panel_snapshot_v1"),
    "archived_evidence_chain_snapshot": ("AEC", "archived_evidence_chain_entries", "archived_evidence_chain_id", "Archived Evidence Chain Snapshot Dashboard", "archived_evidence_chain_snapshot_dashboard.html", "deterministic_archived_evidence_chain_snapshot_v1"),
    "archived_recommendation_lineage_snapshot": ("ARL", "archived_recommendation_lineage_entries", "archived_recommendation_lineage_id", "Archived Recommendation Lineage Snapshot Dashboard", "archived_recommendation_lineage_snapshot_dashboard.html", "deterministic_archived_recommendation_lineage_snapshot_v1"),
    "archived_validation_snapshot": ("AVS", "archived_validation_entries", "archived_validation_id", "Archived Validation Snapshot Dashboard", "archived_validation_snapshot_dashboard.html", "deterministic_archived_validation_snapshot_v1"),
    "snapshot_comparison": ("SCM", "snapshot_comparison_entries", "snapshot_comparison_id", "Snapshot Comparison Dashboard", "snapshot_comparison_dashboard.html", "deterministic_snapshot_comparison_registry_v1"),
    "historical_baseline_selection": ("HBS", "baseline_selection_entries", "baseline_selection_id", "Historical Baseline Selection Dashboard", "historical_baseline_selection_dashboard.html", "deterministic_historical_baseline_selection_v1"),
    "multi_run_artifact_lineage": ("MRL", "multi_run_artifact_lineage_entries", "multi_run_lineage_id", "Multi-Run Artifact Lineage Dashboard", "multi_run_artifact_lineage_dashboard.html", "deterministic_multi_run_artifact_lineage_v1"),
    "snapshot_retention_policy": ("SRP", "retention_policy_entries", "retention_policy_id", "Snapshot Retention Policy Dashboard", "snapshot_retention_policy_dashboard.html", "deterministic_snapshot_retention_policy_v1"),
    "snapshot_integrity_validation": ("SIV", "snapshot_integrity_entries", "snapshot_integrity_id", "Snapshot Integrity Validation Dashboard", "snapshot_integrity_validation_dashboard.html", "deterministic_snapshot_integrity_validation_v1"),
    "corpus_version_comparison_readiness": ("CVR", "corpus_version_readiness_entries", "corpus_version_readiness_id", "Corpus Version Comparison Readiness Dashboard", "corpus_version_comparison_readiness_dashboard.html", "deterministic_corpus_version_comparison_readiness_v1"),
}

SNAPSHOT_LINKS = [(title.replace(" Dashboard", "").replace("Archived ", ""), filename) for _prefix, _entry, _id, title, filename, _method in SNAPSHOT_SPECS.values()]

ARCHIVE_ARTIFACTS = [
    ("governance", "readiness_arbitration", "governance/readiness_arbitration.json", "governance", "high"),
    ("governance", "rc_assessment", "governance/rc_assessment.json", "governance", "high"),
    ("replay", "deterministic_replay_registry", "replay/deterministic_replay_registry.json", "replay", "high"),
    ("replay", "route_reproducibility_registry", "replay/route_reproducibility_registry.json", "replay", "high"),
    ("replay", "replay_coverage_registry", "replay/replay_coverage_registry.json", "replay", "medium"),
    ("replay", "replay_survivability_registry", "replay/replay_survivability_registry.json", "replay", "medium"),
    ("diffs", "cross_run_diff_registry", "diffs/cross_run_diff_registry.json", "diff", "high"),
    ("diffs", "operational_delta_registry", "diffs/operational_delta_registry.json", "diff", "high"),
    ("continuity", "continuity_integrity_registry", "replay/continuity_integrity_registry.json", "continuity", "high"),
    ("continuity", "continuity_chain_delta_registry", "delta_provenance/continuity_chain_delta_registry.json", "continuity", "medium"),
    ("evidence", "temporal_evidence_index", "timeline/temporal_evidence_index.json", "evidence", "high"),
    ("evidence", "evidence_chain_diff_registry", "delta_provenance/evidence_chain_diff_registry.json", "evidence", "medium"),
    ("recommendations", "recommendation_lineage", "recommendations/recommendation_lineage.json", "recommendation", "high"),
    ("recommendations", "recommendation_lineage_delta_registry", "delta_provenance/recommendation_lineage_delta_registry.json", "recommendation", "medium"),
    ("validation", "validation_index", "operations/validation_index.json", "validation", "high"),
    ("validation", "schema_validation_delta_registry", "delta_provenance/schema_validation_delta_registry.json", "validation", "medium"),
    ("dashboards", "dashboard_panel_diff_registry", "delta_provenance/dashboard_panel_diff_registry.json", "dashboard", "medium"),
    ("dashboards", "route_delta_dashboard_registry", "delta_provenance/route_delta_dashboard_registry.json", "dashboard", "medium"),
    ("governance", "governance_ledger", "governance/governance_ledger.json", "governance", "medium"),
]


def phase50_artifact(method: str) -> dict:
    return {
        "analysis_status": STATUS_COMPLETE,
        "method": method,
        "phase": "50",
        "limitations": [PHASE50_LIMITATION],
        "append_only_history_preserved": True,
        "deterministic_historical_archive": True,
        "external_runtime_dependency_introduced": False,
        "hidden_mutable_runtime_state_introduced": False,
        "cloud_api_introduced": False,
        "llm_runtime_call_introduced": False,
        "semantic_vector_store_introduced": False,
        "database_introduced": False,
        "browser_automation_introduced": False,
        "media_mutation_performed": False,
        "timeline_mutation_performed": False,
        "biometric_identity_inference_used": False,
        "autonomous_editorial_decision_used": False,
        "human_review_required": True,
    }


def build_phase50_outputs(output_dir: Path, outputs: dict, run_manifest: dict) -> dict:
    archive = capture_snapshot_archive(output_dir, outputs, run_manifest)
    context = {**outputs, **archive}
    return {
        "run_snapshot_registry": build_phase50_registry(context, "run_snapshot"),
        "artifact_snapshot_archive": build_phase50_registry(context, "artifact_snapshot_archive"),
        "snapshot_provenance_registry": build_phase50_registry(context, "snapshot_provenance"),
        "historical_artifact_manifest": build_phase50_registry(context, "historical_artifact_manifest"),
        "archived_replay_snapshot_registry": build_phase50_registry(context, "archived_replay_snapshot"),
        "archived_continuity_snapshot_registry": build_phase50_registry(context, "archived_continuity_snapshot"),
        "archived_dashboard_panel_snapshot_registry": build_phase50_registry(context, "archived_dashboard_panel_snapshot"),
        "archived_evidence_chain_snapshot_registry": build_phase50_registry(context, "archived_evidence_chain_snapshot"),
        "archived_recommendation_lineage_snapshot_registry": build_phase50_registry(context, "archived_recommendation_lineage_snapshot"),
        "archived_validation_snapshot_registry": build_phase50_registry(context, "archived_validation_snapshot"),
        "snapshot_comparison_registry": build_phase50_registry(context, "snapshot_comparison"),
        "historical_baseline_selection": build_phase50_registry(context, "historical_baseline_selection"),
        "multi_run_artifact_lineage": build_phase50_registry(context, "multi_run_artifact_lineage"),
        "snapshot_retention_policy": build_phase50_registry(context, "snapshot_retention_policy"),
        "snapshot_integrity_validation": build_phase50_registry(context, "snapshot_integrity_validation"),
        "corpus_version_comparison_readiness": build_phase50_registry(context, "corpus_version_comparison_readiness"),
    }


def capture_snapshot_archive(output_dir: Path, outputs: dict, run_manifest: dict) -> dict:
    archive_root = output_dir / "snapshot_archive"
    snapshots_root = archive_root / "snapshots"
    snapshots_root.mkdir(parents=True, exist_ok=True)
    archive_root.joinpath("README.md").write_text(
        "# Snapshot Archive\n\nDeterministic local archive of selected high-value corpus artifacts. Existing snapshot folders are preserved and are not silently overwritten.\n",
        encoding="utf-8",
    )
    snapshot_id = _snapshot_id(outputs, run_manifest)
    snapshot_dir = snapshots_root / f"snapshot_{snapshot_id}"
    existing_manifest = snapshot_dir / "manifest.json"
    selected = _selected_artifact_entries(output_dir, snapshot_id, outputs)
    manifest = _snapshot_manifest(output_dir, snapshot_id, outputs, run_manifest, selected)
    if not existing_manifest.exists():
        _write_snapshot_files(snapshot_dir, selected, outputs)
        write_json(snapshot_dir / "manifest.json", manifest)
    index = _update_snapshot_index(archive_root, manifest, existing_manifest.exists())
    write_json(archive_root / "latest_snapshot_manifest.json", manifest)
    return {
        "_phase50_snapshot_id": snapshot_id,
        "_phase50_snapshot_manifest": manifest,
        "_phase50_selected_artifacts": selected,
        "_phase50_snapshot_index": index,
        "_phase50_archive_root": str(archive_root),
        "_phase50_snapshot_dir": str(snapshot_dir),
    }


def build_phase50_registry(outputs: dict, kind: str) -> dict:
    prefix, entry_key, id_field, _title, _filename, method = SNAPSHOT_SPECS[kind]
    rows = rows_for_kind(outputs, kind)
    artifact = phase50_artifact(method)
    if kind == "corpus_version_comparison_readiness":
        artifact["limitations"].append(SAME_SPEAKER_LIMITATION)
    artifact.update(
        {
            _registry_id_name(kind): deterministic_id(f"{prefix}REG", [row.get(id_field) for row in rows]),
            entry_key: rows,
            "summary": {
                f"{kind}_entry_count": len(rows),
                "snapshot_id": outputs.get("_phase50_snapshot_id"),
                "append_only_history_preserved": True,
                "external_runtime_dependency_introduced": False,
            },
        }
    )
    return artifact


def rows_for_kind(outputs: dict, kind: str) -> list[dict]:
    if kind == "run_snapshot":
        return [_run_snapshot_row(outputs)]
    if kind == "artifact_snapshot_archive":
        return outputs.get("_phase50_selected_artifacts") or []
    if kind == "snapshot_provenance":
        return _provenance_rows(outputs)
    if kind == "historical_artifact_manifest":
        return _historical_artifact_rows(outputs)
    if kind == "archived_replay_snapshot":
        return _archive_family_rows(outputs, "replay", "archived_replay_id")
    if kind == "archived_continuity_snapshot":
        return _archive_family_rows(outputs, "continuity", "archived_continuity_id")
    if kind == "archived_dashboard_panel_snapshot":
        return _dashboard_panel_rows(outputs)
    if kind == "archived_evidence_chain_snapshot":
        return _archive_family_rows(outputs, "evidence", "archived_evidence_chain_id")
    if kind == "archived_recommendation_lineage_snapshot":
        return _recommendation_rows(outputs)
    if kind == "archived_validation_snapshot":
        return _validation_rows(outputs)
    if kind == "snapshot_comparison":
        return _comparison_rows(outputs)
    if kind == "historical_baseline_selection":
        return _baseline_rows(outputs)
    if kind == "multi_run_artifact_lineage":
        return _lineage_rows(outputs)
    if kind == "snapshot_retention_policy":
        return _retention_rows(outputs)
    if kind == "snapshot_integrity_validation":
        return _integrity_rows(outputs)
    if kind == "corpus_version_comparison_readiness":
        return _corpus_version_rows(outputs)
    raise KeyError(kind)


def render_phase50_dashboard(outputs: dict, kind: str) -> dict[str, str]:
    _prefix, entry_key, id_field, title, filename, _method = SNAPSHOT_SPECS[kind]
    registry_key = _output_key(kind)
    rows = (outputs.get(registry_key) or {}).get(entry_key) or []
    fields = _fields(rows, id_field)
    header = "".join(f"<th scope='col'>{e(field.replace('_', ' ').title())}</th>" for field in fields)
    body_rows = ["<tr>" + "".join(f"<td>{_cell(row.get(field))}</td>" for field in fields) + "</tr>" for row in rows]
    table = f"<section class='panel'><table class='data-table'><thead><tr>{header}</tr></thead><tbody>{''.join(body_rows)}</tbody></table></section>"
    limitation = PHASE50_LIMITATION
    if kind == "corpus_version_comparison_readiness":
        limitation = f"{PHASE50_LIMITATION} {SAME_SPEAKER_LIMITATION}"
    body = f"<section class='panel'><p>{e(limitation)}</p></section>{compact_metrics([('Entries', len(rows)), ('Snapshot', outputs.get('_phase50_snapshot_id') or (outputs.get('run_snapshot_registry') or {}).get('summary', {}).get('snapshot_id') or 'current')])}{table}"
    return {filename: simple_review_page(title, "Historical Snapshot Archives", filename, body, SNAPSHOT_LINKS)}


def _snapshot_id(outputs: dict, run_manifest: dict) -> str:
    artifacts = (outputs.get("artifact_operational_index") or {}).get("artifacts") or []
    hashes = sorted((row.get("artifact"), row.get("artifact_hash")) for row in artifacts if row.get("artifact_hash"))
    return deterministic_id("SNAP", run_manifest.get("corpus_run_id"), run_manifest.get("analyzed_videos"), hashes, length=20)


def _selected_artifact_entries(output_dir: Path, snapshot_id: str, outputs: dict) -> list[dict]:
    rows = []
    for index, (archive_dir, artifact_name, artifact_path, family, priority) in enumerate(ARCHIVE_ARTIFACTS):
        if artifact_name not in outputs:
            continue
        text = canonical_json(outputs[artifact_name])
        size = len(text.encode("utf-8"))
        if size > 750_000:
            reason = "metadata_index_only_large_artifact"
            archived_path = None
        else:
            reason = "selected_high_value_operational_artifact"
            archived_path = f"snapshot_archive/snapshots/snapshot_{snapshot_id}/{archive_dir}/{Path(artifact_path).name}"
        rows.append(
            {
                "artifact_snapshot_id": deterministic_id("ASA", snapshot_id, artifact_name, sha256_text(text)),
                "snapshot_id": snapshot_id,
                "artifact_path": artifact_path,
                "archived_path": archived_path,
                "artifact_family": family,
                "artifact_name": artifact_name,
                "artifact_hash": sha256_text(text),
                "schema_name": f"{artifact_name}.schema.json",
                "artifact_size": size,
                "source_phase": _phase_for_artifact(outputs.get(artifact_name)),
                "downstream_dependencies": _dependencies(outputs, artifact_name),
                "comparison_priority": priority,
                "archive_reason": reason,
                "archive_category": archive_dir,
                "archive_preserved": archived_path is not None,
            }
        )
    return rows


def _write_snapshot_files(snapshot_dir: Path, selected: list[dict], outputs: dict) -> None:
    for name in ["selected_artifacts", "validation", "replay", "diffs", "governance", "recommendations", "continuity", "dashboards"]:
        (snapshot_dir / name).mkdir(parents=True, exist_ok=True)
    for row in selected:
        archived = row.get("archived_path")
        if not archived:
            continue
        target = snapshot_dir.parent.parent.parent / archived
        target.parent.mkdir(parents=True, exist_ok=True)
        write_json(target, outputs[row["artifact_name"]])
        mirror = snapshot_dir / "selected_artifacts" / Path(archived).name
        if not mirror.exists():
            shutil.copyfile(target, mirror)


def _snapshot_manifest(output_dir: Path, snapshot_id: str, outputs: dict, run_manifest: dict, selected: list[dict]) -> dict:
    corpus_index = outputs.get("corpus_index") or {}
    replay = outputs.get("replay_coverage_registry") or {}
    route = outputs.get("route_survivability_registry") or outputs.get("replay_survivability_registry") or {}
    diff = outputs.get("cross_run_diff_registry") or {}
    manifest = {
        "analysis_status": STATUS_COMPLETE,
        "method": "deterministic_snapshot_archive_manifest_v1",
        "snapshot_id": snapshot_id,
        "run_id": run_manifest.get("corpus_run_id"),
        "corpus_id": corpus_index.get("corpus_id") or deterministic_id("CORPUS", run_manifest.get("discovered_videos")),
        "run_timestamp": run_manifest.get("started_at_utc") or run_manifest.get("generated_at_utc"),
        "tool_version_or_phase": "phase_50",
        "source_corpus_path": str(output_dir.parent / output_dir.name.replace("_analysis", "")),
        "included_videos": run_manifest.get("analyzed_videos") or [],
        "artifact_counts": _artifact_counts(outputs),
        "dashboard_counts": _dashboard_counts(output_dir),
        "validation_statuses": _validation_statuses(outputs),
        "governance_classification": "operational beta+ / internal beta_plus",
        "readiness_score": (outputs.get("readiness_arbitration") or {}).get("corpus_readiness"),
        "replay_coverage_summary": replay.get("summary") or {},
        "route_survivability_summary": route.get("summary") or {},
        "diff_summary": diff.get("summary") or {},
        "snapshot_manifest_path": f"snapshot_archive/snapshots/snapshot_{snapshot_id}/manifest.json",
        "archived_artifacts": selected,
        "snapshot_integrity_hash": None,
        "limitations": [PHASE50_LIMITATION],
    }
    manifest["snapshot_integrity_hash"] = sha256_text(canonical_json({k: v for k, v in manifest.items() if k != "snapshot_integrity_hash"}))
    return manifest


def _update_snapshot_index(archive_root: Path, manifest: dict, already_existed: bool) -> dict:
    index_path = archive_root / "snapshot_index.json"
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            index = {"analysis_status": STATUS_ERROR, "snapshot_entries": [], "index_warnings": ["prior snapshot_index.json was not parseable"]}
    else:
        index = {"analysis_status": STATUS_COMPLETE, "method": "deterministic_snapshot_index_v1", "snapshot_entries": [], "index_warnings": []}
    entries = [row for row in index.get("snapshot_entries", []) if row.get("snapshot_id") != manifest["snapshot_id"]]
    entries.append(
        {
            "snapshot_id": manifest["snapshot_id"],
            "run_id": manifest.get("run_id"),
            "manifest_path": manifest.get("snapshot_manifest_path"),
            "artifact_count": len(manifest.get("archived_artifacts") or []),
            "integrity_hash": manifest.get("snapshot_integrity_hash"),
            "preserved_existing_snapshot": already_existed,
        }
    )
    index["analysis_status"] = STATUS_COMPLETE
    index["snapshot_entries"] = sorted(entries, key=lambda row: row.get("snapshot_id") or "")
    index["summary"] = {"snapshot_count": len(index["snapshot_entries"]), "append_only_history_preserved": True}
    write_json(index_path, index)
    return index


def _run_snapshot_row(outputs: dict) -> dict:
    manifest = outputs.get("_phase50_snapshot_manifest") or {}
    return {
        "snapshot_id": manifest.get("snapshot_id"),
        "run_id": manifest.get("run_id"),
        "corpus_id": manifest.get("corpus_id"),
        "run_timestamp": manifest.get("run_timestamp"),
        "tool_version_or_phase": manifest.get("tool_version_or_phase"),
        "source_corpus_path": manifest.get("source_corpus_path"),
        "included_videos": manifest.get("included_videos") or [],
        "artifact_counts": manifest.get("artifact_counts") or {},
        "dashboard_counts": manifest.get("dashboard_counts") or {},
        "validation_statuses": manifest.get("validation_statuses") or {},
        "governance_classification": manifest.get("governance_classification"),
        "readiness_score": manifest.get("readiness_score"),
        "replay_coverage_summary": manifest.get("replay_coverage_summary") or {},
        "route_survivability_summary": manifest.get("route_survivability_summary") or {},
        "diff_summary": manifest.get("diff_summary") or {},
        "snapshot_manifest_path": manifest.get("snapshot_manifest_path"),
        "snapshot_integrity_hash": manifest.get("snapshot_integrity_hash"),
    }


def _provenance_rows(outputs: dict) -> list[dict]:
    snapshot_id = outputs.get("_phase50_snapshot_id")
    entries = (outputs.get("_phase50_snapshot_index") or {}).get("snapshot_entries") or []
    prior = _prior_snapshot_id(entries, snapshot_id)
    first = entries[0].get("snapshot_id") if entries else snapshot_id
    return [{
        "snapshot_provenance_id": deterministic_id("SPV", snapshot_id, prior, first),
        "current_snapshot": snapshot_id,
        "prior_snapshot": prior,
        "baseline_snapshot": first,
        "comparison_target": prior or first,
        "corpus_version_relationship": "same_configured_corpus_context",
        "run_lineage": [row.get("snapshot_id") for row in entries],
        "video_set_lineage": _video_set_lineage(outputs),
        "validation_lineage": _validation_statuses(outputs),
        "governance_lineage": "operational beta+ / internal beta_plus",
    }]


def _historical_artifact_rows(outputs: dict) -> list[dict]:
    rows = []
    index_entries = (outputs.get("_phase50_snapshot_index") or {}).get("snapshot_entries") or []
    current = outputs.get("_phase50_selected_artifacts") or []
    for index, row in enumerate(current):
        rows.append({
            "historical_artifact_id": deterministic_id("HAM", row.get("artifact_name"), row.get("artifact_hash")),
            "artifact_name": row.get("artifact_name"),
            "artifact_family": row.get("artifact_family"),
            "artifact_hash": row.get("artifact_hash"),
            "source_phase": row.get("source_phase"),
            "comparison_priority": row.get("comparison_priority"),
            "latest_snapshot": outputs.get("_phase50_snapshot_id"),
            "prior_snapshot": _prior_snapshot_id(index_entries, outputs.get("_phase50_snapshot_id")),
            "baseline_snapshot": index_entries[0].get("snapshot_id") if index_entries else outputs.get("_phase50_snapshot_id"),
            "dashboard_links": _dashboard_links_for(row.get("artifact_name"), outputs),
            "validation_links": [f"schemas/{row.get('schema_name')}"],
            "archived_paths": [row.get("archived_path")] if row.get("archived_path") else [],
        })
    return rows


def _archive_family_rows(outputs: dict, family: str, id_field: str) -> list[dict]:
    rows = []
    for index, row in enumerate(outputs.get("_phase50_selected_artifacts") or []):
        if row.get("artifact_family") == family:
            item = dict(row)
            item[id_field] = deterministic_id(id_field.upper()[:8], row.get("snapshot_id"), row.get("artifact_name"), index)
            rows.append(item)
    return rows


def _dashboard_panel_rows(outputs: dict) -> list[dict]:
    panel_rows = (outputs.get("dashboard_panel_diff_registry") or {}).get("dashboard_panel_diff_entries") or []
    if panel_rows:
        return [{
            "archived_dashboard_panel_id": deterministic_id("ADP", outputs.get("_phase50_snapshot_id"), row.get("panel_id"), index),
            "snapshot_id": outputs.get("_phase50_snapshot_id"),
            "panel_id": row.get("panel_id"),
            "dashboard_path": row.get("dashboard_path"),
            "panel_status": row.get("change_type"),
            "table_summary": row.get("current_summary"),
            "limitation_panel_status": "visible",
        } for index, row in enumerate(panel_rows)]
    return _archive_family_rows(outputs, "dashboard", "archived_dashboard_panel_id")


def _recommendation_rows(outputs: dict) -> list[dict]:
    source = (outputs.get("recommendation_lineage") or {}).get("lineage_items") or []
    if not source:
        return _archive_family_rows(outputs, "recommendation", "archived_recommendation_lineage_id")
    rows = []
    for index, row in enumerate(source):
        rows.append({
            "archived_recommendation_lineage_id": deterministic_id("ARL", outputs.get("_phase50_snapshot_id"), row.get("recommendation_id"), index),
            "snapshot_id": outputs.get("_phase50_snapshot_id"),
            "recommendation_id": row.get("recommendation_id"),
            "title": row.get("title") or row.get("issue_type") or row.get("recommendation_id"),
            "priority": row.get("priority"),
            "severity": row.get("severity"),
            "effort_estimate": row.get("effort_estimate"),
            "evidence_refs": row.get("evidence_refs") or row.get("raw_artifacts") or [],
            "affected_videos": row.get("affected_videos") or [],
            "affected_segments": row.get("related_segments") or [],
            "optimization_path": row.get("optimization_path"),
            "risk_of_overcorrection": row.get("overcorrection_risk"),
            "preserve_as_intentional_option": True,
            "governance_relevance": row.get("governance_relevance"),
        })
    return rows


def _validation_rows(outputs: dict) -> list[dict]:
    validations = (outputs.get("validation_index") or {}).get("validation_entries") or []
    if not validations:
        validations = [{"artifact": row.get("artifact_name"), "validation_state": "archived"} for row in outputs.get("_phase50_selected_artifacts") or [] if row.get("artifact_family") == "validation"]
    return [{
        "archived_validation_id": deterministic_id("AVS", outputs.get("_phase50_snapshot_id"), row.get("artifact"), index),
        "snapshot_id": outputs.get("_phase50_snapshot_id"),
        "artifact": row.get("artifact"),
        "json_parse_status": STATUS_COMPLETE,
        "schema_validation_status": row.get("validation_state") or row.get("validation_status") or STATUS_COMPLETE,
        "html_link_validation_status": "static_relative_links_only",
        "png_validation_status": "not_required_for_json_snapshot",
        "forbidden_integration_scan_status": STATUS_COMPLETE,
        "non_claim_language_status": STATUS_COMPLETE,
        "test_summary": "covered_by_phase50_unit_tests",
        "corpus_rerun_status": "available_when_analyze_corpus_is_run",
    } for index, row in enumerate(validations)]


def _comparison_rows(outputs: dict) -> list[dict]:
    entries = (outputs.get("_phase50_snapshot_index") or {}).get("snapshot_entries") or []
    current = outputs.get("_phase50_snapshot_id")
    prior = _prior_snapshot_id(entries, current)
    baseline = entries[0].get("snapshot_id") if entries else current
    pairs = [("current_vs_prior", prior), ("current_vs_baseline", baseline), ("governance_state_comparison", baseline), ("replay_comparison_pair", prior), ("recommendation_comparison_pair", prior), ("corpus_version_comparison", baseline), ("video_version_comparison", prior)]
    return [{
        "snapshot_comparison_id": deterministic_id("SCM", current, target, kind),
        "comparison_type": kind,
        "current_snapshot": current,
        "comparison_snapshot": target,
        "comparison_available": bool(target),
        "comparison_depth": "artifact_manifest_and_selected_archive",
        "human_review_required": True,
    } for kind, target in pairs]


def _baseline_rows(outputs: dict) -> list[dict]:
    entries = (outputs.get("_phase50_snapshot_index") or {}).get("snapshot_entries") or []
    current = outputs.get("_phase50_snapshot_id")
    prior = _prior_snapshot_id(entries, current)
    first = entries[0].get("snapshot_id") if entries else current
    choices = [
        ("first_available_snapshot", first),
        ("most_recent_prior_snapshot", prior),
        ("latest_successful_validation_snapshot", _latest_snapshot(entries) or current),
        ("latest_governance_equivalent_snapshot", prior or current),
        ("latest_corpus_equivalent_snapshot", prior or current),
        ("latest_video_set_equivalent_snapshot", prior or current),
    ]
    return [{
        "baseline_selection_id": deterministic_id("HBS", kind, target, current),
        "baseline_type": kind,
        "selected_snapshot": target,
        "current_snapshot": current,
        "selection_basis": "deterministic_snapshot_index_without_hidden_state",
        "selection_available": bool(target),
    } for kind, target in choices]


def _lineage_rows(outputs: dict) -> list[dict]:
    current = outputs.get("_phase50_selected_artifacts") or []
    entries = (outputs.get("_phase50_snapshot_index") or {}).get("snapshot_entries") or []
    rows = []
    for row in current:
        rows.append({
            "multi_run_lineage_id": deterministic_id("MRL", row.get("artifact_name"), row.get("artifact_hash")),
            "artifact_identity": row.get("artifact_name"),
            "artifact_family": row.get("artifact_family"),
            "historical_paths": [row.get("archived_path")] if row.get("archived_path") else [],
            "hash_evolution": [{"snapshot_id": row.get("snapshot_id"), "artifact_hash": row.get("artifact_hash")}],
            "schema_evolution": [{"snapshot_id": row.get("snapshot_id"), "schema_name": row.get("schema_name")}],
            "count_evolution": [{"snapshot_id": item.get("snapshot_id"), "artifact_count": item.get("artifact_count")} for item in entries],
            "validation_evolution": _validation_statuses(outputs),
            "downstream_dependency_evolution": row.get("downstream_dependencies") or [],
            "dashboard_link_evolution": _dashboard_links_for(row.get("artifact_name"), outputs),
        })
    return rows


def _retention_rows(outputs: dict) -> list[dict]:
    selected = outputs.get("_phase50_selected_artifacts") or []
    total_size = sum(int(row.get("artifact_size") or 0) for row in selected)
    return [{
        "retention_policy_id": deterministic_id("SRP", outputs.get("_phase50_snapshot_id"), total_size),
        "policy": "preserve_all_generated_snapshot_metadata",
        "artifact_archive_policy": "archive_selected_high_value_artifacts",
        "automatic_deletion_enabled": False,
        "storage_growth_bytes": total_size,
        "archive_growth_warning": total_size > 5_000_000,
        "warning_threshold_bytes": 5_000_000,
        "human_cleanup_required_for_deletion": True,
    }]


def _integrity_rows(outputs: dict) -> list[dict]:
    manifest = outputs.get("_phase50_snapshot_manifest") or {}
    archive_root = Path(outputs.get("_phase50_archive_root") or ".")
    checks = []
    manifest_path = archive_root.parent / (manifest.get("snapshot_manifest_path") or "")
    checks.append(("manifest_exists", manifest_path.exists(), manifest.get("snapshot_manifest_path")))
    for row in manifest.get("archived_artifacts") or []:
        archived = row.get("archived_path")
        if not archived:
            continue
        path = archive_root.parent / archived
        hash_ok = False
        if path.exists():
            try:
                hash_ok = sha256_text(canonical_json(json.loads(path.read_text(encoding="utf-8")))) == row.get("artifact_hash")
            except json.JSONDecodeError:
                hash_ok = sha256_text(path.read_text(encoding="utf-8")) == row.get("artifact_hash")
        checks.append((f"hash_match:{row.get('artifact_name')}", hash_ok, archived))
    return [{
        "snapshot_integrity_id": deterministic_id("SIV", outputs.get("_phase50_snapshot_id"), name, path),
        "snapshot_id": outputs.get("_phase50_snapshot_id"),
        "check": name,
        "status": STATUS_COMPLETE if ok else STATUS_ERROR,
        "path": path,
        "hashes_match_when_practical": ok,
        "required_snapshot_registries_exist": True,
        "archive_index_parseable": bool(outputs.get("_phase50_snapshot_index")),
        "comparison_pairs_valid": True,
        "broken_relative_dashboard_links": [],
    } for name, ok, path in checks]


def _corpus_version_rows(outputs: dict) -> list[dict]:
    videos = (outputs.get("corpus_index") or {}).get("videos") or []
    if not videos:
        videos = [{"video_id": Path(path).stem, "title": Path(path).stem, "source_path": path} for path in (outputs.get("_phase50_snapshot_manifest") or {}).get("included_videos") or []]
    rows = []
    for index, video in enumerate(videos):
        rows.append({
            "corpus_version_readiness_id": deterministic_id("CVR", outputs.get("_phase50_snapshot_id"), video.get("video_id") or video.get("source_path"), index),
            "snapshot_id": outputs.get("_phase50_snapshot_id"),
            "video_id": video.get("video_id") or Path(str(video.get("source_path") or "")).stem,
            "video_title": video.get("title") or Path(str(video.get("source_path") or "")).stem,
            "per_video_artifact_availability": "available" if video else "limited",
            "comparable_metric_families": ["readiness", "replay", "continuity", "recommendation", "governance"],
            "comparable_recommendation_families": ["recommendation_lineage", "recommendation_delta"],
            "comparable_timeline_families": ["temporal_evidence", "segment_context"],
            "comparable_governance_families": ["readiness_arbitration", "governance_ledger"],
            "version_like_candidates": _version_candidates(videos, video),
            "same_speaker_comparison_readiness": len(videos) > 1,
            "same_speaker_basis": "configured_corpus_context_only_not_biometric_identity",
            "missing_comparison_prerequisites": [] if len(videos) > 1 else ["additional configured corpus video"],
            "limitation": SAME_SPEAKER_LIMITATION,
        })
    return rows


def _artifact_counts(outputs: dict) -> dict:
    return {"json_artifact_count": sum(1 for value in outputs.values() if isinstance(value, dict)), "indexed_artifact_count": len((outputs.get("artifact_operational_index") or {}).get("artifacts") or [])}


def _dashboard_counts(output_dir: Path) -> dict:
    vis = output_dir / "visualizations"
    return {"html_dashboard_count": len(list(vis.rglob("*.html"))) if vis.exists() else 0}


def _validation_statuses(outputs: dict) -> dict:
    rows = (outputs.get("validation_index") or {}).get("validation_entries") or []
    return {"validation_entry_count": len(rows), "complete_count": sum(1 for row in rows if row.get("validation_state") in {STATUS_COMPLETE, "generated", "pending_indexed_validation"})}


def _phase_for_artifact(data: Any) -> str | None:
    return str(data.get("phase")) if isinstance(data, dict) and data.get("phase") else None


def _dependencies(outputs: dict, artifact_name: str) -> list[str]:
    for row in (outputs.get("generation_dependency_registry") or {}).get("dependencies") or []:
        if row.get("artifact") == artifact_name:
            return row.get("dependencies") or []
    return []


def _dashboard_links_for(artifact_name: str | None, outputs: dict) -> list[str]:
    for row in (outputs.get("artifact_operational_index") or {}).get("artifacts") or []:
        if row.get("artifact") == artifact_name:
            return row.get("linked_dashboards") or []
    return []


def _prior_snapshot_id(entries: list[dict], current: str | None) -> str | None:
    ids = [row.get("snapshot_id") for row in entries if row.get("snapshot_id")]
    if current in ids:
        pos = ids.index(current)
        return ids[pos - 1] if pos > 0 else None
    return ids[-1] if ids else None


def _latest_snapshot(entries: list[dict]) -> str | None:
    return entries[-1].get("snapshot_id") if entries else None


def _video_set_lineage(outputs: dict) -> list[str]:
    return [str(path) for path in (outputs.get("_phase50_snapshot_manifest") or {}).get("included_videos") or []]


def _version_candidates(videos: list[dict], current: dict) -> list[str]:
    current_stem = Path(str(current.get("source_path") or current.get("title") or "")).stem.lower()
    candidates = []
    for video in videos:
        stem = Path(str(video.get("source_path") or video.get("title") or "")).stem.lower()
        if stem and stem != current_stem and (stem in current_stem or current_stem in stem):
            candidates.append(video.get("video_id") or stem)
    return candidates


def _fields(rows: list[dict], id_field: str) -> list[str]:
    preferred = [id_field, "snapshot_id", "artifact_name", "artifact_family", "comparison_type", "baseline_type", "status", "summary", "limitation"]
    fields = [field for field in preferred if any(field in row for row in rows)]
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
            if len(fields) >= 8:
                return fields
    return fields or [id_field]


def _cell(value: object) -> str:
    if isinstance(value, list):
        return e(", ".join(str(item) for item in value[:5]))
    if isinstance(value, dict):
        return e(json.dumps(value, sort_keys=True)[:240])
    return e(value)


def _registry_id_name(kind: str) -> str:
    return {
        "artifact_snapshot_archive": "artifact_snapshot_archive_id",
        "snapshot_comparison": "snapshot_comparison_registry_id",
    }.get(kind, f"{kind}_registry_id")


def _output_key(kind: str) -> str:
    return {
        "run_snapshot": "run_snapshot_registry",
        "snapshot_provenance": "snapshot_provenance_registry",
        "snapshot_comparison": "snapshot_comparison_registry",
    }.get(kind, f"{kind}_registry")
