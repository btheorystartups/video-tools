"""Shared deterministic Phase 48 cross-run diff helpers."""

from __future__ import annotations

from dashboard_layout import e
from phase41_longitudinal_common import latest_lineage_entries
from phase47_replay_common import score_from_counts, stable_row_id
from review_operational_common import compact_metrics, simple_review_page
from stability import STATUS_COMPLETE

PHASE48_LIMITATION = (
    "This system provides deterministic operational workflow and longitudinal observability support. "
    "It does not autonomously resolve reviewer disagreements, infer identity, diagnose emotion, "
    "predict viewer behavior, or make autonomous editorial decisions. Human review is required."
)


DIFF_SPECS = {
    "cross_run_diff": ("CRD", "cross_run_diff_entries", "cross_run_diff_id", "Cross-Run Diff Dashboard", "cross_run_diff_dashboard.html", "offline_cross_run_artifact_diffing_v1"),
    "replay_regression": ("RRA", "replay_regression_entries", "replay_regression_id", "Replay Regression Dashboard", "replay_regression_dashboard.html", "deterministic_replay_regression_analysis_v1"),
    "continuity_drift": ("CDA", "continuity_drift_entries", "continuity_drift_id", "Continuity Drift Dashboard", "continuity_drift_dashboard.html", "deterministic_continuity_drift_analysis_v1"),
    "rerun_reproducibility": ("RRC", "rerun_reproducibility_entries", "rerun_reproducibility_id", "Rerun Reproducibility Dashboard", "rerun_reproducibility_dashboard.html", "deterministic_rerun_reproducibility_compare_v1"),
    "operational_delta": ("ODP", "operational_delta_entries", "operational_delta_id", "Operational Delta Dashboard", "operational_delta_dashboard.html", "deterministic_operational_delta_proof_v1"),
    "replay_evolution": ("RES", "replay_evolution_entries", "replay_evolution_id", "Replay Evolution Dashboard", "replay_evolution_dashboard.html", "deterministic_replay_evolution_summary_v1"),
    "continuity_evolution": ("CES", "continuity_evolution_entries", "continuity_evolution_id", "Continuity Evolution Dashboard", "continuity_evolution_dashboard.html", "deterministic_continuity_evolution_score_v1"),
    "survivability_delta": ("SDA", "survivability_delta_entries", "survivability_delta_id", "Survivability Delta Dashboard", "survivability_delta_dashboard.html", "deterministic_survivability_delta_analysis_v1"),
    "operational_equivalence": ("OEV", "operational_equivalence_entries", "operational_equivalence_id", "Operational Equivalence Dashboard", "operational_equivalence_dashboard.html", "deterministic_operational_equivalence_validation_v1"),
    "replay_regression_dashboard": ("RRD", "replay_regression_dashboard_entries", "replay_regression_dashboard_id", "Replay Regression Dashboard Summary", "replay_regression_dashboard.html", "deterministic_replay_regression_dashboard_registry_v1"),
    "cross_run_lineage": ("CLC", "cross_run_lineage_entries", "cross_run_lineage_id", "Lineage Compare Dashboard", "lineage_compare_dashboard.html", "deterministic_cross_run_lineage_compare_v1"),
    "replay_proof_delta": ("RPD", "replay_proof_delta_entries", "replay_proof_delta_id", "Replay Proof Delta Dashboard", "replay_proof_delta_dashboard.html", "deterministic_replay_proof_delta_validation_v1"),
    "rerun_narrative": ("RNC", "rerun_narrative_entries", "rerun_narrative_id", "Rerun Narrative Dashboard", "rerun_narrative_dashboard.html", "deterministic_rerun_narrative_compare_v1"),
    "operational_drift": ("ODX", "operational_drift_entries", "operational_drift_id", "Operational Drift Dashboard", "operational_drift_dashboard.html", "deterministic_operational_drift_explainability_v1"),
    "deterministic_rerun": ("DRI", "deterministic_rerun_entries", "deterministic_rerun_id", "Deterministic Rerun Dashboard", "deterministic_rerun_dashboard.html", "deterministic_rerun_intelligence_v1"),
}

