"""Shared deterministic Phase 49 fine-grained delta provenance helpers."""

from __future__ import annotations

from dashboard_layout import e
from phase45_interaction_common import route_rows
from phase47_replay_common import continuity_chain_rows, score_from_counts, stable_row_id
from phase48_diff_common import PHASE48_LIMITATION
from review_operational_common import compact_metrics, simple_review_page
from stability import STATUS_COMPLETE

PHASE49_LIMITATION = PHASE48_LIMITATION

DELTA_SPECS = {
    "artifact_diff_drilldown": ("ADD", "artifact_diff_drilldown_entries", "artifact_delta_id", "Artifact Diff Drilldown Dashboard", "artifact_diff_drilldown_dashboard.html", "deterministic_artifact_diff_drilldowns_v1"),
    "replay_route_delta": ("RRD49", "replay_route_delta_entries", "route_delta_id", "Replay Route Delta Dashboard", "replay_route_delta_dashboard.html", "deterministic_replay_route_delta_provenance_v1"),
    "dashboard_panel_diff": ("DPD", "dashboard_panel_diff_entries", "panel_delta_id", "Dashboard Panel Diff Dashboard", "dashboard_panel_diff_dashboard.html", "deterministic_dashboard_panel_diff_v1"),
    "continuity_chain_delta": ("CCD", "continuity_chain_delta_entries", "continuity_chain_delta_id", "Continuity Chain Delta Dashboard", "continuity_chain_delta_dashboard.html", "deterministic_continuity_chain_delta_v1"),
    "evidence_chain_diff": ("ECD", "evidence_chain_diff_entries", "evidence_chain_delta_id", "Evidence Chain Diff Dashboard", "evidence_chain_diff_dashboard.html", "deterministic_evidence_chain_diff_v1"),
    "recommendation_lineage_delta": ("RLD", "recommendation_lineage_delta_entries", "recommendation_lineage_delta_id", "Recommendation Lineage Delta Dashboard", "recommendation_lineage_delta_dashboard.html", "deterministic_recommendation_lineage_delta_v1"),
    "schema_validation_delta": ("SVD", "schema_validation_delta_entries", "schema_validation_delta_id", "Schema Validation Delta Dashboard", "schema_validation_delta_dashboard.html", "deterministic_schema_validation_delta_v1"),
    "regression_localization": ("RGL", "regression_localization_entries", "regression_localization_id", "Regression Localization Dashboard", "regression_localization_dashboard.html", "deterministic_regression_localization_v1"),
    "artifact_provenance_compare": ("APC", "artifact_provenance_compare_entries", "artifact_provenance_compare_id", "Artifact Provenance Compare Dashboard", "artifact_provenance_compare_dashboard.html", "deterministic_artifact_provenance_compare_v1"),
    "route_delta_dashboard": ("RDD", "route_delta_dashboard_entries", "route_delta_dashboard_id", "Route Delta Dashboard", "route_delta_dashboard.html", "deterministic_route_delta_dashboard_v1"),
    "panel_change_explainer": ("PCE", "panel_change_explainer_entries", "panel_change_explainer_id", "Panel Change Explainer Dashboard", "panel_change_explainer_dashboard.html", "deterministic_panel_change_explainer_v1"),
    "continuity_edge_diff": ("CED", "continuity_edge_diff_entries", "continuity_edge_diff_id", "Continuity Edge Diff Dashboard", "continuity_edge_diff_dashboard.html", "deterministic_continuity_edge_diff_v1"),
    "delta_drilldown_navigation": ("DDN", "delta_drilldown_navigation_entries", "delta_drilldown_navigation_id", "Delta Drilldown Navigation Dashboard", "delta_drilldown_navigation_dashboard.html", "deterministic_delta_drilldown_navigation_v1"),
    "regression_localization_packet": ("RLP", "regression_localization_packet_entries", "regression_packet_id", "Regression Localization Packet Dashboard", "regression_localization_packet_dashboard.html", "deterministic_regression_localization_packets_v1"),
    "unresolved_delta_queue": ("UDQ", "unresolved_delta_queue_entries", "unresolved_delta_id", "Unresolved Delta Queue Dashboard", "unresolved_delta_queue_dashboard.html", "deterministic_unresolved_delta_queue_v1"),
}

