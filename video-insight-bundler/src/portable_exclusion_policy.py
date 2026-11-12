"""Exclusion and privacy policy for portable review packages."""

from __future__ import annotations

from pathlib import Path
import re


def _has_name_token(name: str, tokens: tuple[str, ...]) -> bool:
    """Match artifact tokens, not substrings such as temporal or traceability."""
    parts = set(re.split(r"[^a-z0-9]+", name.lower()))
    return any(set(token.split("_")).issubset(parts) for token in tokens)

RAW_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
RAW_AUDIO_EXTENSIONS = {".wav", ".mp3", ".aac", ".flac", ".m4a"}
RAW_MEDIA_EXTENSIONS = RAW_VIDEO_EXTENSIONS | RAW_AUDIO_EXTENSIONS

CACHE_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".venv",
    "venv",
    "env",
    ".env",
    "portable_review_package",
    "exports",
}
RECURSIVE_PACKAGE_DIR_NAMES = {
    "portable_review_package",
    "portable_extract",
    "exports",
}
EXPORT_PROFILES = {"minimal", "review", "audit", "full", "executive", "presentation", "investigation", "diff_only"}

TEMP_EXTENSIONS = {".tmp", ".temp", ".bak", ".swp", ".part", ".pyc", ".pyo"}
TEMP_NAME_TOKENS = ("tmp", "temp", "ffmpeg_intermediate", "intermediate")
RISKY_NAME_TOKENS = (
    ".env",
    "id_rsa",
    "credentials",
    "credential",
    "token",
    "api_key",
    "apikey",
    "secret",
    "password",
    ".git/config",
)

KEEP_DISPLAY_EXTENSIONS = {
    ".html",
    ".htm",
    ".css",
    ".js",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".svg",
}
KEEP_ANALYSIS_EXTENSIONS = {
    ".json",
    ".md",
    ".csv",
    ".tsv",
    ".txt",
    ".srt",
    ".xml",
    ".yaml",
    ".yml",
    ".schema",
}
KEEP_EXTENSIONS = KEEP_DISPLAY_EXTENSIONS | KEEP_ANALYSIS_EXTENSIONS

REVIEW_JSON_TOKENS = (
    "summary",
    "manifest",
    "index",
    "dashboard",
    "interpretation",
    "recommendation",
    "evidence",
    "governance",
    "readiness",
    "timeline",
    "review",
    "validation",
    "report",
    "corpus",
    "graph",
)
AUDIT_JSON_TOKENS = REVIEW_JSON_TOKENS + (
    "schema",
    "provenance",
    "diff",
    "delta",
    "replay",
    "snapshot",
    "lineage",
)
MINIMAL_JSON_TOKENS = ("summary", "manifest", "validation", "dashboard", "index", "report")
LOW_LEVEL_REVIEW_TOKENS = (
    "schema",
    "raw",
    "cache",
    "debug",
    "trace",
    "registry",
    "packet",
    "lineage",
    "snapshot",
    "replay",
    "delta",
    "diff",
)


def _rel_parts(path: Path, source_root: Path) -> tuple[str, ...]:
    try:
        return tuple(part.lower() for part in path.relative_to(source_root).parts)
    except ValueError:
        return tuple(part.lower() for part in path.parts)


def is_raw_media(path: Path) -> bool:
    return path.suffix.lower() in RAW_MEDIA_EXTENSIONS


def is_privacy_risky(path: Path) -> bool:
    normalized = path.as_posix().lower()
    name = path.name.lower()
    return any(token in normalized or token == name for token in RISKY_NAME_TOKENS)


def _is_recursive_export_artifact(path: Path, source_root: Path) -> bool:
    parts = _rel_parts(path, source_root)
    name = path.name.lower()
    rel = "/".join(parts)
    if any(part in RECURSIVE_PACKAGE_DIR_NAMES for part in parts):
        return True
    if any(part.startswith("portable_review_package_") for part in parts):
        return True
    if any(part.startswith("portable_extract_") for part in parts):
        return True
    if any(part.startswith("portable_") and part.endswith("_package") for part in parts):
        return True
    if name in {"portable_review_package.zip"}:
        return True
    if name.startswith("portable_") and name.endswith("_package.zip"):
        return True
    if name.endswith("_portable_review_package.zip"):
        return True
    if any(part.endswith("_portable_review_package") for part in parts):
        return True
    if path.suffix.lower() == ".zip" and ("/exports/" in f"/{rel}/" or path.parent == source_root):
        return True
    return False


