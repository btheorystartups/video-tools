"""Estimate deterministic rebuild cost from dependency and artifact indexes."""

from __future__ import annotations

from operator_workflow_common import deterministic_cost, phase39_artifact, stable_row_id


def build_rebuild_cost_registry(outputs: dict) -> dict:
    dependencies = (outputs.get("generation_dependency_registry") or {}).get("dependencies") or []
    artifacts = (outputs.get("artifact_operational_index") or {}).get("artifacts") or []
    dep_counts = {row.get("artifact"): len(row.get("dependencies") or []) for row in dependencies}
    rows = []
    for artifact in artifacts:
        name = artifact.get("artifact")
        depth = _depth(name, {row.get("artifact"): row.get("dependencies") or [] for row in dependencies})
        impacted_dashboards = artifact.get("linked_dashboards") or []
        rows.append({
            "rebuild_cost_id": stable_row_id("RBCOST", name, depth, impacted_dashboards),
            "artifact": name,
            "estimated_regeneration_count": 1 + dep_counts.get(name, 0),
            "estimated_validation_count": 1 if artifact.get("linked_schemas") else 0,
            "dependency_chain_depth": depth,
            "impacted_dashboards": impacted_dashboards,
            "impacted_queues": _impacted_queues(name),
            "estimated_cost_units": deterministic_cost(dep_counts.get(name, 0), depth, len(impacted_dashboards), base=1.0, scale=0.25),
            "hidden_mutable_runtime_state": False,
        })
    artifact = phase39_artifact("deterministic_rebuild_cost_estimator_v1")
    artifact.update({"rebuild_cost_registry_id": stable_row_id("RBCOSTREG", [row["rebuild_cost_id"] for row in rows]), "rebuild_costs": rows, "summary": {"rebuild_cost_count": len(rows), "max_dependency_chain_depth": max([row["dependency_chain_depth"] for row in rows] or [0]), "estimated_total_cost_units": round(sum(row["estimated_cost_units"] for row in rows), 3)}})
    return artifact


def _depth(name: str | None, deps: dict, seen: set[str] | None = None) -> int:
    if not name or name not in deps:
        return 0
    seen = seen or set()
    if name in seen:
        return 0
    seen.add(name)
    children = deps.get(name) or []
    return 1 + max((_depth(child, deps, set(seen)) for child in children), default=0)


def _impacted_queues(name: str | None) -> list[str]:
    text = str(name or "")
    if "adjudication" in text:
        return ["queues/governance_adjudication_queue.json", "queues/reviewer_disagreement_queue.json"]
    if "reconciliation" in text or "import" in text:
        return ["queues/reconciliation_required_queue.json", "queues/unresolved_conflict_queue.json"]
    return []
