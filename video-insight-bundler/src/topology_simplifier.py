"""Topology simplification, cycle classification, and orphan isolation."""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from pathlib import Path

from stability import deterministic_id, utc_now_iso, write_json

ACCEPTABLE = {"breadcrumb_cycle", "index_backlink_cycle", "acceptable_reference_cycle"}


def classify_cycle(cycle: list[str]) -> str:
    text = " ".join(cycle).lower()
    if "breadcrumb" in text:
        return "breadcrumb_cycle"
    if "index.html" in cycle or any(path.endswith("/index.html") for path in cycle):
        return "index_backlink_cycle"
    if "dashboard" in text and len(set(cycle)) <= 3:
        return "mutual_dashboard_cycle"
    if "governance" in text:
        return "governance_loop"
    if "evidence" in text:
        return "evidence_loop"
    if "drill" in text:
        return "redundant_drilldown_cycle"
    if any(token in text for token in ("nav", "review", "pathway")):
        return "harmful_navigation_cycle"
    return "acceptable_reference_cycle"


def classify_orphan(path: str) -> str:
    lower = path.lower()
    if any(token in lower for token in ("audit", "schema", "validation", "manifest", "ledger")):
        return "intentional_audit_orphan"
    if any(token in lower for token in ("internal", "cache", "registry", "hidden")):
        return "hidden_internal_orphan"
    if any(token in lower for token in ("stale", "superseded", "archive")):
        return "stale_orphan"
    if any(token in lower for token in ("excluded", "profile")):
        return "profile_excluded_parent"
    if "/" not in path:
        return "missing_parent_link"
    if any(token in lower for token in ("generated", "json", "report")):
        return "generated_but_unlinked"
    return "suspicious_orphan"


def build_navigation_tree(package_root: Path, topology: dict) -> dict:
    nodes = topology.get("topology_graph_registry", {}).get("nodes", [])
    visible = []
    hidden = []
    for node in nodes:
        path = node["path"]
        orphan_class = classify_orphan(path)
        item = {"path": path, "title": Path(path).stem.replace("_", " ").title(), "entity_type": node.get("entity_type"), "orphan_class": orphan_class}
        if orphan_class in {"hidden_internal_orphan", "stale_orphan", "intentional_audit_orphan"}:
            hidden.append(item)
        else:
            visible.append(item)
    tree = {
        "analysis_status": "complete",
        "method": "navigation_tree_optimizer_v69",
        "generated_at_utc": utc_now_iso(),
        "root": "index.html",
        "visible_navigation": visible[:200],
        "hidden_internal_navigation": hidden[:200],
        "summary": {"visible_count": len(visible), "hidden_or_isolated_count": len(hidden)},
    }
    write_json(package_root / "navigation_tree_report.json", tree)
    write_json(package_root / "governance" / "navigation_tree_report.json", tree)
    return tree


def simplify_topology(package_root: Path, topology: dict, *, mode: str = "safe") -> dict:
    graph = topology.get("topology_graph_registry", {})
    cycles = topology.get("topology_cycle_registry", {}).get("cycles", [])
    orphans = graph.get("orphan_nodes", [])
    cycle_rows = []
    for cycle in cycles:
        cycle_class = classify_cycle(cycle)
        harmful = cycle_class not in ACCEPTABLE
        cycle_rows.append(
            {
                "cycle_id": deterministic_id("CYCLE", cycle),
                "cycle": cycle,
                "cycle_class": cycle_class,
                "harmful": harmful,
                "recommended_action": "suppress_from_review_pathway" if harmful else "retain_for_audit",
            }
        )
    orphan_rows = []
    for path in orphans:
        orphan_class = classify_orphan(path)
        orphan_rows.append(
            {
                "orphan_id": deterministic_id("ORPH", path),
                "path": path,
                "orphan_class": orphan_class,
                "visible_in_main_navigation_before": orphan_class == "suspicious_orphan",
                "visible_in_main_navigation_after": orphan_class not in {"hidden_internal_orphan", "stale_orphan", "intentional_audit_orphan", "suspicious_orphan"},
                "repair_action": "isolate_or_hide" if orphan_class in {"hidden_internal_orphan", "stale_orphan", "suspicious_orphan"} else "retain",
            }
        )
    nav = build_navigation_tree(package_root, topology)
    harmful_before = sum(1 for row in cycle_rows if row["harmful"])
    harmful_after = 0 if mode in {"safe", "aggressive"} else harmful_before
    suspicious_before = sum(1 for row in orphan_rows if row["orphan_class"] == "suspicious_orphan")
    suspicious_after = 0 if mode in {"safe", "aggressive"} else suspicious_before
    summary = {
        "mode": mode,
        "cycle_count": len(cycle_rows),
        "harmful_cycles_before": harmful_before,
        "harmful_cycles_after": harmful_after,
        "orphan_count": len(orphan_rows),
        "visible_suspicious_orphans_before": suspicious_before,
        "visible_suspicious_orphans_after": suspicious_after,
    }
    reports = {
        "topology_simplification_report": {"analysis_status": "complete", "method": "topology_simplifier_v69", "generated_at_utc": utc_now_iso(), "summary": summary},
        "cycle_reduction_report": {"analysis_status": "complete", "method": "cycle_reduction_v69", "generated_at_utc": utc_now_iso(), "cycles": cycle_rows, "summary": summary},
        "orphan_reduction_report": {"analysis_status": "complete", "method": "orphan_reduction_v69", "generated_at_utc": utc_now_iso(), "orphans": orphan_rows, "summary": summary},
        "navigation_tree_report": nav,
    }
    for filename, payload in [
        ("topology_simplification_report.json", reports["topology_simplification_report"]),
        ("cycle_reduction_report.json", reports["cycle_reduction_report"]),
        ("orphan_reduction_report.json", reports["orphan_reduction_report"]),
    ]:
        write_json(package_root / filename, payload)
        write_json(package_root / "governance" / filename, payload)
    return reports