DELTA_LINKS = [
    ("Diffs", "../diffs/cross_run_diff_dashboard.html"),
    ("Artifacts", "artifact_diff_drilldown_dashboard.html"),
    ("Routes", "replay_route_delta_dashboard.html"),
    ("Panels", "dashboard_panel_diff_dashboard.html"),
    ("Continuity", "continuity_chain_delta_dashboard.html"),
    ("Evidence", "evidence_chain_diff_dashboard.html"),
    ("Recommendations", "recommendation_lineage_delta_dashboard.html"),
    ("Validation", "schema_validation_delta_dashboard.html"),
    ("Regressions", "regression_localization_dashboard.html"),
    ("Queue", "unresolved_delta_queue_dashboard.html"),
]

DELTA_DRILLDOWN_LINKS = [
    ("Diffs", "../../diffs/cross_run_diff_dashboard.html"),
    ("Artifacts", "../artifact_diff_drilldown_dashboard.html"),
    ("Routes", "../replay_route_delta_dashboard.html"),
    ("Panels", "../dashboard_panel_diff_dashboard.html"),
    ("Continuity", "../continuity_chain_delta_dashboard.html"),
    ("Evidence", "../evidence_chain_diff_dashboard.html"),
    ("Recommendations", "../recommendation_lineage_delta_dashboard.html"),
    ("Validation", "../schema_validation_delta_dashboard.html"),
    ("Regressions", "../regression_localization_dashboard.html"),
    ("Queue", "../unresolved_delta_queue_dashboard.html"),
]


def phase49_artifact(method: str) -> dict:
    return {
        "analysis_status": STATUS_COMPLETE,
        "method": method,
        "phase": "49",
        "limitations": [PHASE49_LIMITATION],
        "append_only_history_preserved": True,
        "deterministic_operational_evolution_tracking": True,
        "fine_grained_delta_provenance": True,
        "offline_cross_run_diffing": True,
        "browserless_replay_validation": True,
        "external_runtime_dependency_introduced": False,
        "hidden_mutable_runtime_state_introduced": False,
        "cloud_api_introduced": False,
        "llm_runtime_call_introduced": False,
        "semantic_vector_store_introduced": False,
        "autonomous_remediation_used": False,
        "autonomous_editorial_decision_used": False,
        "human_review_required": True,
    }


def _list(outputs: dict, key: str, field: str) -> list[dict]:
    value = (outputs.get(key) or {}).get(field) or []
    return [row for row in value if isinstance(row, dict)]


def _by(rows: list[dict], *keys: str) -> dict[str, dict]:
    indexed = {}
    for index, row in enumerate(rows):
        key = next((str(row.get(name)) for name in keys if row.get(name) is not None), None)
        indexed[key or stable_row_id("DKEY", index, row)] = row
    return indexed


def _changed_keys(prior: dict | None, current: dict | None) -> tuple[list[str], list[str], list[str]]:
    prior = prior or {}
    current = current or {}
    prior_keys = set(prior)
    current_keys = set(current)
    changed = sorted(key for key in prior_keys & current_keys if prior.get(key) != current.get(key))
    return changed, sorted(current_keys - prior_keys), sorted(prior_keys - current_keys)


def _change_type(prior: dict | None, current: dict | None, degraded: bool = False) -> str:
    if prior is None:
        return "new"
    if current is None:
        return "removed"
    changed, added, removed = _changed_keys(prior, current)
    if degraded:
        return "degraded"
    if changed or added or removed:
        return "changed"
    return "unchanged"


