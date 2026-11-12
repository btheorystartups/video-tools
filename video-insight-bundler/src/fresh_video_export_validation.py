"""Fresh-video export validation for one-command portable exports."""

from __future__ import annotations

import json
from pathlib import Path

from stability import utc_now_iso, write_json


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def validate_fresh_video_export(
    analysis_root: Path,
    requested_video: Path,
    *,
    export_started_at: str | None = None,
    strict: bool = True,
) -> dict:
    root = analysis_root.resolve()
    requested = requested_video.resolve()
    requested_name = requested.name.lower()
    refs: list[str] = []
    for path in sorted(root.rglob("*.json"))[:5000]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if requested_name in text.lower() or requested.as_posix().lower() in text.lower():
            refs.append(path.relative_to(root).as_posix())
    manifest = _load_json(root / "corpus_run_manifest.json") or _load_json(root / "run_manifest.json")
    generated_at = manifest.get("generated_at_utc") or manifest.get("generation_timestamp")
    warnings: list[str] = []
    if not refs:
        warnings.append("Requested video name was not found in sampled analysis JSON metadata.")
    if export_started_at and generated_at and generated_at < export_started_at:
        warnings.append("Analysis timestamp appears older than export start.")
    old_package_excluded = not any(
        path.name == "portable_review_package.zip" or "portable_review_package" in path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.exists() and path != root / "portable_review_package"
    )
    if not old_package_excluded:
        warnings.append("Old package artifacts were detected near analysis outputs.")
    passed = not warnings or not strict
    report = {
        "analysis_status": "complete" if passed else "error",
        "method": "fresh_video_export_validation_v1",
        "generated_at_utc": utc_now_iso(),
        "requested_video": requested.as_posix(),
        "analysis_root": root.as_posix(),
        "analysis_video_refs": refs[:250],
        "analysis_generation_timestamp": generated_at,
        "export_generation_timestamp": export_started_at,
        "fresh_analysis_confirmed": bool(refs) and not any("older than export start" in warning for warning in warnings),
        "stale_artifact_warnings": warnings,
        "old_package_excluded": old_package_excluded,
        "pass_fail": "pass" if passed else "fail",
    }
    evidence = root / "verification_evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    write_json(evidence / "fresh_video_export_validation.json", report)
    return report