def _profile_exclusion(path: Path, source_root: Path, export_profile: str) -> tuple[bool, str, str]:
    rel = "/".join(_rel_parts(path, source_root))
    suffix = path.suffix.lower()
    name = path.name.lower()
    if export_profile == "full":
        return False, "", ""
    if export_profile == "audit":
        if suffix == ".json" and any(token in rel for token in AUDIT_JSON_TOKENS):
            return False, "", ""
        return False, "", ""
    if export_profile == "executive":
        if suffix in {".html", ".htm", ".css", ".js"}:
            return False, "", ""
        if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"} and any(token in rel for token in ("graph", "dashboard", "summary", "readiness")):
            return False, "", ""
        if suffix == ".md" and any(token in rel for token in ("summary", "report", "readme", "package")):
            return False, "", ""
        if suffix == ".json" and any(token in rel for token in ("summary", "dashboard", "governance", "recommendation", "readiness", "coherence", "pathway", "importance")):
            return False, "", ""
        return True, "Executive profile excludes detailed audit and machine artifacts.", "profile_executive_excludes_detail_artifacts"
    if export_profile == "presentation":
        if suffix in KEEP_DISPLAY_EXTENSIONS:
            return False, "", ""
        if suffix == ".md" and any(token in rel for token in ("summary", "report", "readme", "package")):
            return False, "", ""
        if suffix == ".json" and any(token in rel for token in ("summary", "dashboard", "recommendation", "governance", "pathway")):
            return False, "", ""
        return True, "Presentation profile keeps display surfaces and summary metadata only.", "profile_presentation_excludes_non_display"
    if export_profile == "investigation":
        if suffix in {".html", ".htm", ".css", ".js"}:
            if _has_name_token(rel, ("debug", "trace", "tmp", "cache")):
                return True, "Investigation profile excludes noisy debug surfaces.", "profile_investigation_excludes_debug"
            return False, "", ""
        if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}:
            if any(token in rel for token in ("evidence", "recommendation", "timeline", "governance", "interpretation", "validation", "graph", "dashboard")):
                return False, "", ""
            return True, "Investigation profile excludes unrelated display assets.", "profile_investigation_excludes_unfocused_display"
        if suffix == ".json" and any(token in rel for token in AUDIT_JSON_TOKENS + ("integrity", "reference", "orphan", "coherence")):
            return False, "", ""
        if suffix in {".md", ".csv", ".tsv", ".txt"} and any(token in rel for token in ("evidence", "recommendation", "timeline", "governance", "interpretation", "validation", "summary", "report", "review")):
            return False, "", ""
        if suffix == ".json":
            return True, "Investigation profile excludes unrelated machine JSON.", "profile_investigation_excludes_unfocused_json"
        return False, "", ""
    if export_profile == "diff_only":
        if suffix in {".html", ".htm", ".css", ".js"} and any(token in rel for token in ("delta", "diff", "route", "regression", "dashboard", "index")):
            return False, "", ""
        if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}:
            if any(token in rel for token in ("delta", "diff", "route", "regression")):
                return False, "", ""
        if suffix in {".json", ".md", ".csv", ".tsv", ".txt"} and any(token in rel for token in ("delta", "diff", "route", "regression", "validation", "manifest", "summary", "coherence")):
            return False, "", ""
        return True, "Diff-only profile keeps delta and regression review artifacts.", "profile_diff_only_excludes_non_delta"
    if export_profile == "minimal":
        if suffix in {".html", ".htm", ".css", ".js"}:
            return False, "", ""
        if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}:
            return False, "", ""
        if suffix == ".md" and any(token in rel for token in ("summary", "report", "readme", "package")):
            return False, "", ""
        if suffix == ".json" and any(token in rel for token in MINIMAL_JSON_TOKENS):
            return False, "", ""
        if suffix in {".csv", ".tsv"} and "review" in rel:
            return False, "", ""
        return True, "Minimal profile excludes non-essential review artifacts.", "profile_minimal_excludes_nonessential"
    if export_profile == "review":
        if suffix in KEEP_DISPLAY_EXTENSIONS or suffix in {".md", ".csv", ".tsv", ".txt"}:
            if _has_name_token(name, ("debug", "trace", "tmp")):
                return True, "Review profile excludes developer/debug artifacts.", "profile_review_excludes_debug"
            return False, "", ""
        if suffix == ".json":
            if any(token in rel for token in REVIEW_JSON_TOKENS) and not ("schemas/" in rel or name.endswith(".schema.json")):
                return False, "", ""
            if any(token in rel for token in LOW_LEVEL_REVIEW_TOKENS):
                return True, "Review profile excludes low-level machine/audit JSON.", "profile_review_excludes_low_level_json"
            return True, "Review profile excludes unclassified low-level JSON.", "profile_review_excludes_unclassified_json"
        if suffix in {".yaml", ".yml", ".xml", ".srt"}:
            return True, "Review profile excludes machine-side support artifacts.", "profile_review_excludes_support_artifact"
    return False, "", ""