def _prior(outputs: dict, name: str, current: list[dict]) -> list[dict]:
    explicit = outputs.get(f"phase49_prior_{name}")
    return explicit if isinstance(explicit, list) else current


def artifact_delta_rows(outputs: dict) -> list[dict]:
    current = _list(outputs, "artifact_operational_index", "artifacts")
    prior = _prior(outputs, "artifacts", current)
    current_by = _by(current, "artifact", "artifact_ref", "artifact_index_id")
    prior_by = _by(prior, "artifact", "artifact_ref", "artifact_index_id")
    rows = []
    for index, key in enumerate(sorted(set(current_by) | set(prior_by))):
        cur = current_by.get(key)
        old = prior_by.get(key)
        changed, added, removed = _changed_keys(old, cur)
        change_type = _change_type(old, cur, bool(old and cur and old.get("validation_state") != cur.get("validation_state") and cur.get("validation_state") != "generated"))
        artifact_name = (cur or old).get("artifact") or key
        artifact_ref = (cur or old).get("artifact_ref")
        rows.append({
            "artifact_delta_id": stable_row_id("ADD", index, key, changed, added, removed),
            "current_artifact_path": cur.get("artifact_ref") if cur else None,
            "prior_artifact_path": old.get("artifact_ref") if old else None,
            "artifact_family": artifact_name,
            "artifact_type": (cur or old).get("artifact_type"),
            "current_artifact_hash": cur.get("artifact_hash") if cur else None,
            "prior_artifact_hash": old.get("artifact_hash") if old else None,
            "schema_version": "local_schema_copy",
            "generated_phase": (cur or old).get("generation_phase"),
            "change_type": change_type,
            "summary": f"{artifact_name} {change_type}; {len(changed)} changed keys, {len(added)} added keys, {len(removed)} removed keys.",
            "changed_keys": changed,
            "added_keys": added,
            "removed_keys": removed,
            "changed_references": [artifact_ref] if artifact_ref else [],
            "downstream_impacts": (cur or old).get("dependencies") or [],
            "related_dashboards": (cur or old).get("linked_dashboards") or [],
            "related_routes": [],
            "related_validation": (cur or old).get("validation_state"),
            "human_review_recommended": change_type in {"changed", "removed", "degraded"},
            "evidence_refs": [ref for ref in [(cur or old).get("artifact_ref"), *((cur or old).get("linked_schemas") or [])] if ref],
            "drilldown_href": f"drilldowns/artifact_delta_{stable_row_id('ADDHTML', key)}.html",
        })
    return rows


def route_delta_rows(outputs: dict) -> list[dict]:
    current = _list(outputs, "route_reproducibility_registry", "route_reproducibility_entries") or route_rows()
    prior = _prior(outputs, "routes", current)
    current_by = _by(current, "route_id", "route_reproducibility_id")
    prior_by = _by(prior, "route_id", "route_reproducibility_id")
    rows = []
    for index, key in enumerate(sorted(set(current_by) | set(prior_by))):
        cur = current_by.get(key)
        old = prior_by.get(key)
        degraded = bool(old and cur and old.get("route_reproducibility_status") == "reproducible" and cur.get("route_reproducibility_status") != "reproducible")
        change_type = _change_type(old, cur, degraded)
        old_score = 1.0 if old and old.get("route_reproducibility_status") == "reproducible" else 0.0
        cur_score = 1.0 if cur and cur.get("route_reproducibility_status") == "reproducible" else 0.0
        rows.append({
            "route_delta_id": stable_row_id("RTD", index, key, change_type),
            "route_id": (cur or old).get("route_id") or key,
            "source_dashboard": (old or cur).get("dashboard_href"),
            "destination_dashboard": (cur or old).get("dashboard_href"),
            "breadcrumb_path": [(old or cur).get("dashboard_href"), (cur or old).get("dashboard_href")],
            "continuity_path": [(cur or old).get("route_id")],
            "prior_route_validity": old.get("route_reproducibility_status") if old else None,
            "current_route_validity": cur.get("route_reproducibility_status") if cur else None,
            "route_depth_delta": 0 if old and cur else 1,
            "prior_survivability_score": old_score,
            "current_survivability_score": cur_score,
            "survivability_delta": round(cur_score - old_score, 3),
            "became_unreachable": degraded or (cur is None),
            "became_newly_reachable": bool(cur and not old),
            "change_type": change_type,
            "what_changed": f"Route {(cur or old).get('route_id') or key} {change_type}; survivability delta {round(cur_score - old_score, 3)}.",
            "caused_by_artifacts": [(cur or old).get("dashboard_href")] if (cur or old).get("dashboard_href") else [],
            "human_review_recommended": change_type in {"degraded", "removed"},
            "evidence_refs": [ref for ref in [(cur or old).get("dashboard_href")] if ref],
            "drilldown_href": f"drilldowns/route_delta_{stable_row_id('RTHTML', key)}.html",
        })
    return rows


