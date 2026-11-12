"""Longitudinal editorial intelligence orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean, pstdev

from anomaly_clustering import build_anomaly_clusters
from confidence_volatility import build_confidence_volatility
from persistent_patterns import build_persistent_patterns
from recommendation_evolution import build_recommendation_evolution
from schema_validation import validate_against_schema
from semantic_evolution import build_semantic_evolution
from stability import STATUS_COMPLETE, STATUS_LIMITED, deterministic_id, utc_now_iso, write_json
from trend_analysis import build_trend_analysis

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover
    plt = None


LONGITUDINAL_JSON = {
    "longitudinal_analysis": "longitudinal_analysis.json",
    "trend_analysis": "trend_analysis.json",
    "confidence_volatility": "confidence_volatility.json",
    "recommendation_evolution": "recommendation_evolution.json",
    "anomaly_clusters": "anomaly_clusters.json",
    "persistent_patterns": "persistent_patterns.json",
    "semantic_evolution": "semantic_evolution.json",
}

LONGITUDINAL_GRAPHS = [
    "readiness_trend.png",
    "continuity_trend.png",
    "contradiction_trend.png",
    "confidence_volatility_curve.png",
    "recommendation_evolution_map.png",
    "persistent_weakness_heatmap.png",
    "anomaly_cluster_graph.png",
    "discourse_evolution_timeline.png",
    "semantic_readiness_timeline.png",
]


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _metric(snapshot: dict, key: str):
    if key == "readiness_score":
        return (snapshot.get("readiness") or {}).get("score")
    return (snapshot.get("key_metrics") or {}).get(key)


def _values(snapshots: list[dict], key: str) -> list[float]:
    values = []
    for row in snapshots:
        try:
            value = _metric(row, key)
            if value is not None:
                values.append(float(value))
        except (TypeError, ValueError):
            pass
    return values


def build_longitudinal_analysis(
    snapshots: list[dict],
    trend_report: dict,
    volatility_report: dict,
    recommendation_report: dict,
    anomaly_report: dict,
    persistent_report: dict,
) -> dict:
    stable_metrics = []
    unstable_metrics = []
    for row in trend_report.get("trends", []):
        if row.get("classification") == "stable":
            stable_metrics.append(row.get("metric"))
        if row.get("classification") in {"volatile", "degrading"}:
            unstable_metrics.append(row.get("metric"))
    recurring_issues = []
    recurring_issues.extend(row.get("pattern_type") for row in persistent_report.get("patterns", []) if row.get("is_persistent"))
    recurring_issues.extend(row.get("cluster_type") for row in anomaly_report.get("anomaly_clusters", []) if row.get("item_count", 0) > 0)
    strengths = []
    for key in ("readiness_score", "ambiguity_adjusted_continuity", "visual_continuity_score", "artifact_integrity_score"):
        values = _values(snapshots, key)
        if len(values) >= 2 and mean(values) >= 0.72 and (pstdev(values) if len(values) > 1 else 0.0) <= 0.08:
            strengths.append({"metric": key, "mean": round(mean(values), 3), "stability": "stable"})
    longitudinal_confidence = round(
        min(1.0, (len(snapshots) / 5.0) * 0.55 + (len(stable_metrics) / max(len(trend_report.get("trends") or []), 1)) * 0.45),
        3,
    )
    return {
        "longitudinal_analysis_version": "1.0",
        "analysis_status": STATUS_COMPLETE if len(snapshots) >= 3 else STATUS_LIMITED,
        "generated_at_utc": utc_now_iso(),
        "tracked_runs": [
            {
                "run_id": row.get("run_id"),
                "timestamp_utc": row.get("timestamp_utc"),
                "source_sha256": row.get("source_sha256"),
                "profile_hash": row.get("profile_hash"),
                "readiness_score": (row.get("readiness") or {}).get("score"),
                "readiness_class": (row.get("readiness") or {}).get("class"),
            }
            for row in snapshots
        ],
        "run_lineage": {
            "lineage_id": deterministic_id("long_lineage", [row.get("run_id") for row in snapshots], length=16),
            "run_count": len(snapshots),
            "source_sha256_values": sorted({row.get("source_sha256") for row in snapshots if row.get("source_sha256")}),
            "profile_hash_values": sorted({row.get("profile_hash") for row in snapshots if row.get("profile_hash")}),
        },
        "trend_windows": trend_report.get("trend_windows", []),
        "stable_metrics": stable_metrics,
        "unstable_metrics": unstable_metrics,
        "recurring_issues": sorted(set(item for item in recurring_issues if item)),
        "persistent_strengths": strengths,
        "readiness_evolution": _run_metric_rows(snapshots, "readiness_score"),
        "continuity_evolution": _run_metric_rows(snapshots, "ambiguity_adjusted_continuity"),
        "contradiction_evolution": _run_metric_rows(snapshots, "false_positive_boundary_ratio"),
        "recommendation_evolution": recommendation_report.get("recommendation_confidence_evolution", []),
        "integrity_evolution": _run_metric_rows(snapshots, "artifact_integrity_score"),
        "discourse_evolution": {
            "argument_completeness": _run_metric_rows(snapshots, "argument_completeness_score"),
            "callback_quality": _run_metric_rows(snapshots, "callback_resolution_quality"),
        },
        "visual_evidence_evolution": _run_metric_rows(snapshots, "visual_continuity_score"),
        "longitudinal_summary": {
            "tracked_run_count": len(snapshots),
            "stable_metric_count": len(stable_metrics),
            "unstable_metric_count": len(unstable_metrics),
            "recurring_issue_count": len(set(recurring_issues)),
            "volatility_score": volatility_report.get("volatility_score"),
            "persistent_pattern_pressure": (persistent_report.get("persistent_pattern_summary") or {}).get("persistent_pattern_pressure"),
        },
        "longitudinal_confidence": longitudinal_confidence,
        "limitations": [
            "Longitudinal analysis uses retained local snapshots and current generated artifacts only.",
            "It is deterministic editorial review evidence, not prediction or autonomous decision-making.",
        ],
    }


def _run_metric_rows(snapshots: list[dict], key: str) -> list[dict]:
    rows = []
    for snapshot in snapshots:
        value = _metric(snapshot, key)
        rows.append({"run_id": snapshot.get("run_id"), "value": value})
    return rows


def write_longitudinal_outputs(output_dir: Path, snapshots: list[dict], schema_dir: Path) -> dict:
    longitudinal_dir = output_dir / "longitudinal"
    reports_dir = output_dir / "reports"
    graphs_dir = output_dir / "graphs"
    vis_dir = output_dir / "visualizations"
    evidence_dir = output_dir / "verification_evidence"
    for directory in (longitudinal_dir, reports_dir, graphs_dir, vis_dir, evidence_dir):
        directory.mkdir(exist_ok=True)

    current_recommendations = read_json(output_dir / "recommendations.json")
    current_consensus = read_json(output_dir / "consensus" / "evidence_consensus.json")
    current_boundary = read_json(output_dir / "continuity" / "boundary_diagnostics.json")

    trend = build_trend_analysis(snapshots)
    volatility = build_confidence_volatility(snapshots, trend)
    recommendation = build_recommendation_evolution(snapshots, current_recommendations)
    anomaly = build_anomaly_clusters(snapshots, current_consensus, current_boundary, current_recommendations)
    persistent = build_persistent_patterns(snapshots, anomaly, recommendation)
    semantic = build_semantic_evolution()
    longitudinal = build_longitudinal_analysis(snapshots, trend, volatility, recommendation, anomaly, persistent)
    summary = {
        "longitudinal_summary_version": "1.0",
        "analysis_status": longitudinal.get("analysis_status"),
        "generated_at_utc": utc_now_iso(),
        "tracked_run_count": len(snapshots),
        "longitudinal_confidence": longitudinal.get("longitudinal_confidence"),
        "trend_class_counts": trend.get("trend_class_counts"),
        "volatility_score": volatility.get("volatility_score"),
        "persistent_pattern_pressure": (persistent.get("persistent_pattern_summary") or {}).get("persistent_pattern_pressure"),
        "active_anomaly_cluster_count": (anomaly.get("cluster_summary") or {}).get("active_cluster_count"),
        "semantic_scaffold_status": semantic.get("analysis_status"),
        "classification_guidance": "operational beta+",
        "limitations": longitudinal.get("limitations", []),
    }
    outputs = {
        "longitudinal_analysis": longitudinal,
        "trend_analysis": trend,
        "confidence_volatility": volatility,
        "recommendation_evolution": recommendation,
        "anomaly_clusters": anomaly,
        "persistent_patterns": persistent,
        "semantic_evolution": semantic,
        "longitudinal_summary": summary,
    }
    for key, filename in {**LONGITUDINAL_JSON, "longitudinal_summary": "longitudinal_summary.json"}.items():
        write_json(longitudinal_dir / filename, outputs[key])
    _write_reports(reports_dir, outputs)
    _write_graphs(graphs_dir, outputs)
    _write_visualizations(vis_dir, outputs)
    validations = _validate_longitudinal_outputs(longitudinal_dir, schema_dir, outputs)
    write_json(evidence_dir / "longitudinal_validation.json", validations)
    _update_readiness(output_dir, outputs)
    _update_consensus(output_dir, outputs)
    return outputs


def _write_reports(reports_dir: Path, outputs: dict) -> None:
    for key, filename in [
        ("longitudinal_analysis", "longitudinal_analysis_report.md"),
        ("trend_analysis", "trend_analysis_report.md"),
        ("confidence_volatility", "confidence_volatility_report.md"),
        ("recommendation_evolution", "recommendation_evolution_report.md"),
        ("anomaly_clusters", "anomaly_clusters_report.md"),
        ("persistent_patterns", "persistent_patterns_report.md"),
        ("semantic_evolution", "semantic_evolution_report.md"),
    ]:
        data = outputs[key]
        title = key.replace("_", " ").title()
        lines = [
            f"# {title}",
            "",
            "Longitudinal and semantic-evolution outputs are deterministic historical-analysis heuristics intended for editorial review and system explainability. They are not semantic truth systems, predictive systems, or autonomous editorial agents.",
            "",
            f"- Status: `{data.get('analysis_status')}`",
            f"- Generated: `{data.get('generated_at_utc')}`",
            f"- Tracked runs: `{data.get('tracked_run_count', data.get('tracked_runs') and len(data.get('tracked_runs')) )}`",
            "",
            "## Summary",
            "",
        ]
        summary = data.get("longitudinal_summary") or data.get("cluster_summary") or data.get("persistent_pattern_summary") or data.get("recommendation_stability") or data.get("trend_class_counts") or {}
        if isinstance(summary, dict):
            lines.extend(f"- `{k}`: `{v}`" for k, v in summary.items())
        else:
            lines.append(f"- `{summary}`")
        lines.extend(["", "## Limitations", ""])
        lines.extend(f"- {item}" for item in data.get("limitations", []))
        (reports_dir / filename).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _plot_line(path: Path, title: str, rows: list[dict], ylabel: str = "Score") -> None:
    if not plt:
        path.write_bytes(b"")
        return
    values = [row.get("value") for row in rows if row.get("value") is not None]
    labels = [str(index + 1) for index, row in enumerate(rows) if row.get("value") is not None]
    if not values:
        values = [0.0]
        labels = ["none"]
    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=140)
    ax.plot(labels, values, marker="o", linewidth=2, color="#386b8f")
    ax.set_title(title, loc="left")
    ax.set_xlabel("Run")
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _plot_bar(path: Path, title: str, rows: list[tuple[str, float]]) -> None:
    if not plt:
        path.write_bytes(b"")
        return
    labels = [row[0] for row in rows] or ["none"]
    values = [row[1] for row in rows] or [0.0]
    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=140)
    ax.bar(labels, values, color="#5d7f62")
    ax.set_title(title, loc="left")
    ax.set_ylim(0, 1)
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _write_graphs(graphs_dir: Path, outputs: dict) -> None:
    long = outputs["longitudinal_analysis"]
    _plot_line(graphs_dir / "readiness_trend.png", "Readiness Trend", long.get("readiness_evolution") or [])
    _plot_line(graphs_dir / "continuity_trend.png", "Continuity Trend", long.get("continuity_evolution") or [])
    _plot_line(graphs_dir / "contradiction_trend.png", "Contradiction Trend", long.get("contradiction_evolution") or [])
    _plot_bar(
        graphs_dir / "confidence_volatility_curve.png",
        "Confidence Volatility",
        [(row.get("metric"), row.get("volatility") or 0.0) for row in outputs["confidence_volatility"].get("volatility_regions", [])[:12]],
    )
    _plot_line(graphs_dir / "recommendation_evolution_map.png", "Recommendation Evolution", [
        {"value": row.get("recommendation_count")} for row in outputs["recommendation_evolution"].get("recommendation_confidence_evolution", [])
    ], "Count")
    _plot_bar(
        graphs_dir / "persistent_weakness_heatmap.png",
        "Persistent Weakness Heatmap",
        [(row.get("pattern_type"), row.get("pressure") or 0.0) for row in outputs["persistent_patterns"].get("patterns", [])],
    )
    _plot_bar(
        graphs_dir / "anomaly_cluster_graph.png",
        "Anomaly Cluster Graph",
        [(row.get("cluster_type"), row.get("cluster_pressure") or 0.0) for row in outputs["anomaly_clusters"].get("anomaly_clusters", [])],
    )
    _plot_line(graphs_dir / "discourse_evolution_timeline.png", "Discourse Evolution", (long.get("discourse_evolution") or {}).get("argument_completeness") or [])
    _plot_bar(graphs_dir / "semantic_readiness_timeline.png", "Semantic Readiness Timeline", [("scaffold", 1.0), ("future_hooks", 0.0)])


def _write_visualizations(vis_dir: Path, outputs: dict) -> None:
    links = "".join(
        f"<a href='{name}.html'>{name.replace('_', ' ').title()}</a>"
        for name in ["longitudinal_analysis", "trend_analysis", "confidence_volatility", "recommendation_evolution", "anomaly_clusters", "persistent_patterns", "semantic_evolution"]
    )
    graph_map = {
        "longitudinal_analysis": "readiness_trend.png",
        "trend_analysis": "continuity_trend.png",
        "confidence_volatility": "confidence_volatility_curve.png",
        "recommendation_evolution": "recommendation_evolution_map.png",
        "anomaly_clusters": "anomaly_cluster_graph.png",
        "persistent_patterns": "persistent_weakness_heatmap.png",
        "semantic_evolution": "semantic_readiness_timeline.png",
    }
    for key, graph in graph_map.items():
        data = outputs[key]
        title = key.replace("_", " ").title()
        body = json.dumps(data, indent=2, ensure_ascii=False).replace("&", "&amp;").replace("<", "&lt;")
        page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><link rel="stylesheet" href="../static_assets/report.css"></head>
<body><aside class="sidebar"><div class="brand">Longitudinal</div><nav><a href="dashboard.html">Dashboard</a>{links}</nav></aside>
<main class="main"><header class="page-header"><p>Longitudinal Intelligence</p><h1>{title}</h1></header>
<figure class="graph"><img src="../graphs/{graph}" alt="{title}"></figure><section class="panel"><pre>{body}</pre></section></main></body></html>
"""
        (vis_dir / f"{key}.html").write_text(page, encoding="utf-8")


