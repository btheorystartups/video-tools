"""Cross-artifact reference validation for generated local analysis bundles."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from stability import STATUS_COMPLETE, STATUS_ERROR, utc_now_iso, write_json

ID_KEYS = {
    "segment_id",
    "from_segment_id",
    "to_segment_id",
    "transition_id",
    "boundary_id",
    "revision_id",
    "parent_revision_id",
    "root_revision_id",
    "candidate_id",
    "from_node_id",
    "to_node_id",
    "node_id",
    "callback_id",
    "setup_segment_id",
    "payoff_segment_id",
}

PATH_KEYS = {
    "path",
    "artifact",
    "schema",
    "schema_path",
    "image_path",
    "href",
    "src",
    "report",
}

EXPECTED_CORE_ARTIFACTS = [
    "manifest.json",
    "analysis_index.json",
    "llm_context_bundle.json",
    "transcript.json",
    "scene_segments.json",
    "recommendations.json",
    "consensus/evidence_consensus.json",
    "consensus/transition_confidence.json",
    "discourse/argument_graph.json",
    "revision_graph/revision_graph.json",
    "revision_graph/release_readiness_report.json",
    "visualizations/dashboard.html",
]


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def json_files(root: Path) -> list[Path]:
    skipped = {".git", "__pycache__", ".pytest_cache"}
    return sorted(
        path
        for path in root.rglob("*.json")
        if path.is_file() and not any(part in skipped for part in path.parts)
    )


def existing_relative_paths(root: Path) -> set[str]:
    skipped = {".git", "__pycache__", ".pytest_cache"}
    return {
        rel(path, root)
        for path in root.rglob("*")
        if path.is_file() and not any(part in skipped for part in path.parts)
    }


def collect_known_ids(root: Path) -> dict[str, set[str]]:
    ids: dict[str, set[str]] = {
        "segment": set(),
        "transition": set(),
        "boundary": set(),
        "revision": set(),
        "candidate": set(),
        "node": set(),
        "callback": set(),
    }
    for segment in (read_json(root / "scene_segments.json").get("segments") or []):
        if segment.get("segment_id"):
            ids["segment"].add(str(segment["segment_id"]))
    for row in (read_json(root / "consensus" / "transition_confidence.json").get("transitions") or []):
        if row.get("transition_id"):
            ids["transition"].add(str(row["transition_id"]))
    for row in (read_json(root / "discourse" / "discourse_state.json").get("discourse_transitions") or []):
        if row.get("transition_id"):
            ids["transition"].add(str(row["transition_id"]))
    for row in (read_json(root / "continuity" / "boundary_diagnostics.json").get("boundaries") or []):
        if row.get("boundary_id"):
            ids["boundary"].add(str(row["boundary_id"]))
    revision_graph = read_json(root / "revision_graph" / "revision_graph.json")
    for state in revision_graph.get("revision_states") or []:
        if state.get("revision_id"):
            ids["revision"].add(str(state["revision_id"]))
    for row in revision_graph.get("revision_candidates") or []:
        if row.get("candidate_id"):
            ids["candidate"].add(str(row["candidate_id"]))
        if row.get("simulated_revision_id"):
            ids["revision"].add(str(row["simulated_revision_id"]))
    argument = read_json(root / "discourse" / "argument_graph.json")
    for node in argument.get("nodes") or []:
        if node.get("node_id"):
            ids["node"].add(str(node["node_id"]))
    for row in (read_json(root / "discourse" / "callback_resolution.json").get("callback_pairs") or []):
        if row.get("callback_id"):
            ids["callback"].add(str(row["callback_id"]))
    return ids


def _id_type(key: str) -> str | None:
    key = key or ""
    if "segment_id" in key:
        return "segment"
    if "transition_id" in key:
        return "transition"
    if "boundary_id" in key:
        return "boundary"
    if "revision_id" in key:
        return "revision"
    if "candidate_id" in key:
        return "candidate"
    if "node_id" in key:
        return "node"
    if "callback_id" in key:
        return "callback"
    return None


def _typed_id(key: str, value: str) -> str | None:
    if value.startswith("SEG_"):
        return "segment"
    if value.startswith("TR_") or value.startswith("DTR_"):
        return "transition"
    if value.startswith("REV_"):
        return "revision"
    if value.startswith("CAND_"):
        return "candidate"
    if value.startswith("ARG_") or value.startswith("N_"):
        return "node"
    return _id_type(key)


def _looks_like_path(value: str) -> bool:
    return bool(re.search(r"\.(json|md|html|png|jpg|jpeg|css|js|srt|csv)$", value, re.I)) or "/" in value or "\\" in value


def _walk(value: Any, path: str = "$"):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            yield key, child, child_path
            yield from _walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")


def collect_reference_records(root: Path) -> list[dict]:
    records: list[dict] = []
    for path in json_files(root):
        data = read_json(path)
        source = rel(path, root)
        for key, value, json_path in _walk(data):
            if value is None:
                continue
            if key in ID_KEYS:
                values = value if isinstance(value, list) else [value]
                for item in values:
                    if isinstance(item, (str, int, float)):
                        records.append({"source": source, "path": json_path, "kind": _typed_id(key, str(item)), "key": key, "value": str(item)})
            if key in PATH_KEYS and isinstance(value, str) and _looks_like_path(value):
                if key == "schema" and "/" not in value and "\\" not in value:
                    continue
                if "*" in value:
                    continue
                records.append({"source": source, "path": json_path, "kind": "path", "key": key, "value": value.replace("\\", "/")})
    return records


def _is_internal_path(value: str) -> bool:
    if value.startswith(("http://", "https://", "mailto:", "#")):
        return False
    if re.match(r"^[A-Za-z]:/", value):
        return False
    return _looks_like_path(value)


def validate_references(output_dir: Path) -> dict:
    root = Path(output_dir)
    ids = collect_known_ids(root)
    existing = existing_relative_paths(root)
    records = collect_reference_records(root)
    invalid: list[dict] = []
    valid_count = 0
    for record in records:
        kind = record.get("kind")
        value = str(record.get("value") or "")
        if not value or value == "None":
            continue
        if kind == "path":
            candidate = value[3:] if value.startswith("../") else value
            candidate = candidate.split("#", 1)[0].split("?", 1)[0]
            if _is_internal_path(candidate) and candidate not in existing:
                invalid.append({**record, "reason": "Referenced relative path does not exist."})
            else:
                valid_count += 1
        elif kind in ids:
            if record.get("key") == "parent_revision_id" and value in {"", "None"}:
                valid_count += 1
            elif value in ids[kind]:
                valid_count += 1
            else:
                invalid.append({**record, "reason": f"Referenced {kind} ID is not known."})
    orphan_refs = [item for item in invalid if item.get("kind") != "path"]
    score = round(max(0.0, 1.0 - (len(invalid) / max(len(records), 1))), 3)
    report = {
        "validation_status": STATUS_COMPLETE if not invalid else STATUS_ERROR,
        "generated_at_utc": utc_now_iso(),
        "valid_reference_count": valid_count,
        "invalid_reference_count": len(invalid),
        "orphan_reference_count": len(orphan_refs),
        "unresolved_reference_paths": invalid[:200],
        "stale_reference_summary": {
            "missing_path_count": len([item for item in invalid if item.get("kind") == "path"]),
            "unknown_id_count": len(orphan_refs),
        },
        "reference_integrity_score": score,
        "known_id_counts": {key: len(value) for key, value in ids.items()},
        "limitations": [
            "Reference validation is deterministic and structural; it does not infer semantic equivalence.",
            "Only generated local artifacts and relative links are validated.",
        ],
    }
    integrity = root / "integrity"
    integrity.mkdir(exist_ok=True)
    write_json(integrity / "reference_validation.json", report)
    return report


def write_reference_report(output_dir: Path, report: dict) -> None:
    reports = Path(output_dir) / "reports"
    reports.mkdir(exist_ok=True)
    lines = [
        "# Reference Validation Report",
        "",
        f"- Score: `{report.get('reference_integrity_score')}`",
        f"- Valid references: `{report.get('valid_reference_count')}`",
        f"- Invalid references: `{report.get('invalid_reference_count')}`",
        f"- Orphan references: `{report.get('orphan_reference_count')}`",
        "",
        "## Unresolved References",
        "",
    ]
    for item in report.get("unresolved_reference_paths", [])[:50]:
        lines.append(f"- `{item.get('source')}` `{item.get('path')}` -> `{item.get('value')}` ({item.get('reason')})")
    if not report.get("unresolved_reference_paths"):
        lines.append("- No unresolved references detected.")
    (reports / "reference_validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