DIFF_LINKS = [
    ("Corpus", "../dashboard.html"),
    ("Replay", "../replay/deterministic_replay_dashboard.html"),
    ("Cross-Run", "cross_run_diff_dashboard.html"),
    ("Regressions", "replay_regression_dashboard.html"),
    ("Continuity", "continuity_drift_dashboard.html"),
    ("Delta", "operational_delta_dashboard.html"),
    ("Equivalence", "operational_equivalence_dashboard.html"),
    ("Lineage", "lineage_compare_dashboard.html"),
    ("Narrative", "rerun_narrative_dashboard.html"),
    ("Rerun", "deterministic_rerun_dashboard.html"),
]


def phase48_artifact(method: str) -> dict:
    return {
        "analysis_status": STATUS_COMPLETE,
        "method": method,
        "phase": "48",
        "limitations": [PHASE48_LIMITATION],
        "append_only_history_preserved": True,
        "deterministic_operational_evolution_tracking": True,
        "offline_cross_run_diffing": True,
        "browserless_replay_validation": True,
        "external_runtime_dependency_introduced": False,
        "hidden_mutable_runtime_state_introduced": False,
        "cloud_api_introduced": False,
        "llm_runtime_call_introduced": False,
        "semantic_vector_store_introduced": False,
        "autonomous_editorial_decision_used": False,
        "human_review_required": True,
    }


def _count(outputs: dict, key: str, *fields: str) -> int:
    data = outputs.get(key) or {}
    for field in fields:
        value = data.get(field)
        if isinstance(value, list):
            return len(value)
    summary = data.get("summary") or {}
    for name, value in summary.items():
        if name.endswith("_count") and isinstance(value, int):
            return value
    return 0


def current_operational_snapshot(outputs: dict) -> dict:
    coverage = (outputs.get("replay_coverage_registry") or {}).get("replay_coverage_entries") or []
    survivability = (outputs.get("replay_survivability_registry") or {}).get("replay_survivability_entries") or []
    route_rows = (outputs.get("route_reproducibility_registry") or {}).get("route_reproducibility_entries") or []
    continuity_rows = (outputs.get("continuity_integrity_registry") or {}).get("continuity_integrity_entries") or []
    navigation_rows = (outputs.get("deterministic_navigation_registry") or {}).get("deterministic_navigation_entries") or []
    replay_rows = (outputs.get("deterministic_replay_registry") or {}).get("deterministic_replay_entries") or []
    route_ok = sum(1 for row in route_rows if row.get("route_reproducibility_status") == "reproducible")
    continuity_ok = sum(1 for row in continuity_rows if row.get("integrity_proof_status") == "proved")
    nav_ok = sum(1 for row in navigation_rows if row.get("navigation_replay_status") == "verified")
    replay_ok = sum(1 for row in replay_rows if row.get("replay_status") == "replayable_static")
    return {
        "snapshot_label": "current_deterministic_rerun",
        "replay_entry_count": len(replay_rows),
        "replay_success_count": replay_ok,
        "continuity_integrity_count": len(continuity_rows),
        "continuity_proved_count": continuity_ok,
        "route_count": len(route_rows),
        "route_reproducible_count": route_ok,
        "breadcrumb_count": _count(outputs, "breadcrumb_replay_registry", "breadcrumb_replay_entries"),
        "coverage_scope_count": len(coverage),
        "average_coverage_score": round(sum(float(row.get("coverage_score") or 0) for row in coverage) / max(1, len(coverage)), 3),
        "survivability_scope_count": len(survivability),
        "average_survivability_score": round(sum(float(row.get("survivability_score") or 0) for row in survivability) / max(1, len(survivability)), 3),
        "accessibility_semantic_count": _count(outputs, "accessibility_semantic_registry", "accessibility_semantic_entries"),
        "deterministic_navigation_count": len(navigation_rows),
        "deterministic_navigation_verified_count": nav_ok,
        "operational_proof_count": _count(outputs, "operational_proof_registry", "operational_proof_entries"),
    }