def panel_delta_rows(outputs: dict) -> list[dict]:
    artifacts = _list(outputs, "artifact_operational_index", "artifacts")
    current = []
    for artifact in artifacts:
        for dashboard in artifact.get("linked_dashboards") or []:
            current.append({"dashboard_path": dashboard, "panel_id": artifact.get("artifact"), "source_count": len(artifact.get("dependencies") or []), "status_badge": artifact.get("validation_state"), "recommendation_count": 0})
    if not current:
        current = [{"dashboard_path": "visualizations/diffs/cross_run_diff_dashboard.html", "panel_id": "cross_run_diff_summary", "source_count": len(_list(outputs, "cross_run_diff_registry", "cross_run_diff_entries")), "status_badge": "generated", "recommendation_count": 0}]
    prior = _prior(outputs, "panels", current)
    current_by = _by(current, "panel_id")
    prior_by = _by(prior, "panel_id")
    rows = []
    for index, key in enumerate(sorted(set(current_by) | set(prior_by))):
        cur = current_by.get(key)
        old = prior_by.get(key)
        changed, added, removed = _changed_keys(old, cur)
        change_type = _change_type(old, cur)
        rows.append({
            "panel_delta_id": stable_row_id("PND", index, key, change_type),
            "dashboard_path": (cur or old).get("dashboard_path"),
            "panel_id": (cur or old).get("panel_id") or key,
            "change_type": change_type,
            "prior_summary": f"{old.get('source_count')} sources; {old.get('status_badge')}" if old else None,
            "current_summary": f"{cur.get('source_count')} sources; {cur.get('status_badge')}" if cur else None,
            "changed_links": ["dashboard_path"] if "dashboard_path" in changed else [],
            "changed_counts": [key for key in changed if key.endswith("_count") or key == "source_count"],
            "changed_status_badges": [key for key in changed if "status" in key],
            "changed_recommendations": [key for key in changed if "recommendation" in key],
            "review_priority": "high" if change_type in {"removed", "degraded"} else "medium" if change_type == "changed" else "low",
            "human_review_recommended": change_type != "unchanged",
            "evidence_refs": [(cur or old).get("dashboard_path")],
            "drilldown_href": f"drilldowns/panel_delta_{stable_row_id('PNHTML', key)}.html",
        })
    return rows


def continuity_delta_rows(outputs: dict) -> list[dict]:
    current = continuity_chain_rows(outputs)
    prior = _prior(outputs, "continuity_chains", current)
    return _generic_rows("CCH", current, prior, "chain_id", "continuity_chain_delta_id", "continuity_chain_delta", "continuity_chain_delta", ["nodes", "edges", "reachability", "orphan_status", "breadcrumb_continuity", "replay_coverage", "governance_relevance", "escalation_relevance"])


