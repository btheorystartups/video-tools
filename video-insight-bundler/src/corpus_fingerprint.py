"""Corpus-level editorial-structure fingerprint aggregation."""

from __future__ import annotations

from collections import Counter

from intelligence_common import avg, base_artifact, deterministic_id


def build_corpus_fingerprint(analyses: list[dict], comparative_outputs: dict | None = None) -> dict:
    comparative_outputs = comparative_outputs or {}
    style_rows = (comparative_outputs.get("style_fingerprint") or {}).get("style_fingerprints") or []
    rhetorical_rows = (comparative_outputs.get("rhetorical_fingerprint") or {}).get("rhetorical_fingerprints") or []
    pacing_rows = (comparative_outputs.get("pacing_fingerprint") or {}).get("pacing_fingerprints") or []
    discourse_rows = (comparative_outputs.get("discourse_fingerprint") or {}).get("discourse_fingerprints") or []
    rec_counts: Counter = Counter()
    temporal_values = []
    pressure_values = []
    visual_values = []
    for analysis in analyses:
        rec_counts.update(row.get("issue_type") for row in (analysis.get("recommendations") or {}).get("recommendations", []) if row.get("issue_type"))
        temporal_values.append(((analysis.get("temporal_rhythm") or {}).get("summary") or {}).get("mean_intensity_wave_score"))
        pressure_values.append(((analysis.get("editorial_pressure") or {}).get("summary") or {}).get("peak_cumulative_pressure_score"))
        visual_values.append((analysis.get("visual_structure") or {}).get("visual_continuity_score"))
    output = base_artifact(method="deterministic_corpus_fingerprint_v1")
    output.update(
        {
            "corpus_fingerprint_id": deterministic_id("CFP", [row.get("fingerprint_id") for row in style_rows], sorted(rec_counts.items())),
            "style_fingerprint_summary": (comparative_outputs.get("style_fingerprint") or {}).get("summary", {}),
            "rhetorical_fingerprint_summary": (comparative_outputs.get("rhetorical_fingerprint") or {}).get("summary", {}),
            "pacing_fingerprint_summary": (comparative_outputs.get("pacing_fingerprint") or {}).get("summary", {}),
            "discourse_fingerprint_summary": (comparative_outputs.get("discourse_fingerprint") or {}).get("summary", {}),
            "visual_continuity_fingerprint": avg(visual_values),
            "temporal_rhythm_fingerprint": avg(temporal_values),
            "pressure_fingerprint": avg(pressure_values),
            "recommendation_fingerprint": [{"issue_type": key, "count": value} for key, value in rec_counts.most_common()],
            "summary": {
                "analysis_count": len(analyses),
                "style_fingerprint_count": len(style_rows),
                "rhetorical_fingerprint_count": len(rhetorical_rows),
                "pacing_fingerprint_count": len(pacing_rows),
                "discourse_fingerprint_count": len(discourse_rows),
                "recommendation_family_count": len(rec_counts),
            },
        }
    )
    return output
