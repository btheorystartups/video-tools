"""Deterministic argument-chain graph construction."""

from __future__ import annotations

import re
from collections import defaultdict
from statistics import mean

from report_generator import STOPWORDS, words
from rhetorical_coherence import CLAIM_RE, CONTRAST_RE, EXAMPLE_RE, QUESTION_RE, RESOLVE_RE, TAKEAWAY_RE
from stability import STATUS_COMPLETE, STATUS_LIMITED, deterministic_id


IMPLICATION_RE = re.compile(r"\b(which means|that means|therefore|so|as a result|implies)\b", re.I)
COUNTER_RE = re.compile(r"\b(but|however|although|on the other hand|counterpoint|except)\b", re.I)


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 3)


def _tokens(text: str) -> set[str]:
    return {token for token in words(text) if len(token) > 2 and token not in STOPWORDS}


def _node_roles(text: str) -> list[str]:
    roles = []
    if CLAIM_RE.search(text or ""):
        roles.append("claim")
    if EXAMPLE_RE.search(text or ""):
        roles.append("example")
    if IMPLICATION_RE.search(text or ""):
        roles.append("implication")
    if CONTRAST_RE.search(text or ""):
        roles.append("contrast")
    if COUNTER_RE.search(text or ""):
        roles.append("counterpoint")
    if TAKEAWAY_RE.search(text or ""):
        roles.append("takeaway")
    if QUESTION_RE.search(text or ""):
        roles.append("unresolved_claim")
    return roles or ["context"]


def _edge_type(left_roles: list[str], right_roles: list[str], shared: set[str]) -> str:
    if "contrast" in right_roles or "counterpoint" in right_roles:
        return "contrasts"
    if "takeaway" in right_roles and ({"claim", "unresolved_claim"} & set(left_roles)):
        return "resolves"
    if "example" in right_roles and "claim" in left_roles:
        return "supports"
    if shared and ("claim" in left_roles or "implication" in right_roles):
        return "expands"
    if shared:
        return "revisits"
    return "redirects"