def _validate_longitudinal_outputs(longitudinal_dir: Path, schema_dir: Path, outputs: dict) -> dict:
    validations = []
    for key, filename in LONGITUDINAL_JSON.items():
        schema_path = schema_dir / f"{key}.schema.json"
        if schema_path.exists():
            validations.append({"artifact": f"longitudinal/{filename}", **validate_against_schema(outputs[key], schema_path)})
        else:
            validations.append({"artifact": f"longitudinal/{filename}", "validation_status": STATUS_LIMITED, "error_count": 1, "errors": [{"path": "$", "message": "Schema missing."}]})
    referenced_runs = {row.get("run_id") for row in outputs["longitudinal_analysis"].get("tracked_runs", [])}
    reference_errors = []
    for rows_key in ("readiness_evolution", "continuity_evolution", "contradiction_evolution"):
        for row in outputs["longitudinal_analysis"].get(rows_key, []):
            if row.get("run_id") not in referenced_runs:
                reference_errors.append({"path": rows_key, "message": f"Unknown run reference: {row.get('run_id')}"})
    validations.append(
        {
            "artifact": "longitudinal/reference_checks",
            "validation_status": STATUS_COMPLETE if not reference_errors else "error",
            "error_count": len(reference_errors),
            "errors": reference_errors,
        }
    )
    return {
        "validation_status": STATUS_COMPLETE if all(row.get("validation_status") == STATUS_COMPLETE for row in validations) else "error",
        "generated_at_utc": utc_now_iso(),
        "validations": validations,
        "historical_reference_count": len(referenced_runs),
        "limitations": ["Validation checks local JSON schemas and deterministic run references."],
    }


