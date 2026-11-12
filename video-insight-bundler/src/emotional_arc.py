"""Transparent heuristic emotional arc scoring."""

from __future__ import annotations

from stability import deterministic_id

POSITIVE = {"good", "great", "better", "love", "clear", "success", "useful", "strong", "win", "hope"}
NEGATIVE = {"bad", "worse", "problem", "fail", "risk", "wrong", "hard", "pain", "fear", "loss"}
CERTAINTY = {"must", "will", "always", "never", "clearly", "definitely", "certainly", "proven"}
UNCERTAINTY = {"maybe", "perhaps", "might", "could", "possibly", "unclear", "seems"}
INTENSIFIERS = {"very", "extremely", "critical", "urgent", "massive", "deeply", "really", "absolutely"}
TONES = {
    "analytical": {"because", "therefore", "data", "pattern", "model", "system", "evidence"},
    "instructional": {"step", "first", "next", "should", "need", "practice", "learn"},
    "motivational": {"can", "build", "grow", "future", "possible", "believe", "change"},
    "critical": {"problem", "risk", "wrong", "failure", "broken", "avoid"},
    "reflective": {"meaning", "think", "understand", "life", "question", "truth"},
}


def _tokens(text: str) -> set[str]:
    return {token.strip(".,!?;:\"'()[]{}").lower() for token in text.split() if token.strip()}


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 3)


def _dominant_tone(tokens: set[str]) -> tuple[str, list[str]]:
    scores = []
    for tone, markers in TONES.items():
        hits = sorted(tokens & markers)
        scores.append((len(hits), tone, hits))
    scores.sort(reverse=True)
    if scores and scores[0][0] > 0:
        return scores[0][1], scores[0][2]
    return "neutral", []


def build_emotional_arc(
    scene_segments: dict,
    transcript: dict,
    audio_features: dict,
    source_hash: str | None = None,
    profile_hash: str | None = None,
) -> dict:
    results = []
    for segment in scene_segments.get("segments", []):
        text = segment.get("text", "")
        tokens = _tokens(text)
        positive_hits = sorted(tokens & POSITIVE)
        negative_hits = sorted(tokens & NEGATIVE)
        certainty_hits = sorted(tokens & CERTAINTY)
        uncertainty_hits = sorted(tokens & UNCERTAINTY)
        intensifier_hits = sorted(tokens & INTENSIFIERS)
        tone, tone_evidence = _dominant_tone(tokens)
        speech_rate = float(segment.get("speech_rate_wpm") or 0.0)

        valence = 0.5 + (0.08 * len(positive_hits)) - (0.08 * len(negative_hits))
        certainty = 0.55 + (0.08 * len(certainty_hits)) - (0.08 * len(uncertainty_hits))
        energy = 0.35 + min(speech_rate, 220.0) / 400.0 + (0.04 * len(intensifier_hits))
        intensity = 0.25 + (0.08 * len(positive_hits + negative_hits + intensifier_hits))
        if "critical" == tone:
            intensity += 0.12

        evidence = []
        for label, hits in (
            ("positive", positive_hits),
            ("negative", negative_hits),
            ("certainty", certainty_hits),
            ("uncertainty", uncertainty_hits),
            ("intensity", intensifier_hits),
            ("tone", tone_evidence),
        ):
            if hits:
                evidence.append(f"{label} markers: {', '.join(hits[:8])}")
        if speech_rate:
            evidence.append(f"speech rate: {speech_rate:.1f} wpm")
        if not evidence:
            evidence.append("No strong lexical or pacing signal; neutral fallback.")

        results.append(
            {
                "arc_entry_id": deterministic_id(
                    "ARC",
                    source_hash or "",
                    profile_hash or "",
                    segment.get("segment_id"),
                    segment.get("start_sec"),
                    segment.get("end_sec"),
                ),
                "segment_id": segment.get("segment_id"),
                "start_sec": segment.get("start_sec"),
                "end_sec": segment.get("end_sec"),
                "energy": _clamp(energy),
                "valence": _clamp(valence),
                "certainty": _clamp(certainty),
                "intensity": _clamp(intensity),
                "dominant_tone": tone,
                "evidence": evidence,
            }
        )

    return {
        "analysis_status": "complete" if results else "limited",
        "model": "transparent_lexical_pacing_heuristic_v1",
        "disclaimer": "Scores are communication-style signals, not psychological or clinical claims.",
        "segments": results,
    }
