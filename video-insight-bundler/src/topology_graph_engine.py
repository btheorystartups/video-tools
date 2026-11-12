"""Formal topology graph engine for portable review exports."""

from __future__ import annotations

import math
from collections import Counter, defaultdict, deque
from pathlib import Path

from asset_dependency_scanner import classify_file, extract_references, is_text_file, resolve_reference
from stability import deterministic_id, utc_now_iso, write_json


ENTITY_TOKEN_TYPES = [
    ("governance", "governance"),
    ("recommendation", "recommendation"),
    ("evidence", "evidence"),
    ("timeline", "timeline"),
    ("continuity", "timeline"),
    ("snapshot", "snapshot"),
    ("diff", "diff"),
    ("delta", "diff"),
    ("replay", "lineage"),
    ("lineage", "lineage"),
    ("review", "review_workflow"),
    ("pathway", "pathway"),
    ("provenance", "provenance"),
]


def build_topology_graph(package_root: Path, governance: dict | None = None) -> dict:
    root = package_root.resolve()
    nodes = []
    node_paths = set()
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix().lower()):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        entity_type = _entity_type(rel, classify_file(root, path))
        node_paths.add(rel)
        nodes.append(
            {
                "node_id": deterministic_id("TOPO", rel),
                "path": rel,
                "entity_type": entity_type,
                "artifact_type": classify_file(root, path),
                "size_bytes": path.stat().st_size,
                "cluster_key": _cluster_key(rel, entity_type),
            }
        )
    edges = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix().lower()):
        if not path.is_file() or not is_text_file(path):
            continue
        source = path.relative_to(root).as_posix()
        for ref in extract_references(path):
            if ref.get("kind") == "absolute_path":
                continue
            resolved = resolve_reference(path, root, str(ref.get("value") or ""))
            if not resolved or not resolved.exists() or not resolved.is_file():
                continue
            target = resolved.relative_to(root).as_posix()
            if source != target and target in node_paths:
                edges.append({"source": source, "target": target, "edge_type": ref.get("kind") or "reference"})
    graph = _adjacency(edges)
    reverse = _reverse(graph)
    cycles = detect_cycles(graph)
    sccs = strongly_connected_components(graph)
    clusters = _clusters(nodes, graph)
    duplicate_pathways = _duplicate_pathways(graph)
    entry = _entrypoint(root)
    shortest_paths = _shortest_review_paths(graph, entry, nodes)
    depths = _dependency_depths(graph)
    entity_counts = Counter(node["entity_type"] for node in nodes)
    reachable = set(shortest_paths)
    orphan_nodes = sorted(node["path"] for node in nodes if node["path"] not in reachable and node["path"] != entry)
    density = round(len(edges) / max(len(nodes) * max(len(nodes) - 1, 1), 1), 6)
    entropy = _navigation_entropy(nodes, graph)
    registry = {
        "analysis_status": "complete",
        "method": "topology_graph_engine_v64",
        "generated_at_utc": utc_now_iso(),
        "nodes": nodes,
        "edges": edges,
        "entity_types": dict(sorted(entity_counts.items())),
        "metrics": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "cycle_count": len(cycles),
            "orphan_count": len(orphan_nodes),
            "strongly_connected_component_count": len(sccs),
            "topology_density": density,
            "navigation_entropy": entropy,
            "max_dependency_depth": max(depths.values() or [0]),
            "duplicate_pathway_count": len(duplicate_pathways),
        },
        "orphan_nodes": orphan_nodes,
        "dependency_depths": depths,
    }
    cycle_registry = {
        "analysis_status": "complete",
        "method": "topology_cycle_registry_v64",
        "generated_at_utc": utc_now_iso(),
        "cycles": cycles,
        "strongly_connected_components": sccs,
        "summary": {"cycle_count": len(cycles), "strongly_connected_component_count": len(sccs)},
    }
    cluster_registry = {
        "analysis_status": "complete",
        "method": "topology_cluster_registry_v64",
        "generated_at_utc": utc_now_iso(),
        "clusters": clusters,
        "duplicate_pathways": duplicate_pathways,
        "summary": {"cluster_count": len(clusters), "duplicate_pathway_count": len(duplicate_pathways)},
    }
    review_optimization = {
        "analysis_status": "complete",
        "method": "review_path_optimization_v64",
        "generated_at_utc": utc_now_iso(),
        "entrypoint": entry,
        "shortest_review_paths": shortest_paths,
        "recommended_next_dashboard": _recommended_next(shortest_paths, nodes),
        "index_hierarchy_suggestions": _hierarchy_suggestions(clusters),
        "cycle_reduction_candidates": cycles[:25],
        "orphan_reduction_candidates": orphan_nodes[:100],
        "summary": {
            "optimized_path_count": len(shortest_paths),
            "cycle_reduction_candidate_count": len(cycles),
            "orphan_reduction_candidate_count": len(orphan_nodes),
        },
    }
    for name, payload in [
        ("topology_graph_registry.json", registry),
        ("topology_cycle_registry.json", cycle_registry),
        ("topology_cluster_registry.json", cluster_registry),
        ("review_path_optimization.json", review_optimization),
    ]:
        write_json(root / name, payload)
        write_json(root / "governance" / name, payload)
    return {
        "topology_graph_registry": registry,
        "topology_cycle_registry": cycle_registry,
        "topology_cluster_registry": cluster_registry,
        "review_path_optimization": review_optimization,
    }