def evidence_delta_rows(outputs: dict) -> list[dict]:
    current = _list(outputs, "temporal_evidence_index", "temporal_evidence_entries")
    prior = _prior(outputs, "evidence_chains", current)
    return _generic_rows("ECH", current, prior, "temporal_evidence_id", "evidence_chain_delta_id", "evidence_chain_delta", "evidence_chain_delta", ["evidence_refs", "linked_artifacts", "recommendations", "governance_references", "segment_references", "timeline_references", "validation_references"])


def recommendation_delta_rows(outputs: dict) -> list[dict]:
    current = _list(outputs, "recommendation_lineage", "lineage_items")
    prior = _prior(outputs, "recommendations", current)
    return _generic_rows("RLD", current, prior, "recommendation_id", "recommendation_lineage_delta_id", "recommendation_lineage_delta", "recommendation_lineage_delta", ["priority", "effort_estimate", "evidence_refs", "segment_link", "governance_relevance", "optimization_path", "overcorrection_risk"])


def schema_delta_rows(outputs: dict) -> list[dict]:
    current = [{"schema_path": row} for artifact in _list(outputs, "artifact_operational_index", "artifacts") for row in artifact.get("linked_schemas") or []]
    prior = _prior(outputs, "schemas", current)
    return _generic_rows("SVD", current, prior, "schema_path", "schema_validation_delta_id", "schema_validation_delta", "schema_validation_delta", ["schema_additions", "schema_removals", "validation_status_changes", "validation_count_changes", "parse_status_changes", "link_validation_changes", "png_validation_changes", "forbidden_integration_scan_changes"])


def _generic_rows(prefix: str, current: list[dict], prior: list[dict], match_key: str, id_field: str, href_prefix: str, scope: str, fields: list[str]) -> list[dict]:
    current_by = _by(current, match_key)
    prior_by = _by(prior, match_key)
    rows = []
    for index, key in enumerate(sorted(set(current_by) | set(prior_by))):
        cur = current_by.get(key)
        old = prior_by.get(key)
        changed, added, removed = _changed_keys(old, cur)
        change_type = _change_type(old, cur)
        rows.append({
            id_field: stable_row_id(prefix, index, key, change_type),
            "delta_scope": scope,
            "source_id": key,
            "change_type": change_type,
            "summary": f"{scope} {key} {change_type}; changed={len(changed)}, added={len(added)}, removed={len(removed)}.",
            "changed_keys": changed,
            "added_keys": added,
            "removed_keys": removed,
            "delta_fields": fields,
            "human_review_recommended": change_type != "unchanged",
            "evidence_refs": [ref for ref in [(cur or old).get(match_key), *((cur or old).get("evidence_refs") or [])] if ref],
            "drilldown_href": f"drilldowns/{href_prefix}_{stable_row_id(prefix + 'HTML', key)}.html",
        })
    return rows


def regression_rows(outputs: dict) -> list[dict]:
    candidates = []
    for source, rows in [
        ("route", route_delta_rows(outputs)),
        ("artifact", artifact_delta_rows(outputs)),
        ("panel", panel_delta_rows(outputs)),
        ("continuity", continuity_delta_rows(outputs)),
        ("evidence", evidence_delta_rows(outputs)),
        ("validation", schema_delta_rows(outputs)),
    ]:
        for row in rows:
            if row.get("change_type") in {"degraded", "removed"} or row.get("became_unreachable") or row.get("human_review_recommended"):
                candidates.append((source, row))
    output = []
    for index, (source, row) in enumerate(candidates[:120]):
        output.append({
            "regression_localization_id": stable_row_id("RGL", index, source, row),
            "regression_type": f"{source}_regression" if row.get("change_type") in {"degraded", "removed"} else f"{source}_delta_review",
            "localized_to": source,
            "affected_artifacts": row.get("caused_by_artifacts") or row.get("evidence_refs") or [],
            "affected_routes": [row.get("route_id")] if row.get("route_id") else [],
            "affected_dashboards": [row.get("dashboard_path")] if row.get("dashboard_path") else row.get("related_dashboards") or [],
            "affected_continuity_chains": [row.get("source_id")] if source == "continuity" else [],
            "affected_evidence_chains": [row.get("source_id")] if source == "evidence" else [],
            "summary": row.get("what_changed") or row.get("summary"),
            "review_priority": row.get("review_priority") or "medium",
            "evidence_refs": row.get("evidence_refs") or [],
            "human_review_required": True,
            "drilldown_href": row.get("drilldown_href"),
        })
    return output or [{
        "regression_localization_id": stable_row_id("RGL", "no_regression"),
        "regression_type": "no_fine_grained_regression_detected",
        "localized_to": "phase49_delta_surface",
        "affected_artifacts": [],
        "affected_routes": [],
        "affected_dashboards": [],
        "affected_continuity_chains": [],
        "affected_evidence_chains": [],
        "summary": "No fine-grained regression was detected in the deterministic local comparison surface.",
        "review_priority": "low",
        "evidence_refs": [],
        "human_review_required": True,
        "drilldown_href": None,
    }]


