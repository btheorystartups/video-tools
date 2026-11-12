"""Graph consistency validation across deterministic analysis artifacts."""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from pathlib import Path

from reference_validation import collect_known_ids, read_json
from stability import STATUS_COMPLETE, STATUS_ERROR, utc_now_iso, write_json


def _duplicates(values: list[str]) -> list[str]:
    return sorted(value for value, count in Counter(values).items() if value and count > 1)


def _cycle_summary(nodes: set[str], edges: list[tuple[str, str]]) -> dict:
    outgoing: dict[str, list[str]] = defaultdict(list)
    indegree = {node: 0 for node in nodes}
    for left, right in edges:
        if left in nodes and right in nodes:
            outgoing[left].append(right)
            indegree[right] = indegree.get(right, 0) + 1
            indegree.setdefault(left, 0)
    queue = deque([node for node, degree in indegree.items() if degree == 0])
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for child in outgoing.get(node, []):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    has_cycle = visited < len(indegree)
    return {"cycle_detected": has_cycle, "checked_node_count": len(indegree), "acyclic_node_count": visited}


def _fragmentation(nodes: set[str], edges: list[tuple[str, str]]) -> dict:
    if not nodes:
        return {"component_count": 0, "fragmented": False, "isolated_node_count": 0}
    graph: dict[str, set[str]] = {node: set() for node in nodes}
    for left, right in edges:
        if left in nodes and right in nodes:
            graph[left].add(right)
            graph[right].add(left)
    seen: set[str] = set()
    components = 0
    isolated = 0
    for node in nodes:
        if node in seen:
            continue
        components += 1
        stack = [node]
        size = 0
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            size += 1
            stack.extend(graph[current] - seen)
        if size == 1 and not graph[node]:
            isolated += 1
    return {"component_count": components, "fragmented": components > 1 and len(nodes) > 1, "isolated_node_count": isolated}


def _revision_graph(root: Path) -> dict:
    graph = read_json(root / "revision_graph" / "revision_graph.json")
    states = graph.get("revision_states") or []
    nodes = [row.get("revision_id") for row in states if row.get("revision_id")]
    edges = []
    invalid = []
    known = set(nodes)
    for state in states:
        parent = state.get("parent_revision_id")
        child = state.get("revision_id")
        if parent:
            edges.append((str(parent), str(child)))
            if parent not in known:
                invalid.append({"graph": "revision_graph", "from": parent, "to": child, "reason": "Unknown parent revision."})
    return {"nodes": set(nodes), "node_list": nodes, "edges": edges, "invalid_edges": invalid, "cycles_forbidden": True}


def _argument_graph(root: Path) -> dict:
    graph = read_json(root / "discourse" / "argument_graph.json")
    nodes = [row.get("node_id") for row in graph.get("nodes") or [] if row.get("node_id")]
    known = set(nodes)
    edges = []
    invalid = []
    for edge in graph.get("edges") or []:
        left = edge.get("from_node_id")
        right = edge.get("to_node_id")
        if left and right:
            edges.append((str(left), str(right)))
            if left not in known or right not in known:
                invalid.append({"graph": "argument_graph", "from": left, "to": right, "reason": "Unknown argument node."})
    return {"nodes": set(nodes), "node_list": nodes, "edges": edges, "invalid_edges": invalid, "cycles_forbidden": False}


def _segment_edge_graph(root: Path, artifact: str, row_key: str, left_key: str, right_key: str, name: str) -> dict:
    data = read_json(root / artifact)
    segment_ids = collect_known_ids(root).get("segment", set())
    edges = []
    invalid = []
    nodes = set(segment_ids)
    for row in data.get(row_key) or []:
        left = row.get(left_key)
        right = row.get(right_key)
        if left and right:
            edges.append((str(left), str(right)))
            if left not in segment_ids or right not in segment_ids:
                invalid.append({"graph": name, "from": left, "to": right, "reason": "Unknown segment reference."})
    return {"nodes": nodes, "node_list": list(nodes), "edges": edges, "invalid_edges": invalid, "cycles_forbidden": True}