def detect_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
    cycles = []
    visited = set()
    stack = []
    in_stack = set()

    def visit(node: str) -> None:
        if node in in_stack:
            idx = stack.index(node)
            cycles.append(stack[idx:] + [node])
            return
        if node in visited:
            return
        visited.add(node)
        in_stack.add(node)
        stack.append(node)
        for target in graph.get(node, []):
            visit(target)
        stack.pop()
        in_stack.remove(node)

    for node in graph:
        visit(node)
    seen = set()
    unique = []
    for cycle in cycles:
        key = tuple(sorted(cycle))
        if key not in seen:
            seen.add(key)
            unique.append(cycle)
    return unique


def strongly_connected_components(graph: dict[str, list[str]]) -> list[dict]:
    index = 0
    stack = []
    indexes = {}
    lowlinks = {}
    on_stack = set()
    components = []

    def visit(node: str) -> None:
        nonlocal index
        indexes[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for target in graph.get(node, []):
            if target not in indexes:
                visit(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in on_stack:
                lowlinks[node] = min(lowlinks[node], indexes[target])
        if lowlinks[node] == indexes[node]:
            component = []
            while True:
                item = stack.pop()
                on_stack.remove(item)
                component.append(item)
                if item == node:
                    break
            if len(component) > 1:
                components.append({"component_id": deterministic_id("SCC", sorted(component)), "nodes": sorted(component), "size": len(component)})

    for node in graph:
        if node not in indexes:
            visit(node)
    return components


def shortest_path(graph: dict[str, list[str]], start: str, target: str) -> list[str]:
    queue = deque([(start, [start])])
    seen = {start}
    while queue:
        node, path = queue.popleft()
        if node == target:
            return path
        for nxt in graph.get(node, []):
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, path + [nxt]))
    return []


def _entity_type(rel: str, artifact_type: str) -> str:
    lower = rel.lower()
    if artifact_type == "dashboard" or rel.endswith((".html", ".htm")):
        return "dashboard"
    if artifact_type in {"graph", "image", "board", "web_asset"}:
        return "asset"
    for token, entity in ENTITY_TOKEN_TYPES:
        if token in lower:
            return entity
    return artifact_type or "artifact"


def _cluster_key(rel: str, entity_type: str) -> str:
    parts = Path(rel).parts
    if parts:
        return f"{entity_type}:{parts[0]}"
    return entity_type