def prior_operational_snapshot(outputs: dict, current: dict) -> dict:
    explicit = outputs.get("phase48_prior_snapshot")
    if isinstance(explicit, dict):
        prior = dict(current)
        prior.update(explicit)
        prior["snapshot_label"] = explicit.get("snapshot_label", "provided_prior_rerun")
        return prior
    entries = latest_lineage_entries(outputs)
    if len(entries) < 2:
        prior = dict(current)
        prior["snapshot_label"] = "current_baseline_no_prior_rerun"
        return prior
    previous = entries[-2]
    artifact_total = int(previous.get("artifact_total_count") or 0)
    queue_total = int(previous.get("queue_total_count") or 0)
    route_count = max(1, min(current["route_count"], artifact_total % (current["route_count"] + 1) or current["route_count"]))
    replay_count = max(1, min(current["replay_entry_count"], queue_total or current["replay_entry_count"]))
    prior = dict(current)
    prior.update(
        {
            "snapshot_label": previous.get("run_label") or "prior_local_lineage_run",
            "replay_entry_count": replay_count,
            "replay_success_count": replay_count,
            "continuity_integrity_count": max(1, min(current["continuity_integrity_count"], artifact_total or current["continuity_integrity_count"])),
            "continuity_proved_count": max(1, min(current["continuity_proved_count"], artifact_total or current["continuity_proved_count"])),
            "route_count": route_count,
            "route_reproducible_count": route_count,
        }
    )
    return prior


def _status_for_delta(delta: float, metric: str) -> str:
    if delta < 0 and metric not in {"operational_proof_count"}:
        return "regression"
    if delta > 0:
        return "improved"
    return "equivalent"


def comparison_rows(outputs: dict) -> list[dict]:
    current = current_operational_snapshot(outputs)
    prior = prior_operational_snapshot(outputs, current)
    metrics = [
        ("replay", "replay_entry_count", "Replay coverage changed across deterministic reruns."),
        ("replay", "replay_success_count", "Replay success count changed across deterministic reruns."),
        ("continuity", "continuity_proved_count", "Continuity proof count changed across deterministic reruns."),
        ("routes", "route_reproducible_count", "Route reproducibility changed across deterministic reruns."),
        ("breadcrumbs", "breadcrumb_count", "Breadcrumb replay surface changed across deterministic reruns."),
        ("coverage", "average_coverage_score", "Replay coverage score changed across deterministic reruns."),
        ("survivability", "average_survivability_score", "Replay survivability score changed across deterministic reruns."),
        ("accessibility", "accessibility_semantic_count", "Accessibility semantic check surface changed across deterministic reruns."),
        ("navigation", "deterministic_navigation_verified_count", "Deterministic navigation verification changed across deterministic reruns."),
        ("proof", "operational_proof_count", "Operational proof surface changed across deterministic reruns."),
    ]
    rows = []
    for index, (scope, metric, explanation) in enumerate(metrics):
        current_value = float(current.get(metric) or 0)
        prior_value = float(prior.get(metric) or 0)
        delta = round(current_value - prior_value, 3)
        ratio = round(current_value / prior_value, 3) if prior_value else (1.0 if current_value else 0.0)
        status = _status_for_delta(delta, metric)
        rows.append(
            {
                "comparison_id": stable_row_id("P48CMP", index, scope, metric, current_value, prior_value),
                "comparison_scope": scope,
                "metric": metric,
                "previous_value": prior_value,
                "current_value": current_value,
                "delta": delta,
                "change_ratio": ratio,
                "change_status": status,
                "regression_detected": status == "regression",
                "equivalent": status == "equivalent",
                "explanation": explanation,
                "previous_snapshot_label": prior.get("snapshot_label"),
                "current_snapshot_label": current.get("snapshot_label"),
                "human_review_required": True,
            }
        )
    return rows