def _update_readiness(output_dir: Path, outputs: dict) -> None:
    path = output_dir / "revision_graph" / "release_readiness_report.json"
    readiness = read_json(path)
    if not readiness:
        return
    volatility_score = float(outputs["confidence_volatility"].get("volatility_score") or 0.0)
    persistent_pressure = float((outputs["persistent_patterns"].get("persistent_pattern_summary") or {}).get("persistent_pattern_pressure") or 0.0)
    anomaly_pressure = float((outputs["anomaly_clusters"].get("cluster_summary") or {}).get("active_cluster_count") or 0.0) / 6.0
    historical_stability = round(max(0.0, 1.0 - max(volatility_score, persistent_pressure, anomaly_pressure)), 3)
    components = {
        "historical_stability": historical_stability,
        "confidence_volatility": round(max(0.0, 1.0 - volatility_score), 3),
        "recurring_issue_pressure": round(max(0.0, 1.0 - persistent_pressure), 3),
        "persistent_contradiction_pressure": round(max(0.0, 1.0 - anomaly_pressure), 3),
        "chronic_weak_boundaries": round(max(0.0, 1.0 - persistent_pressure), 3),
        "longitudinal_recommendation_stability": 1.0 if (outputs["recommendation_evolution"].get("recommendation_stability") or {}).get("stability_class") == "stable" else 0.72,
        "anomaly_clustering_pressure": round(max(0.0, 1.0 - anomaly_pressure), 3),
    }
    readiness.setdefault("score_components", {}).update(components)
    readiness["longitudinal_inputs"] = {
        "longitudinal_summary": outputs["longitudinal_summary"],
        "readiness_note": "Stable repeated runs improve confidence only conservatively; volatility and persistent pressure can only hold down readiness.",
    }
    base = float(readiness.get("release_readiness_score") or 0.0)
    longitudinal_mean = mean(components.values())
    readiness["release_readiness_score"] = round(min(base, (base * 0.9) + (longitudinal_mean * 0.1)), 3)
    blocking = readiness.setdefault("blocking_issues", [])
    message = "Longitudinal history shows persistent or volatile editorial pressure."
    if (volatility_score >= 0.32 or persistent_pressure >= 0.34 or anomaly_pressure >= 0.5) and message not in blocking:
        blocking.append(message)
    if blocking or readiness["release_readiness_score"] < 0.5:
        readiness["release_readiness_class"] = "not_ready"
    elif readiness["release_readiness_score"] < 0.68:
        readiness["release_readiness_class"] = "review_ready"
    elif readiness["release_readiness_score"] < 0.82:
        readiness["release_readiness_class"] = "dry_run_ready"
    else:
        readiness["release_readiness_class"] = "release_candidate"
    write_json(path, readiness)
    graph_path = output_dir / "revision_graph" / "revision_graph.json"
    graph = read_json(graph_path)
    if graph:
        graph["release_readiness"] = readiness
        write_json(graph_path, graph)