def _adjacency(edges: list[dict]) -> dict[str, list[str]]:
    graph: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        graph[edge["source"]].add(edge["target"])
        graph.setdefault(edge["target"], set())
    return {key: sorted(value) for key, value in graph.items()}


def _reverse(graph: dict[str, list[str]]) -> dict[str, list[str]]:
    rev: dict[str, set[str]] = defaultdict(set)
    for source, targets in graph.items():
        rev.setdefault(source, set())
        for target in targets:
            rev[target].add(source)
    return {key: sorted(value) for key, value in rev.items()}


def _clusters(nodes: list[dict], graph: dict[str, list[str]]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for node in nodes:
        grouped[node["cluster_key"]].append(node)
    clusters = []
    for key, items in sorted(grouped.items()):
        paths = [item["path"] for item in items]
        outbound = sum(len([target for target in graph.get(path, []) if target not in paths]) for path in paths)
        clusters.append(
            {
                "cluster_id": deterministic_id("CLUSTER", key),
                "cluster_key": key,
                "entity_type": key.split(":", 1)[0],
                "node_count": len(items),
                "representative_paths": paths[:20],
                "outbound_edge_count": outbound,
            }
        )
    return clusters


def _duplicate_pathways(graph: dict[str, list[str]]) -> list[dict]:
    signatures: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for source, targets in graph.items():
        html_targets = tuple(sorted(target for target in targets if target.endswith((".html", ".htm"))))
        if len(html_targets) >= 2:
            signatures[html_targets].append(source)
    return [
        {"duplicate_pathway_id": deterministic_id("DUPPATH", signature), "sources": sorted(sources), "shared_targets": list(signature)}
        for signature, sources in signatures.items()
        if len(sources) > 1
    ]


def _entrypoint(root: Path) -> str:
    for rel in ["index.html", "visualizations/corpus_dashboard.html", "visualizations/dashboard.html"]:
        if (root / rel).exists():
            return rel
    return "index.html"


def _shortest_review_paths(graph: dict[str, list[str]], entry: str, nodes: list[dict]) -> dict[str, list[str]]:
    targets = [
        node["path"]
        for node in nodes
        if node["entity_type"] in {"dashboard", "governance", "recommendation", "evidence", "timeline", "review_workflow"}
        and node["path"] != entry
    ]
    paths = {}
    for target in targets[:250]:
        path = shortest_path(graph, entry, target)
        if path:
            paths[target] = path
    return paths


def _dependency_depths(graph: dict[str, list[str]]) -> dict[str, int]:
    depths = {}
    for node in graph:
        seen = {node}
        queue = deque([(node, 0)])
        max_depth = 0
        while queue:
            current, depth = queue.popleft()
            max_depth = max(max_depth, depth)
            for target in graph.get(current, []):
                if target not in seen:
                    seen.add(target)
                    queue.append((target, depth + 1))
        depths[node] = max_depth
    return depths


def _navigation_entropy(nodes: list[dict], graph: dict[str, list[str]]) -> float:
    counts = Counter(node["entity_type"] for node in nodes if graph.get(node["path"]))
    total = sum(counts.values())
    if not total:
        return 0.0
    return round(-sum((count / total) * math.log2(count / total) for count in counts.values()), 4)


def _recommended_next(paths: dict[str, list[str]], nodes: list[dict]) -> str | None:
    by_path = {node["path"]: node for node in nodes}
    candidates = sorted(paths, key=lambda path: (len(paths[path]), by_path.get(path, {}).get("size_bytes", 0)))
    return candidates[0] if candidates else None


def _hierarchy_suggestions(clusters: list[dict]) -> list[dict]:
    return [
        {
            "cluster_key": cluster["cluster_key"],
            "suggested_navigation_action": "promote_as_section" if cluster["node_count"] >= 5 else "keep_inline",
            "node_count": cluster["node_count"],
        }
        for cluster in sorted(clusters, key=lambda row: row["node_count"], reverse=True)[:20]
    ]
