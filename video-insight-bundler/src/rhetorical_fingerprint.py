"""Recurring rhetorical signature analysis."""

from __future__ import annotations

from collections import Counter

from intelligence_common import avg, base_artifact, deterministic_id, sorted_segments


def build_rhetorical_fingerprint(analyses: list[dict]) -> dict:
    rows = []
    global_counts: Counter = Counter()
    for analysis in analyses:
        segments = sorted_segments(analysis.get("scene_segments") or {})
        counts: Counter = Counter()
        for segment in segments:
            counts.update(segment.get("topic_markers") or [])
        global_counts.update(counts)
        rows.append(
            {
                "rhetorical_fingerprint_id": deterministic_id("RHETFP", analysis.get("analysis_dir"), sorted(counts.items())),
                "analysis_dir": analysis.get("analysis_dir"),
                "marker_counts": dict(sorted(counts.items())),
                "rhetorical_density": avg([len(row.get("topic_markers") or []) / 4.0 for row in segments]),
                "dominant_rhetorical_signature": counts.most_common(1)[0][0] if counts else "limited",
            }
        )
    output = base_artifact(method="deterministic_rhetorical_fingerprint_v1")
    output.update(
        {
            "rhetorical_fingerprints": rows,
            "recurring_rhetorical_signatures": [{"marker": key, "count": value} for key, value in global_counts.most_common()],
            "summary": {"analysis_count": len(rows), "signature_count": len(global_counts)},
        }
    )
    return output
