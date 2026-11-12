"""Persona and communication style classification heuristics."""

from __future__ import annotations

import json
from pathlib import Path


def load_taxonomy(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _all_text(segments: dict, transcript: dict) -> str:
    if transcript.get("text"):
        return transcript["text"]
    return " ".join(segment.get("text", "") for segment in segments.get("segments", []))


def _score_category(text: str, category: dict, audio_features: dict, emotional_arc: dict | None = None) -> dict:
    lowered = text.lower()
    marker_hits = []
    score = 0.0
    for marker in category.get("markers", []):
        if marker.lower() in lowered:
            marker_hits.append(marker)
            score += float(category.get("marker_weight", 1.0))

    wpm = audio_features.get("overall_words_per_minute")
    pacing = category.get("pacing", {})
    if wpm and pacing:
        minimum = pacing.get("min_wpm", 0)
        maximum = pacing.get("max_wpm", 999)
        if minimum <= wpm <= maximum:
            score += 0.8
            marker_hits.append(f"pacing:{wpm}wpm")

    if emotional_arc:
        tones = [item.get("dominant_tone") for item in emotional_arc.get("segments", [])]
        for tone in category.get("tones", []):
            if tone in tones:
                score += 0.6
                marker_hits.append(f"tone:{tone}")

    return {"raw_score": round(score, 3), "evidence": marker_hits[:10]}


def _classify(segments: dict, transcript: dict, audio_features: dict, taxonomy: dict, emotional_arc: dict | None = None) -> dict:
    text = _all_text(segments, transcript)
    scored = []
    for category in taxonomy.get("categories", []):
        result = _score_category(text, category, audio_features, emotional_arc)
        scored.append(
            {
                "category": category["id"],
                "label": category.get("label", category["id"]),
                "weight": result["raw_score"],
                "evidence": result["evidence"],
                "description": category.get("description", ""),
            }
        )

    max_score = max([item["weight"] for item in scored] + [0.0])
    for item in scored:
        item["weight"] = round(item["weight"] / max_score, 3) if max_score else 0.0
    scored.sort(key=lambda item: item["weight"], reverse=True)
    return {
        "classification_status": "complete" if text.strip() else "limited",
        "method": "taxonomy_marker_pacing_tone_heuristic_v1",
        "disclaimer": "Categories describe observed communication style, not personal identity.",
        "top_categories": scored[:6],
        "all_categories": scored,
    }


def classify_persona_style(
    segments: dict,
    transcript: dict,
    audio_features: dict,
    emotional_arc: dict,
    taxonomy: dict,
) -> dict:
    return _classify(segments, transcript, audio_features, taxonomy, emotional_arc)


def classify_teaching_style(segments: dict, transcript: dict, audio_features: dict, taxonomy: dict) -> dict:
    return _classify(segments, transcript, audio_features, taxonomy, None)
