"""Deeper deterministic rhetorical feature analysis."""

from __future__ import annotations

import re
from collections import Counter

from report_generator import words
from stability import STATUS_COMPLETE, STATUS_LIMITED

MARKER_GROUPS = {
    "claim": ["i think", "i believe", "the point is", "the truth is", "is that", "means that"],
    "example": ["for example", "for instance", "imagine", "suppose", "like when", "such as"],
    "contrast": ["but", "however", "instead", "whereas", "on the other hand", "although"],
    "causal": ["because", "therefore", "so", "as a result", "which means", "that's why"],
    "instruction": ["you should", "you need", "you have to", "do this", "try", "let's"],
    "self_reference": ["i ", "i'm", "i've", "my ", "me ", "we ", "our "],
    "audience_address": ["you ", "your ", "you're", "you've", "anyone", "people"],
    "motivational": ["can", "better", "worth", "important", "listen", "care", "build"],
    "philosophical_abstract": ["meaning", "truth", "identity", "belief", "value", "principle", "why"],
    "concrete_actionable": ["step", "make", "write", "cut", "show", "ask", "practice", "example"],
}


def _count_phrases(text: str, phrases: list[str]) -> int:
    lowered = f" {(text or '').lower()} "
    return sum(lowered.count(phrase) for phrase in phrases)


def _density(count: int, word_count: int) -> float:
    return round(count / max(word_count, 1) * 100.0, 6)


def _snippet(text: str, phrase: str) -> str | None:
    lowered = text.lower()
    index = lowered.find(phrase.strip())
    if index < 0:
        return None
    start = max(0, index - 70)
    end = min(len(text), index + len(phrase) + 90)
    return " ".join(text[start:end].split())


def _mode(counts: dict[str, int]) -> str:
    priorities = {
        "instruction": "instructional",
        "example": "example-driven",
        "causal": "explanatory",
        "contrast": "contrastive",
        "audience_address": "audience-address",
        "philosophical_abstract": "abstract-reflective",
        "concrete_actionable": "concrete-actionable",
    }
    if not any(counts.values()):
        return "low-marker"
    key = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
    return priorities.get(key, key.replace("_", "-"))


def analyze_rhetoric(transcript: dict, scene_segments: dict) -> dict:
    segments = scene_segments.get("segments") or []
    if not segments:
        return {
            "analysis_status": STATUS_LIMITED,
            "method": "deterministic_marker_density",
            "segments": [],
            "global_counts": {},
            "limitations": ["No segments were available for rhetorical analysis."],
        }

    segment_rows = []
    transitions = []
    global_counts: Counter[str] = Counter()
    for segment in segments:
        text = segment.get("text", "")
        token_count = len(words(text))
        question_count = text.count("?") + len(re.findall(r"\b(why|what|how|when|where|who)\b", text.lower()))
        counts = {label: _count_phrases(text, phrases) for label, phrases in MARKER_GROUPS.items()}
        counts["question"] = question_count
        for key, value in counts.items():
            global_counts[key] += value
        evidence = []
        for label, phrases in MARKER_GROUPS.items():
            for phrase in phrases:
                found = _snippet(text, phrase)
                if found:
                    evidence.append({"marker_type": label, "snippet": found})
                    break
        row = {
            "segment_id": segment.get("segment_id"),
            "start_sec": segment.get("start_sec"),
            "end_sec": segment.get("end_sec"),
            "word_count": token_count,
            "question_density": _density(question_count, token_count),
            "claim_density": _density(counts["claim"], token_count),
            "example_density": _density(counts["example"], token_count),
            "contrast_markers": counts["contrast"],
            "causal_markers": counts["causal"],
            "instruction_markers": counts["instruction"],
            "self_reference_markers": counts["self_reference"],
            "audience_address_markers": counts["audience_address"],
            "motivational_markers": counts["motivational"],
            "philosophical_abstract_markers": counts["philosophical_abstract"],
            "concrete_actionable_markers": counts["concrete_actionable"],
            "rhetorical_mode": _mode(counts),
            "evidence_snippets": evidence[:6],
        }
        segment_rows.append(row)

    for left, right in zip(segment_rows, segment_rows[1:]):
        transitions.append(
            {
                "from_segment_id": left["segment_id"],
                "to_segment_id": right["segment_id"],
                "from_mode": left["rhetorical_mode"],
                "to_mode": right["rhetorical_mode"],
                "transition_type": "mode_shift" if left["rhetorical_mode"] != right["rhetorical_mode"] else "mode_continuation",
            }
        )

    claim = global_counts.get("claim", 0)
    examples = global_counts.get("example", 0)
    abstract = global_counts.get("philosophical_abstract", 0)
    concrete = global_counts.get("concrete_actionable", 0)
    balance_parts = [
        1.0 - abs(claim - examples) / max(claim + examples, 1),
        1.0 - abs(abstract - concrete) / max(abstract + concrete, 1),
    ]
    return {
        "analysis_status": STATUS_COMPLETE if any(row["word_count"] for row in segment_rows) else STATUS_LIMITED,
        "method": "deterministic_marker_density",
        "global_counts": dict(sorted(global_counts.items())),
        "global_densities_per_100_words": {
            key: _density(value, sum(row["word_count"] for row in segment_rows))
            for key, value in sorted(global_counts.items())
        },
        "segments": segment_rows,
        "rhetorical_transitions": transitions,
        "rhetorical_balance_score": round(sum(balance_parts) / len(balance_parts), 6),
        "limitations": [
            "Rhetorical modes are marker-based heuristics, not intent detection.",
            "Evidence snippets preserve local text cues for human review.",
        ],
    }
