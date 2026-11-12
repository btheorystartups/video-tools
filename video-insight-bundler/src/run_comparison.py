"""Historical run comparison orchestration and local drift reports."""

from __future__ import annotations

import json
from pathlib import Path

from artifact_drift import compare_artifact_hashes
from metric_drift import compare_metrics, compare_readiness
from schema_validation import validate_against_schema
from schema_version_diff import compare_schema_versions
from stability import STATUS_COMPLETE, deterministic_id, utc_now_iso, write_json

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover
    plt = None


def _write_md(path: Path, title: str, report: dict, rows_key: str) -> None:
    lines = [f"# {title}", "", f"- Status: `{report.get('analysis_status')}`", f"- Previous run: `{report.get('previous_run_id')}`", f"- Current run: `{report.get('current_run_id')}`", ""]
    rows = report.get(rows_key) or []
    if rows:
        for row in rows[:80]:
            if isinstance(row, dict):
                label = row.get("artifact_path") or row.get("artifact") or row.get("metric") or row.get("classification")
                lines.append(f"- `{label}`: `{row.get('classification')}`")
            else:
                lines.append(f"- `{row}`")
    else:
        lines.append("- No drift detected.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _html(path: Path, title: str, report: dict) -> None:
    body = json.dumps(report, indent=2, ensure_ascii=False)
    path.write_text(f"<!doctype html><meta charset='utf-8'><title>{title}</title><link rel='stylesheet' href='../static_assets/report.css'><main class='main'><h1>{title}</h1><pre>{body}</pre></main>", encoding="utf-8")


def _png(path: Path, title: str, values: list[tuple[str, float]]) -> None:
    if not plt:
        path.write_bytes(b"")
        return
    fig, ax = plt.subplots(figsize=(9, 4), dpi=140)
    labels = [x[0] for x in values] or ["none"]
    nums = [x[1] for x in values] or [0]
    ax.bar(labels, nums, color="#47758f")
    ax.set_title(title, loc="left")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def compare_dependencies(previous: dict | None, current: dict) -> dict:
    if not previous:
        return {
            "report_version": "1.0",
            "analysis_status": STATUS_COMPLETE,
            "generated_at_utc": utc_now_iso(),
            "previous_run_id": None,
            "current_run_id": current.get("run_id"),
            "dependency_drift": [],
            "dependency_drift_count": 0,
        }
    old = (previous or {}).get("dependency_versions") or {}
    new = current.get("dependency_versions") or {}
    watched = {"ffmpeg", "opencv", "faster_whisper", "plotly", "librosa", "sklearn"}
    rows = []
    for name in sorted(watched | set(old) | set(new)):
        if name not in watched:
            continue
        if old.get(name) != new.get(name):
            rows.append({"dependency": name, "previous_version": old.get(name), "current_version": new.get(name), "classification": "dependency_drift"})
    return {
        "report_version": "1.0",
        "analysis_status": STATUS_COMPLETE,
        "generated_at_utc": utc_now_iso(),
        "previous_run_id": (previous or {}).get("run_id"),
        "current_run_id": current.get("run_id"),
        "dependency_drift": rows,
        "dependency_drift_count": len(rows),
    }


def compare_runs(root: Path, previous: dict | None, current: dict, schema_dir: Path) -> dict:
    history = root / "history"
    reports = root / "reports"
    graphs = root / "graphs"
    visualizations = root / "visualizations"
    evidence = root / "verification_evidence"
    for directory in (history, reports, graphs, visualizations, evidence):
        directory.mkdir(exist_ok=True)

    comparison_id = deterministic_id("comparison", (previous or {}).get("run_id"), current.get("run_id"), current.get("source_sha256"), current.get("profile_hash"), length=20)
    artifact = compare_artifact_hashes(previous, current)
    metric = compare_metrics(previous, current)
    schema = compare_schema_versions(previous, current)
    dependency = compare_dependencies(previous, current)
    readiness = compare_readiness(previous, current)
    suspicious = []
    if previous:
        if previous.get("source_sha256") != current.get("source_sha256"):
            suspicious.append("source_sha_changed")
        if previous.get("profile_hash") != current.get("profile_hash"):
            suspicious.append("profile_hash_changed")
    suspicious.extend(["schema_downgrade"] * schema.get("schema_downgrade_count", 0))
    suspicious.extend(["missing_artifact"] * artifact.get("missing_artifact_count", 0))
    comparison = {
        "comparison_schema_version": "1.0",
        "analysis_status": STATUS_COMPLETE,
        "generated_at_utc": utc_now_iso(),
        "comparison_id": comparison_id,
        "previous_run_id": (previous or {}).get("run_id"),
        "current_run_id": current.get("run_id"),
        "drift_summary": {
            "artifact_drift_count": artifact.get("changed_artifact_count"),
            "meaningful_metric_drift_count": metric.get("meaningful_metric_drift_count"),
            "dependency_drift_count": dependency.get("dependency_drift_count"),
            "schema_downgrade_count": schema.get("schema_downgrade_count"),
            "readiness_class_changed": readiness.get("class_changed"),
            "suspicious_drift_count": len(suspicious),
        },
        "drift_causes": {
            "source_changed": previous is not None and previous.get("source_sha256") != current.get("source_sha256"),
            "profile_changed": previous is not None and previous.get("profile_hash") != current.get("profile_hash"),
            "dependency_changed": dependency.get("dependency_drift_count", 0) > 0,
            "schema_changed": bool(schema.get("schema_version_diffs")),
        },
        "classification": "suspicious_drift" if suspicious else ("no_previous_run" if not previous else "expected_or_explained_drift"),
        "suspicious_drift": suspicious,
    }
    for name, data in [
        ("run_comparison.json", comparison),
        ("artifact_drift_report.json", artifact),
        ("metric_drift_report.json", metric),
        ("schema_version_diff.json", schema),
        ("dependency_drift_report.json", dependency),
        ("readiness_drift_report.json", readiness),
    ]:
        write_json(history / name, data)
    _write_md(reports / "artifact_drift_report.md", "Artifact Drift Report", artifact, "artifact_drift")
    _write_md(reports / "metric_drift_report.md", "Metric Drift Report", metric, "metric_drift")
    _write_md(reports / "readiness_drift_report.md", "Readiness Drift Report", readiness, "readiness_drift")
    _write_md(reports / "run_history_report.md", "Run History Report", comparison, "suspicious_drift")
    _html(visualizations / "run_history.html", "Run History", comparison)
    _html(visualizations / "artifact_drift.html", "Artifact Drift", artifact)
    _html(visualizations / "metric_drift.html", "Metric Drift", metric)
    _html(visualizations / "readiness_drift.html", "Readiness Drift", readiness)
    _png(graphs / "metric_drift_heatmap.png", "Metric Drift", [(row["metric"], abs(row.get("delta") or 0)) for row in metric.get("metric_drift", [])])
    _png(graphs / "artifact_drift_matrix.png", "Artifact Drift", [("changed", artifact.get("changed_artifact_count") or 0), ("suspicious", artifact.get("suspicious_drift_count") or 0)])
    _png(graphs / "readiness_drift_timeline.png", "Readiness Drift", [("previous", (readiness.get("previous_readiness") or {}).get("score") or 0), ("current", (readiness.get("current_readiness") or {}).get("score") or 0)])
    _png(graphs / "dependency_drift_timeline.png", "Dependency Drift", [("changed", dependency.get("dependency_drift_count") or 0)])
    validations = [
        validate_against_schema(comparison, schema_dir / "run_comparison.schema.json"),
        validate_against_schema(artifact, schema_dir / "artifact_drift_report.schema.json"),
        validate_against_schema(metric, schema_dir / "metric_drift_report.schema.json"),
        validate_against_schema(schema, schema_dir / "schema_version_diff.schema.json"),
    ]
    write_json(evidence / "history_validation.json", {"validation_status": "complete" if all(v.get("validation_status") == "complete" for v in validations) else "error", "validations": validations})
    return comparison
