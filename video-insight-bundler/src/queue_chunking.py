"""Deterministic queue chunking for dense review workloads."""

from __future__ import annotations

from collections import defaultdict

from operator_workflow_common import ergonomics_links, phase40_artifact, render_registry_page, risk_level, stable_row_id


def build_queue_chunking_registry(outputs: dict, chunk_size: int = 25) -> dict:
    items = _collect_queue_items(outputs)
    buckets: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for item in items:
        severity = _severity(item)
        theme = _theme(item)
        buckets[(severity, theme)].append(item)
    chunks = []
    for (severity, theme), rows in sorted(buckets.items()):
        rows = sorted(rows, key=lambda row: (row.get("source_queue"), row.get("queue_item_id") or row.get("item_id") or ""))
        for index in range(0, len(rows), max(1, chunk_size)):
            subset = rows[index : index + max(1, chunk_size)]
            chunks.append({
                "queue_chunk_id": stable_row_id("QCHUNK", severity, theme, index, [row.get("queue_item_id") or row.get("item_id") for row in subset]),
                "chunk_index": len(chunks) + 1,
                "chunk_strategy": "severity_similarity_workload",
                "governance_severity": severity,
                "ambiguity_density": _density(subset, "ambiguity"),
                "escalation_relevance": _density(subset, "escalation"),
                "recommendation_similarity": theme,
                "operational_workload": len(subset),
                "pressure_level": risk_level(min(1.0, len(subset) / max(1, chunk_size))),
                "item_refs": [row.get("queue_item_id") or row.get("item_id") for row in subset],
                "hidden_runtime_state_used": False,
            })
    artifact = phase40_artifact("deterministic_queue_chunking_v1")
    artifact.update({"queue_chunking_registry_id": stable_row_id("QCHUNKREG", [row["queue_chunk_id"] for row in chunks]), "queue_chunks": chunks, "summary": {"chunk_count": len(chunks), "source_queue_item_count": len(items), "chunk_size": chunk_size}})
    return artifact


def render_queue_chunking_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("queue_chunking_registry") or {}).get("queue_chunks") or []
    return {"queue_chunking_dashboard.html": render_registry_page("Queue Chunking Dashboard", "Session Ergonomics", "queue_chunking_dashboard.html", rows, ["chunk_index", "governance_severity", "ambiguity_density", "escalation_relevance", "operational_workload", "pressure_level"], "queue_chunk_id", [("Chunks", len(rows))], ergonomics_links(""))}


def _collect_queue_items(outputs: dict) -> list[dict]:
    rows = []
    for key in ["review_queue_registry", "adjudication_queue_registry", "unresolved_conflict_queue", "reconciliation_required_queue", "governance_adjudication_queue", "high_priority_review_queue", "escalation_required_queue", "imported_review_followup_queue"]:
        for item in (outputs.get(key) or {}).get("queue_items") or []:
            rows.append({**item, "source_queue": key})
    return rows


def _severity(item: dict) -> str:
    text = " ".join(str(item.get(key, "")) for key in ["severity", "priority", "governance_severity", "queue_type", "source_queue"]).lower()
    if "critical" in text or "blocker" in text:
        return "critical"
    if "high" in text or "escalation" in text or "governance" in text:
        return "high"
    if "medium" in text or "conflict" in text:
        return "medium"
    return "review"


def _theme(item: dict) -> str:
    text = " ".join(str(item.get(key, "")) for key in ["recommendation_id", "category", "queue_type", "reason", "source_queue"]).lower()
    for token in ["governance", "ambiguity", "reconciliation", "pacing", "rhetorical", "followup"]:
        if token in text:
            return token
    return "general_review"


def _density(rows: list[dict], token: str) -> float:
    if not rows:
        return 0.0
    hits = sum(1 for row in rows if token in str(row).lower())
    return round(hits / len(rows), 3)