def validate_graph_consistency(output_dir: Path) -> dict:
    root = Path(output_dir)
    graph_specs = {
        "revision_graph": _revision_graph(root),
        "argument_graph": _argument_graph(root),
        "topic_continuity": _segment_edge_graph(root, "continuity/topic_continuity.json", "topic_bridge_terms", "from_segment_id", "to_segment_id", "topic_continuity"),
        "boundary_diagnostics": _segment_edge_graph(root, "continuity/boundary_diagnostics.json", "boundaries", "from_segment_id", "to_segment_id", "boundary_diagnostics"),
        "callback_graph": _segment_edge_graph(root, "discourse/callback_resolution.json", "callback_pairs", "setup_segment_id", "payoff_segment_id", "callback_graph"),
        "visual_alignment": _segment_edge_graph(root, "visual_structure/visual_boundary_alignment.json", "alignment_rows", "from_segment_id", "to_segment_id", "visual_alignment"),
    }
    invalid_edges = []
    duplicate_nodes = []
    orphan_nodes = []
    cycle_summary = {}
    fragmentation_summary = {}
    counts = {}
    for name, spec in graph_specs.items():
        nodes = spec["nodes"]
        edges = spec["edges"]
        counts[name] = {"node_count": len(nodes), "edge_count": len(edges)}
        duplicate_nodes.extend({"graph": name, "node_id": value} for value in _duplicates(spec["node_list"]))
        invalid_edges.extend(spec["invalid_edges"])
        connected = {item for edge in edges for item in edge}
        orphan_nodes.extend({"graph": name, "node_id": node} for node in sorted(nodes - connected) if edges)
        cycle_summary[name] = _cycle_summary(nodes, edges) if spec.get("cycles_forbidden") else {"cycle_check": "allowed"}
        fragmentation_summary[name] = _fragmentation(nodes, edges)
    issue_count = len(invalid_edges) + len(duplicate_nodes) + sum(1 for item in cycle_summary.values() if item.get("cycle_detected"))
    score = round(max(0.0, 1.0 - (issue_count / max(sum(row["node_count"] + row["edge_count"] for row in counts.values()), 1))), 3)
    report = {
        "validation_status": STATUS_COMPLETE if issue_count == 0 else STATUS_ERROR,
        "generated_at_utc": utc_now_iso(),
        "graph_integrity_score": score,
        "graph_counts": counts,
        "orphan_nodes": orphan_nodes[:200],
        "duplicate_nodes": duplicate_nodes,
        "invalid_edges": invalid_edges,
        "cycle_summary": cycle_summary,
        "fragmentation_summary": fragmentation_summary,
        "cross_graph_consistency": {
            "segment_reference_authority": "scene_segments.json",
            "revision_reference_authority": "revision_graph/revision_graph.json",
            "argument_node_authority": "discourse/argument_graph.json",
        },
        "limitations": [
            "Cycles are forbidden for revision and timeline-order segment graphs, but allowed for argument-support structures.",
            "Graph validation checks identity and structural consistency, not semantic correctness.",
        ],
    }
    integrity = root / "integrity"
    integrity.mkdir(exist_ok=True)
    write_json(integrity / "graph_consistency.json", report)
    return report


def write_graph_consistency_report(output_dir: Path, report: dict) -> None:
    reports = Path(output_dir) / "reports"
    reports.mkdir(exist_ok=True)
    lines = [
        "# Graph Consistency Report",
        "",
        f"- Score: `{report.get('graph_integrity_score')}`",
        f"- Invalid edges: `{len(report.get('invalid_edges') or [])}`",
        f"- Duplicate nodes: `{len(report.get('duplicate_nodes') or [])}`",
        f"- Orphan nodes: `{len(report.get('orphan_nodes') or [])}`",
        "",
        "## Graph Counts",
        "",
    ]
    for name, counts in (report.get("graph_counts") or {}).items():
        lines.append(f"- `{name}`: `{counts.get('node_count')}` nodes, `{counts.get('edge_count')}` edges")
    lines.extend(["", "## Invalid Edges", ""])
    if report.get("invalid_edges"):
        for edge in report["invalid_edges"][:50]:
            lines.append(f"- `{edge.get('graph')}` `{edge.get('from')}` -> `{edge.get('to')}`: {edge.get('reason')}")
    else:
        lines.append("- No invalid graph edges detected.")
    (reports / "graph_consistency_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
