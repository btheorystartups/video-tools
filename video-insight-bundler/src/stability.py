"""Deterministic hashing and status helpers for analysis stabilization."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TOOL_VERSION = "0.2.0"

STATUS_COMPLETE = "complete"
STATUS_LIMITED = "limited"
STATUS_UNAVAILABLE = "unavailable"
STATUS_ERROR = "error"
STATUS_SKIPPED = "skipped"

VALID_STATUSES = {
    STATUS_COMPLETE,
    STATUS_LIMITED,
    STATUS_UNAVAILABLE,
    STATUS_ERROR,
    STATUS_SKIPPED,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_profile(profile: dict) -> str:
    return sha256_text(canonical_json(profile))


def deterministic_id(prefix: str, *parts: Any, length: int = 16) -> str:
    digest = sha256_text("|".join(str(part) for part in parts))
    return f"{prefix}_{digest[:length]}"


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def normalize_status(status: Any) -> str:
    if status in VALID_STATUSES:
        return str(status)
    if status == "ok":
        return STATUS_COMPLETE
    if status in (None, ""):
        return STATUS_UNAVAILABLE
    return STATUS_ERROR


def warning(code: str, message: str, severity: str = "warning", subsystem: str | None = None) -> dict:
    item = {
        "code": code,
        "severity": severity,
        "message": message,
    }
    if subsystem:
        item["subsystem"] = subsystem
    return item