def packet_rows(outputs: dict) -> list[dict]:
    packets = []
    for index, row in enumerate(regression_rows(outputs)):
        packets.append({
            "regression_packet_id": stable_row_id("RLP", index, row.get("regression_localization_id")),
            "regression_summary": row.get("summary"),
            "affected_artifacts": row.get("affected_artifacts") or [],
            "affected_routes": row.get("affected_routes") or [],
            "affected_dashboards": row.get("affected_dashboards") or [],
            "affected_continuity_chains": row.get("affected_continuity_chains") or [],
            "evidence_refs": row.get("evidence_refs") or [],
            "likely_source_area": row.get("localized_to"),
            "suggested_manual_review": "Review the linked local artifacts and dashboards before changing lineage or governance state.",
            "non_autonomous_remediation_guidance": "No automatic remediation is performed; preserve append-only history and record any human decision explicitly.",
            "human_review_required": True,
            "drilldown_href": f"drilldowns/regression_packet_{stable_row_id('RLPHTML', row.get('regression_localization_id'))}.html",
        })
    return packets


def navigation_rows(outputs: dict) -> list[dict]:
    sources = [
        ("overview_to_artifact_delta", artifact_delta_rows(outputs), "artifact_delta_id"),
        ("route_regression_to_route_delta", route_delta_rows(outputs), "route_delta_id"),
        ("dashboard_panel_diff_to_panel_delta", panel_delta_rows(outputs), "panel_delta_id"),
        ("recommendation_delta_to_lineage_delta", recommendation_delta_rows(outputs), "recommendation_lineage_delta_id"),
        ("validation_delta_to_schema_validation_delta", schema_delta_rows(outputs), "schema_validation_delta_id"),
        ("continuity_regression_to_chain_delta", continuity_delta_rows(outputs), "continuity_chain_delta_id"),
    ]
    rows = []
    for nav_type, source_rows, id_field in sources:
        for index, row in enumerate(source_rows[:24]):
            rows.append({
                "delta_drilldown_navigation_id": stable_row_id("DDN", nav_type, index, row.get(id_field)),
                "navigation_type": nav_type,
                "source_delta_id": row.get(id_field),
                "target_drilldown_href": row.get("drilldown_href"),
                "source_dashboard_href": _dashboard_for_nav(nav_type),
                "change_type": row.get("change_type"),
                "human_review_required": True,
            })
    return rows


def _dashboard_for_nav(nav_type: str) -> str:
    if "route" in nav_type:
        return "replay_route_delta_dashboard.html"
    if "panel" in nav_type:
        return "dashboard_panel_diff_dashboard.html"
    if "recommendation" in nav_type:
        return "recommendation_lineage_delta_dashboard.html"
    if "validation" in nav_type:
        return "schema_validation_delta_dashboard.html"
    if "continuity" in nav_type:
        return "continuity_chain_delta_dashboard.html"
    return "artifact_diff_drilldown_dashboard.html"


