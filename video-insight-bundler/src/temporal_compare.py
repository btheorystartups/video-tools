"""Timeline-oriented compare workflows."""

from __future__ import annotations

from itertools import combinations

from intelligence_common import base_artifact, num
from stability import deterministic_id
from temporal_evidence_index import LIMITATION


def build_temporal_compare_registry(outputs: dict, temporal_index: dict) -> dict:
    by_video = {}
    for entry in temporal_index.get("temporal_evidence_entries") or []:
        by_video.setdefault(entry.get("source_video"), []).append(entry)
    rows = []
    for left, right in combinations(sorted(by_video)[:6], 2):
        left_high = sum(1 for row in by_video[left] if (row.get("highest_severity_signal") or {}).get("severity") == "high")
        right_high = sum(1 for row in by_video[right] if (row.get("highest_severity_signal") or {}).get("severity") == "high")
        workflow_id = deterministic_id("TCMP", left, right)
        rows.append({"temporal_compare_id": workflow_id, "workflow_type": "video_to_video", "left_video": left, "right_video": right, "detail_page": f"visualizations/timeline/temporal_compare_{workflow_id.lower()}.html", "metric_deltas": {"high_severity_region_delta": left_high - right_high}, "interpretation_delta": "Directional timeline difference for editorial review; not an objective quality ranking.", "optimization_implications": "Use differences to choose which timeline regions deserve review first.", "evidence_refs": ["timeline/temporal_evidence_index.json"], "non_claim_limitation": LIMITATION})
    for video, entries in sorted(by_video.items())[:6]:
        workflow_id = deterministic_id("TCMPV", video)
        mean_score = round(sum(num((entry.get("highest_severity_signal") or {}).get("score")) for entry in entries) / max(1, len(entries)), 3)
        rows.append({"temporal_compare_id": workflow_id, "workflow_type": "video_to_corpus_median", "left_video": video, "right_video": "local corpus median", "detail_page": f"visualizations/timeline/temporal_compare_{workflow_id.lower()}.html", "metric_deltas": {"mean_timeline_signal": mean_score}, "interpretation_delta": "Shows directional placement against local corpus temporal signals.", "optimization_implications": "Review regions above local norms before considering changes.", "evidence_refs": ["timeline/temporal_evidence_index.json"], "non_claim_limitation": LIMITATION})
    output = base_artifact(method="deterministic_temporal_compare_v1")
    output.update({"temporal_compare_registry_id": deterministic_id("TCMPREG", [row["temporal_compare_id"] for row in rows]), "temporal_compare_workflows": rows, "summary": {"temporal_compare_workflow_count": len(rows)}, "limitations": [LIMITATION]})
    return output