def profile_inclusion_for(path: Path, source_root: Path, export_profile: str, include_raw_media: bool = False) -> dict:
    exclude, reason, rule = should_exclude_path(path, source_root, include_raw_media=include_raw_media, export_profile=export_profile)
    return {
        "profile": export_profile,
        "included": not exclude,
        "reason": reason or "Included by portable export profile.",
        "matched_rule": rule or f"profile_{export_profile}_include",
    }


def should_exclude_path(path: Path, source_root: Path, include_raw_media: bool = False, export_profile: str = "review") -> tuple[bool, str, str]:
    """Return ``(exclude, reason, matched_rule)`` for a source artifact."""

    if export_profile not in EXPORT_PROFILES:
        raise ValueError(f"Unknown export profile: {export_profile}")
    parts = _rel_parts(path, source_root)
    suffix = path.suffix.lower()
    if _is_recursive_export_artifact(path, source_root):
        return True, "Previous portable/export artifact is excluded to prevent recursive packaging.", "recursive_export_artifact"
    if any(part in CACHE_DIR_NAMES for part in parts):
        return True, "Development/cache directory is not needed for package review.", "cache_or_dependency_directory"
    if is_privacy_risky(path):
        return True, "Risky privacy/security filename is excluded by default.", "privacy_risky_filename"
    if suffix in RAW_VIDEO_EXTENSIONS and not include_raw_media:
        return True, "Raw source video is excluded by default.", "raw_video_excluded_by_default"
    if suffix in RAW_AUDIO_EXTENSIONS and not include_raw_media:
        return True, "Raw source audio is excluded by default.", "raw_audio_excluded_by_default"
    if suffix in RAW_MEDIA_EXTENSIONS and include_raw_media:
        return False, "", ""
    if suffix in TEMP_EXTENSIONS:
        return True, "Temporary or bytecode artifact is not needed for review.", "temporary_or_bytecode_file"
    if _has_name_token(path.name, TEMP_NAME_TOKENS):
        return True, "Temporary/intermediate artifact is not needed for review.", "temporary_or_intermediate_file"
    if suffix and suffix not in KEEP_EXTENSIONS:
        return True, "File type is not part of the portable review/display contract.", "unneeded_file_type"
    profile_excluded, profile_reason, profile_rule = _profile_exclusion(path, source_root, export_profile)
    if profile_excluded:
        return profile_excluded, profile_reason, profile_rule
    return False, "", ""


def build_exclusion_entry(path: Path, source_root: Path, reason: str, matched_rule: str) -> dict:
    size = path.stat().st_size if path.exists() and path.is_file() else 0
    suffix = path.suffix.lower()
    would_break_display = suffix in KEEP_DISPLAY_EXTENSIONS and not is_raw_media(path)
    would_break_analysis = suffix in KEEP_ANALYSIS_EXTENSIONS and not is_privacy_risky(path)
    return {
        "source_path": path.resolve().as_posix(),
        "source_relative_path": path.relative_to(source_root).as_posix() if path.is_relative_to(source_root) else path.as_posix(),
        "reason": reason,
        "file_size_bytes": size,
        "matched_rule": matched_rule,
        "would_break_display_if_excluded": would_break_display,
        "would_break_analysis_if_excluded": would_break_analysis,
    }