def queue_rows(outputs: dict) -> list[dict]:
    queued = []
    for source, rows, id_field in [
        ("route_delta", route_delta_rows(outputs), "route_delta_id"),
        ("artifact_delta", artifact_delta_rows(outputs), "artifact_delta_id"),
        ("panel_delta", panel_delta_rows(outputs), "panel_delta_id"),
        ("continuity_delta", continuity_delta_rows(outputs), "continuity_chain_delta_id"),
        ("recommendation_delta", recommendation_delta_rows(outputs), "recommendation_lineage_delta_id"),
        ("validation_delta", schema_delta_rows(outputs), "schema_validation_delta_id"),
    ]:
        for row in rows:
            if row.get("human_review_recommended") or row.get("became_unreachable") or row.get("change_type") in {"changed", "removed", "degraded"}:
                queued.append({
                    "unresolved_delta_id": stable_row_id("UDQ", source, row.get(id_field)),
                    "queue_reason": source,
                    "source_delta_id": row.get(id_field),
                    "change_type": row.get("change_type"),
                    "summary": row.get("what_changed") or row.get("summary"),
                    "review_priority": row.get("review_priority") or ("high" if row.get("change_type") in {"removed", "degraded"} else "medium"),
                    "evidence_refs": row.get("evidence_refs") or [],
                    "auto_remediation_performed": False,
                    "human_review_required": True,
                })
    return queued


def rows_for_kind(outputs: dict, kind: str) -> list[dict]:
    if kind == "artifact_diff_drilldown":
        return artifact_delta_rows(outputs)
    if kind == "replay_route_delta":
        return route_delta_rows(outputs)
    if kind == "dashboard_panel_diff":
        return panel_delta_rows(outputs)
    if kind == "continuity_chain_delta":
        return continuity_delta_rows(outputs)
    if kind == "evidence_chain_diff":
        return evidence_delta_rows(outputs)
    if kind == "recommendation_lineage_delta":
        return recommendation_delta_rows(outputs)
    if kind == "schema_validation_delta":
        return schema_delta_rows(outputs)
    if kind == "regression_localization":
        return regression_rows(outputs)
    if kind == "artifact_provenance_compare":
        return artifact_delta_rows(outputs)
    if kind == "route_delta_dashboard":
        return route_delta_rows(outputs)
    if kind == "panel_change_explainer":
        return panel_delta_rows(outputs)
    if kind == "continuity_edge_diff":
        return continuity_delta_rows(outputs)
    if kind == "delta_drilldown_navigation":
        return navigation_rows(outputs)
    if kind == "regression_localization_packet":
        return packet_rows(outputs)
    if kind == "unresolved_delta_queue":
        return queue_rows(outputs)
    raise KeyError(kind)


def build_phase49_registry(outputs: dict, kind: str) -> dict:
    prefix, entry_key, id_field, _title, _filename, method = DELTA_SPECS[kind]
    rows = rows_for_kind(outputs, kind)
    artifact = phase49_artifact(method)
    artifact.update({
        f"{kind}_registry_id": stable_row_id(f"{prefix}REG", [row.get(id_field) for row in rows]),
        entry_key: rows,
        "comparison_summary": {
            "entry_count": len(rows),
            "changed_count": sum(1 for row in rows if row.get("change_type") in {"changed", "removed", "new", "degraded"}),
            "review_recommended_count": sum(1 for row in rows if row.get("human_review_recommended") or row.get("human_review_required")),
            "fine_grained_survivability_score": score_from_counts(sum(1 for row in rows if row.get("change_type") not in {"removed", "degraded"}), len(rows)),
        },
        "summary": {
            f"{kind}_entry_count": len(rows),
            "external_runtime_dependency_introduced": False,
            "append_only_history_preserved": True,
            "human_review_required": True,
        },
    })
    return artifact