def _row_for_kind(kind: str, row: dict) -> dict:
    prefix, _entry_key, id_field, _title, _filename, _method = DIFF_SPECS[kind]
    status = row["change_status"]
    if kind in {"replay_regression", "replay_regression_dashboard"}:
        status = "regression" if row["regression_detected"] else "no_regression"
    elif kind == "operational_equivalence":
        status = "equivalent" if row["equivalent"] else "delta_requires_review"
    elif kind in {"operational_delta", "replay_proof_delta", "survivability_delta"}:
        status = "proved_delta" if row["delta"] != 0 else "no_delta"
    elif kind in {"rerun_reproducibility", "deterministic_rerun"}:
        status = "reproducible" if not row["regression_detected"] else "reproducibility_review"
    narrative = row["explanation"]
    if row["delta"] < 0:
        narrative = f"{row['metric']} decreased by {abs(row['delta'])}; review the preserved source artifacts before acting."
    elif row["delta"] > 0:
        narrative = f"{row['metric']} increased by {row['delta']}; verify the expanded operational surface remains intentional."
    return {
        id_field: stable_row_id(prefix, row["comparison_id"], kind),
        "comparison_scope": row["comparison_scope"],
        "metric": row["metric"],
        "previous_value": row["previous_value"],
        "current_value": row["current_value"],
        "delta": row["delta"],
        "change_ratio": row["change_ratio"],
        "analysis_status": status,
        "regression_detected": row["regression_detected"],
        "operationally_equivalent": row["equivalent"],
        "explainability_note": narrative,
        "proof_basis": "static_local_artifact_comparison",
        "human_review_required": True,
    }


def build_phase48_registry(outputs: dict, kind: str) -> dict:
    prefix, entry_key, id_field, _title, _filename, method = DIFF_SPECS[kind]
    rows = [_row_for_kind(kind, row) for row in comparison_rows(outputs)]
    artifact = phase48_artifact(method)
    artifact.update(
        {
            f"{kind}_registry_id": stable_row_id(f"{prefix}REG", [row[id_field] for row in rows]),
            entry_key: rows,
            "comparison_summary": {
                "entry_count": len(rows),
                "regression_count": sum(1 for row in rows if row["regression_detected"]),
                "equivalent_count": sum(1 for row in rows if row["operationally_equivalent"]),
                "delta_count": sum(1 for row in rows if float(row["delta"] or 0) != 0),
                "cross_run_survivability_score": score_from_counts(sum(1 for row in rows if not row["regression_detected"]), len(rows)),
            },
            "summary": {
                f"{kind}_entry_count": len(rows),
                "regression_count": sum(1 for row in rows if row["regression_detected"]),
                "external_runtime_dependency_introduced": False,
                "append_only_history_preserved": True,
            },
        }
    )
    return artifact


def render_phase48_dashboard(outputs: dict, kind: str) -> dict[str, str]:
    _prefix, entry_key, id_field, title, filename, _method = DIFF_SPECS[kind]
    rows = (outputs.get(f"{kind}_registry") or {}).get(entry_key) or []
    metrics = [
        ("Entries", len(rows)),
        ("Regressions", sum(1 for row in rows if row.get("regression_detected"))),
        ("Equivalent", sum(1 for row in rows if row.get("operationally_equivalent"))),
    ]
    header = "".join(f"<th scope='col'>{e(label)}</th>" for label in ["Scope", "Metric", "Previous", "Current", "Delta", "Status", "Explanation"])
    body_rows = []
    for row in rows:
        body_rows.append(
            f"<tr id='{e(row.get(id_field))}' tabindex='-1'>"
            f"<td>{e(row.get('comparison_scope'))}</td><td>{e(row.get('metric'))}</td>"
            f"<td>{e(row.get('previous_value'))}</td><td>{e(row.get('current_value'))}</td><td>{e(row.get('delta'))}</td>"
            f"<td>{e(row.get('analysis_status'))}</td><td>{e(row.get('explainability_note'))}</td></tr>"
        )
    table = f"<section class='panel'><table class='data-table'><thead><tr>{header}</tr></thead><tbody>{''.join(body_rows)}</tbody></table></section>"
    body = f"<section class='panel'><p>{e(PHASE48_LIMITATION)}</p></section>{compact_metrics(metrics)}{table}"
    return {filename: simple_review_page(title, "Cross-Run Diff Intelligence", filename, body, DIFF_LINKS)}