def _update_consensus(output_dir: Path, outputs: dict) -> None:
    path = output_dir / "consensus" / "evidence_consensus.json"
    consensus = read_json(path)
    if not consensus:
        return
    volatility_score = float(outputs["confidence_volatility"].get("volatility_score") or 0.0)
    persistent_pressure = float((outputs["persistent_patterns"].get("persistent_pattern_summary") or {}).get("persistent_pattern_pressure") or 0.0)
    anomaly_pressure = float((outputs["anomaly_clusters"].get("cluster_summary") or {}).get("active_cluster_count") or 0.0) / 6.0
    adjustment = round(min(0.18, volatility_score * 0.08 + persistent_pressure * 0.07 + anomaly_pressure * 0.06), 3)
    for row in consensus.get("consensus_items", []):
        base = float(row.get("consensus_score") or 0.0)
        if row.get("consensus_class") in {"disagreement", "weak_agreement"} or row.get("conflicting_modalities"):
            row["volatility_adjusted_confidence"] = round(max(0.0, base - adjustment), 3)
            row.setdefault("evidence_notes", []).append("Historical volatility and persistent-pattern pressure conservatively reduce confidence.")
        else:
            row["volatility_adjusted_confidence"] = round(max(0.0, base - adjustment * 0.35), 3)
    consensus["longitudinal_consensus_inputs"] = {
        "historical_agreement_stability": round(max(0.0, 1.0 - volatility_score), 3),
        "recurring_contradiction_regions": outputs["anomaly_clusters"].get("anomaly_clusters", []),
        "chronic_continuity_patterns": outputs["persistent_patterns"].get("patterns", []),
        "volatility_adjustment": adjustment,
        "persistent_weakness_penalty": persistent_pressure,
        "limitations": ["Longitudinal consensus adjustment is conservative review evidence; it does not change media or boundaries."],
    }
    write_json(path, consensus)