def build_argument_graph(scene_segments: dict, rhetorical_coherence: dict | None = None, topic_continuity: dict | None = None) -> dict:
    segments = scene_segments.get("segments") or []
    if not segments:
        return {
            "analysis_status": STATUS_LIMITED,
            "method": "deterministic_argument_graph_v1",
            "nodes": [],
            "edges": [],
            "argument_chains": [],
            "unresolved_chains": [],
            "fragmented_chains": [],
            "recovered_chains": [],
            "contradiction_clusters": [],
            "argument_completeness_score": 0.0,
            "argument_fragmentation_score": 0.0,
            "limitations": ["No segments were available for argument graph construction."],
        }

    nodes = []
    by_segment = {}
    for index, segment in enumerate(segments):
        text = segment.get("text", "")
        roles = _node_roles(text)
        token_set = _tokens(text)
        node_id = deterministic_id("ARG", segment.get("segment_id"), ",".join(roles), index)
        row = {
            "node_id": node_id,
            "segment_id": segment.get("segment_id"),
            "start_sec": segment.get("start_sec"),
            "end_sec": segment.get("end_sec"),
            "node_type": roles[0],
            "roles": roles,
            "concept_terms": sorted(token_set)[:14],
            "summary": segment.get("summary") or text[:180],
            "support_state": "partial_support" if "claim" in roles and "example" not in roles else "supported" if "example" in roles or "takeaway" in roles else "context",
        }
        nodes.append(row)
        by_segment[row["segment_id"]] = row

    edges = []
    for left, right in zip(nodes, nodes[1:]):
        shared = set(left["concept_terms"]) & set(right["concept_terms"])
        edge_type = _edge_type(left["roles"], right["roles"], shared)
        strength = _clamp((len(shared) / 8.0) + (0.3 if edge_type in {"supports", "resolves", "contrasts"} else 0.1))
        edges.append(
            {
                "edge_id": deterministic_id("AED", left["node_id"], right["node_id"], edge_type),
                "from_node_id": left["node_id"],
                "to_node_id": right["node_id"],
                "from_segment_id": left["segment_id"],
                "to_segment_id": right["segment_id"],
                "edge_type": edge_type,
                "shared_terms": sorted(shared)[:12],
                "edge_strength": strength,
            }
        )

    bridge_rows = (topic_continuity or {}).get("topic_bridge_terms") or []
    for bridge in bridge_rows:
        left = by_segment.get(bridge.get("from_segment_id"))
        right = by_segment.get(bridge.get("to_segment_id"))
        if left and right and bridge.get("continuity_score", 1.0) < 0.34:
            edges.append(
                {
                    "edge_id": deterministic_id("AED", left["node_id"], right["node_id"], "redirect_topic"),
                    "from_node_id": left["node_id"],
                    "to_node_id": right["node_id"],
                    "from_segment_id": left["segment_id"],
                    "to_segment_id": right["segment_id"],
                    "edge_type": "redirects",
                    "shared_terms": bridge.get("bridge_terms", [])[:12],
                    "edge_strength": _clamp(1.0 - float(bridge.get("continuity_score") or 0.0)),
                }
            )

    adjacency: dict[str, list[dict]] = defaultdict(list)
    for edge in edges:
        adjacency[edge["from_node_id"]].append(edge)

    chains = []
    unresolved = []
    fragmented = []
    recovered = []
    contradiction_clusters = []
    for index, node in enumerate(nodes):
        if not ({"claim", "unresolved_claim", "contrast"} & set(node["roles"])):
            continue
        chain_edges = []
        chain_nodes = [node["node_id"]]
        status = "abandoned_argument"
        for edge in edges:
            if edge["from_node_id"] == chain_nodes[-1] and len(chain_nodes) < 5:
                chain_edges.append(edge["edge_id"])
                chain_nodes.append(edge["to_node_id"])
                target = next((item for item in nodes if item["node_id"] == edge["to_node_id"]), {})
                if edge["edge_type"] in {"supports", "resolves"} or "takeaway" in target.get("roles", []):
                    status = "complete"
                    break
                if edge["edge_type"] == "contrasts":
                    status = "partial_support"
        if status != "complete" and any("example" in item["roles"] for item in nodes[index + 1 : index + 3]):
            status = "partial_support"
        chain = {
            "chain_id": deterministic_id("ACH", node["node_id"], ",".join(chain_nodes)),
            "root_node_id": node["node_id"],
            "node_ids": chain_nodes,
            "edge_ids": chain_edges,
            "segment_ids": [item["segment_id"] for item in nodes if item["node_id"] in chain_nodes],
            "chain_status": status,
            "chain_strength": _clamp(mean([edge["edge_strength"] for edge in edges if edge["edge_id"] in chain_edges]) if chain_edges else 0.18),
        }
        chains.append(chain)
        if status == "complete" and len(chain_nodes) > 2:
            recovered.append(chain)
        elif status in {"abandoned_argument", "partial_support"}:
            unresolved.append(chain)
        if any(edge["edge_type"] == "redirects" for edge in edges if edge["edge_id"] in chain_edges):
            fragmented.append(chain)
        if "contrast" in node["roles"] or "counterpoint" in node["roles"]:
            contradiction_clusters.append(
                {
                    "cluster_id": deterministic_id("ACC", node["node_id"], index),
                    "node_ids": chain_nodes,
                    "segment_ids": chain["segment_ids"],
                    "cluster_type": "contrast_or_counterpoint",
                    "resolution_state": "resolved" if status == "complete" else "unresolved",
                }
            )

    completeness = _clamp(sum(1 for chain in chains if chain["chain_status"] == "complete") / max(len(chains), 1))
    fragmentation = _clamp((len(fragmented) + len(unresolved) * 0.65) / max(len(chains), 1))
    return {
        "analysis_status": STATUS_COMPLETE if any(segment.get("text") for segment in segments) else STATUS_LIMITED,
        "method": "deterministic_argument_graph_v1",
        "nodes": nodes,
        "edges": sorted(edges, key=lambda row: (row["from_segment_id"] or "", row["to_segment_id"] or "", row["edge_id"])),
        "argument_chains": chains,
        "unresolved_chains": unresolved,
        "fragmented_chains": fragmented,
        "recovered_chains": recovered,
        "contradiction_clusters": contradiction_clusters,
        "argument_completeness_score": completeness,
        "argument_fragmentation_score": fragmentation,
        "source_rhetorical_gaps": (rhetorical_coherence or {}).get("rhetorical_gap_explanations", [])[:30],
        "limitations": [
            "Argument chains are deterministic marker and adjacency heuristics for editorial review.",
            "They are not proof of factual correctness or semantic entailment.",
        ],
    }