def render_phase49_dashboard(outputs: dict, kind: str) -> dict[str, str]:
    _prefix, entry_key, id_field, title, filename, _method = DELTA_SPECS[kind]
    rows = (outputs.get(f"{kind}_registry") or {}).get(entry_key) or []
    metrics = [
        ("Entries", len(rows)),
        ("Changed", sum(1 for row in rows if row.get("change_type") in {"changed", "removed", "new", "degraded"})),
        ("Review", sum(1 for row in rows if row.get("human_review_recommended") or row.get("human_review_required"))),
    ]
    fields = _fields(rows, id_field)
    header = "".join(f"<th scope='col'>{e(field.replace('_', ' ').title())}</th>" for field in fields)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{_cell(row.get(field))}</td>" for field in fields)
        body_rows.append(f"<tr id='{e(row.get(id_field) or stable_row_id('P49ROW', row))}' tabindex='-1'>{cells}</tr>")
    table = f"<section class='panel'><table class='data-table'><thead><tr>{header}</tr></thead><tbody>{''.join(body_rows)}</tbody></table></section>"
    body = f"<section class='panel'><p>{e(PHASE49_LIMITATION)}</p></section>{compact_metrics(metrics)}{table}"
    return {filename: simple_review_page(title, "Fine-Grained Delta Provenance", filename, body, DELTA_LINKS)}


def _fields(rows: list[dict], id_field: str) -> list[str]:
    preferred = [id_field, "change_type", "summary", "what_changed", "review_priority", "human_review_recommended", "drilldown_href"]
    fields = [field for field in preferred if any(field in row for row in rows)]
    for row in rows:
        for key in row:
            if key not in fields and key not in {"limitations"}:
                fields.append(key)
            if len(fields) >= 8:
                return fields
    return fields or [id_field]


def _cell(value: object) -> str:
    if isinstance(value, list):
        return e(", ".join(str(item) for item in value[:4]))
    return e(value)


def render_phase49_drilldowns(outputs: dict) -> dict[str, str]:
    pages = {}
    drill_specs = [
        ("artifact_diff_drilldown_registry", "artifact_diff_drilldown_entries", "artifact_delta_id", "Artifact Delta"),
        ("replay_route_delta_registry", "replay_route_delta_entries", "route_delta_id", "Route Delta"),
        ("dashboard_panel_diff_registry", "dashboard_panel_diff_entries", "panel_delta_id", "Panel Delta"),
        ("continuity_chain_delta_registry", "continuity_chain_delta_entries", "continuity_chain_delta_id", "Continuity Chain Delta"),
        ("evidence_chain_diff_registry", "evidence_chain_diff_entries", "evidence_chain_delta_id", "Evidence Chain Delta"),
        ("recommendation_lineage_delta_registry", "recommendation_lineage_delta_entries", "recommendation_lineage_delta_id", "Recommendation Lineage Delta"),
        ("regression_localization_packet_registry", "regression_localization_packet_entries", "regression_packet_id", "Regression Packet"),
    ]
    for registry_key, entry_key, id_field, title in drill_specs:
        for row in (outputs.get(registry_key) or {}).get(entry_key) or []:
            href = row.get("drilldown_href")
            if not href:
                continue
            filename = href.replace("drilldowns/", "")
            body = f"<section class='panel'><p>{e(PHASE49_LIMITATION)}</p></section><section class='panel'><h2>{e(title)}</h2>{_detail_list(row)}</section>"
            pages[filename] = simple_review_page(f"{title}: {row.get(id_field)}", "Delta Drilldown", filename, body, DELTA_DRILLDOWN_LINKS, depth=3)
    return pages


def _detail_list(row: dict) -> str:
    items = "".join(f"<dt>{e(key.replace('_', ' ').title())}</dt><dd>{_cell(value)}</dd>" for key, value in sorted(row.items()))
    return f"<dl>{items}</dl>"
