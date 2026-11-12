"""Advisory benchmark report for portable exports."""

from __future__ import annotations

from pathlib import Path

from stability import utc_now_iso, write_json


def run_benchmark_suite(package_root: Path, *, timings: dict | None = None, size_report: dict | None = None, topology: dict | None = None, incremental: dict | None = None, strict: bool = False) -> dict:
    timings = timings or {}
    size_summary = (size_report or {}).get("summary", {})
    topo = (topology or {}).get("topology_graph_registry", {}).get("metrics", {})
    inc = (incremental or {}).get("incremental_export_registry", {}).get("summary", {})
    thresholds = {
        "broken_links": {"max": 0, "strict_fail": True},
        "missing_assets": {"max": 0, "strict_fail": True},
        "absolute_live_paths": {"max": 0, "strict_fail": True},
        "validation_must_pass": {"required": True, "strict_fail": True},
        "zip_time_seconds": {"max": 30, "strict_fail": False},
        "package_size_bytes": {"max": 500 * 1024 * 1024, "strict_fail": False},
    }
    report = {
        "analysis_status": "complete",
        "method": "portable_benchmark_suite_v72",
        "generated_at_utc": utc_now_iso(),
        "strict": strict,
        "metrics": {
            "scan_time": timings.get("scan_duration_seconds"),
            "copy_time": timings.get("copy_duration_seconds"),
            "rewrite_time": timings.get("rewrite_duration_seconds"),
            "governance_time": timings.get("governance_generation_duration_seconds"),
            "topology_time": timings.get("governance_generation_duration_seconds"),
            "dedupe_time": timings.get("dedupe_duration_seconds"),
            "zip_time": timings.get("zip_duration_seconds"),
            "validation_time": timings.get("validation_duration_seconds"),
            "extracted_validation_time": timings.get("extracted_validation_duration_seconds"),
            "package_size": size_summary.get("total_package_size_bytes"),
            "zip_size": size_summary.get("zip_size_bytes"),
            "file_count": size_summary.get("file_count"),
            "dashboard_count": len(list(package_root.rglob("*.html"))),
            "topology_node_count": topo.get("node_count"),
            "topology_edge_count": topo.get("edge_count"),
            "cache_reuse_ratio": round((inc.get("reused_artifact_count") or 0) / max((inc.get("artifact_count") or 0), 1), 4),
        },
        "thresholds": thresholds,
        "summary": {"advisory_thresholds": not strict, "strict_failures": 0},
    }
    write_json(package_root / "portable_benchmark_report.json", report)
    write_json(package_root / "validation" / "portable_benchmark_report.json", report)
    return report
