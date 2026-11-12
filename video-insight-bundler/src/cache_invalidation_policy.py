"""Cache invalidation policy for portable incremental exports."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from asset_dependency_scanner import is_text_file
from stability import utc_now_iso, write_json

MISS_REASON_ORDER = [
    "source_missing",
    "cache_missing",
    "profile_policy_changed",
    "validation_tier_changed",
    "generation_mode_changed",
    "content_changed",
    "metadata_changed",
    "dependency_changed",
    "reference_changed",
    "forced_refresh",
    "unsafe_to_reuse",
]


def decide_reuse(
    *,
    current: dict,
    previous: dict | None,
    export_profile: str,
    validation_tier: str,
    generation_mode: str,
    cache_mode: str = "auto",
    source_exists: bool = True,
) -> dict:
    previous = previous if isinstance(previous, dict) else None
    reasons = []
    if cache_mode == "refresh":
        reasons.append("forced_refresh")
    if cache_mode == "off":
        reasons.append("unsafe_to_reuse")
    if not source_exists:
        reasons.append("source_missing")
    if not previous:
        reasons.append("cache_missing")
    else:
        if previous.get("export_profile") and previous.get("export_profile") != export_profile:
            reasons.append("profile_policy_changed")
        if previous.get("validation_tier") and previous.get("validation_tier") != validation_tier:
            reasons.append("validation_tier_changed")
        if previous.get("generation_mode") and previous.get("generation_mode") != generation_mode:
            reasons.append("generation_mode_changed")
        for key, reason in [
            ("content_hash", "content_changed"),
            ("metadata_hash", "metadata_changed"),
            ("dependency_hash", "dependency_changed"),
            ("reference_hash", "reference_changed"),
        ]:
            if current.get(key) != previous.get(key):
                reasons.append(reason)
    ordered = [reason for reason in MISS_REASON_ORDER if reason in set(reasons)]
    cache_hit = not ordered
    if cache_hit:
        decision = "reuse"
    elif set(ordered) <= {"validation_tier_changed"} and current.get("artifact_type") not in {"dashboard", "manifest", "schema"}:
        decision = "reuse_with_validation_refresh"
    else:
        decision = "refresh"
    return {
        "cache_hit": cache_hit,
        "cache_miss_reason": None if cache_hit else ordered[0],
        "invalidated_by": ordered,
        "reuse_eligible": cache_mode == "auto" and source_exists and "unsafe_to_reuse" not in ordered,
        "reuse_decision": decision,
        "reuse_safety_status": "safe" if decision.startswith("reuse") else ("unsafe" if "unsafe_to_reuse" in ordered else "refresh_required"),
    }


def write_cache_invalidation_report(package_root: Path, artifacts: list[dict]) -> dict:
    reasons = Counter(row.get("cache_miss_reason") or "cache_hit" for row in artifacts)
    text_skips = sum(1 for row in artifacts if row.get("cache_hit") and is_text_file(package_root / row["package_path"]))
    binary_skips = sum(1 for row in artifacts if row.get("cache_hit") and not is_text_file(package_root / row["package_path"]))
    report = {
        "analysis_status": "complete",
        "method": "cache_invalidation_policy_v67",
        "generated_at_utc": utc_now_iso(),
        "cache_miss_reasons": dict(sorted(reasons.items())),
        "unchanged_reference_skip_count": sum(1 for row in artifacts if row.get("cache_hit") and row.get("reference_hash")),
        "unchanged_text_file_skip_count": text_skips,
        "unchanged_binary_skip_count": binary_skips,
        "unchanged_governance_node_skip_count": sum(1 for row in artifacts if row.get("cache_hit") and "governance" in row["package_path"].lower()),
        "unchanged_validation_node_skip_count": sum(1 for row in artifacts if row.get("cache_hit") and "validation" in row["package_path"].lower()),
        "summary": {
            "artifact_count": len(artifacts),
            "cache_hit_count": sum(1 for row in artifacts if row.get("cache_hit")),
            "cache_miss_count": sum(1 for row in artifacts if not row.get("cache_hit")),
        },
    }
    write_json(package_root / "cache_invalidation_report.json", report)
    write_json(package_root / "validation" / "cache_invalidation_report.json", report)
    return report
