"""Deterministic rhetorical coherence diagnostics."""

from __future__ import annotations

import re
from statistics import mean

from report_generator import words
from rhetorical_analysis import MARKER_GROUPS
from stability import STATUS_COMPLETE, STATUS_LIMITED, deterministic_id


CLAIM_RE = re.compile(r"\b(i think|i believe|the point is|the truth is|means that|because|therefore)\b", re.I)
QUESTION_RE = re.compile(r"\?|^\s*(why|what|how|when|where|who)\b", re.I)
EXAMPLE_RE = re.compile(r"\b(for example|for instance|imagine|suppose|such as|like when)\b", re.I)
TAKEAWAY_RE = re.compile(r"\b(so|therefore|that's why|the takeaway|remember|in short|ultimately)\b", re.I)
SETUP_RE = re.compile(r"\b(first|start|begin|setup|problem|question)\b", re.I)
PAYOFF_RE = re.compile(r"\b(finally|result|payoff|answer|therefore|so)\b", re.I)
CONTRAST_RE = re.compile(r"\b(but|however|instead|although|on the other hand)\b", re.I)
RESOLVE_RE = re.compile(r"\b(so|therefore|that means|instead|the answer|resolve)\b", re.I)


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 3)


def _count(text: str, phrases: list[str]) -> int:
    lowered = f" {(text or '').lower()} "
    return sum(lowered.count(phrase) for phrase in phrases)


def _mode(text: str) -> str:
    counts = {label: _count(text, phrases) for label, phrases in MARKER_GROUPS.items()}
    if QUESTION_RE.search(text or ""):
        counts["question"] = counts.get("question", 0) + 2
    if not any(counts.values()):
        return "low-marker"
    key = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
    return {
        "claim": "claim",
        "example": "example",
        "contrast": "contrast",
        "causal": "explanation",
        "instruction": "instruction",
        "audience_address": "audience-address",
        "philosophical_abstract": "abstract",
        "concrete_actionable": "concrete",
        "question": "question",
    }.get(key, key.replace("_", "-"))


def analyze_rhetorical_coherence(transcript: dict, scene_segments: dict, rhetorical_analysis: dict | None = None) -> dict:
    segments = scene_segments.get("segments") or []
    segment_modes = []
    unresolved_questions = []
    claims_without_examples = []
    examples_without_takeaways = []
    setup_payoff_links = []
    gaps = []
    question_stack: list[dict] = []
    setup_stack: list[dict] = []
    scores = []
    abstract_total = 0
    concrete_total = 0
    for segment in segments:
        text = segment.get("text", "")
        mode = _mode(text)
        claim = bool(CLAIM_RE.search(text))
        question = bool(QUESTION_RE.search(text))
        example = bool(EXAMPLE_RE.search(text))
        takeaway = bool(TAKEAWAY_RE.search(text))
        abstract = _count(text, MARKER_GROUPS["philosophical_abstract"])
        concrete = _count(text, MARKER_GROUPS["concrete_actionable"]) + (1 if example else 0)
        abstract_total += abstract
        concrete_total += concrete
        support_score = _clamp((0.25 if claim else 0.0) + (0.25 if example else 0.0) + (0.2 if takeaway else 0.0) + (0.15 if concrete else 0.0) + (0.15 if words(text) else 0.0))
        scores.append(support_score)
        row = {
            "segment_id": segment.get("segment_id"),
            "start_sec": segment.get("start_sec"),
            "end_sec": segment.get("end_sec"),
            "mode": mode,
            "has_claim": claim,
            "has_question": question,
            "has_example": example,
            "has_takeaway": takeaway,
            "abstract_markers": abstract,
            "concrete_markers": concrete,
            "audience_address_markers": _count(text, MARKER_GROUPS["audience_address"]),
            "support_score": support_score,
        }
        segment_modes.append(row)
        if question:
            question_stack.append(row)
        if question_stack and (TAKEAWAY_RE.search(text) or re.search(r"\b(answer|because|so)\b", text, re.I)):
            question_stack.clear()
        if claim and not example:
            claims_without_examples.append({"segment_id": row["segment_id"], "issue": "claim lacks nearby concrete example"})
        if example and not takeaway:
            examples_without_takeaways.append({"segment_id": row["segment_id"], "issue": "example lacks explicit takeaway marker"})
        if SETUP_RE.search(text):
            setup_stack.append(row)
        if setup_stack and PAYOFF_RE.search(text):
            setup = setup_stack.pop(0)
            setup_payoff_links.append(
                {
                    "link_id": deterministic_id("RPL", setup["segment_id"], row["segment_id"]),
                    "setup_segment_id": setup["segment_id"],
                    "payoff_segment_id": row["segment_id"],
                    "link_strength": 0.72,
                }
            )
        if CONTRAST_RE.search(text) and not RESOLVE_RE.search(text):
            gaps.append({"segment_id": row["segment_id"], "gap_type": "unresolved_contrast", "explanation": "Contrast marker lacks nearby resolution marker."})

    mode_transitions = []
    for left, right in zip(segment_modes, segment_modes[1:]):
        mode_transitions.append(
            {
                "from_segment_id": left["segment_id"],
                "to_segment_id": right["segment_id"],
                "from_mode": left["mode"],
                "to_mode": right["mode"],
                "transition_type": "mode_continuation" if left["mode"] == right["mode"] else "mode_shift",
            }
        )
    unresolved_questions = [
        {"segment_id": row["segment_id"], "issue": "question or question-like setup was not clearly answered later"}
        for row in question_stack
    ]
    balance = _clamp(1.0 - abs(abstract_total - concrete_total) / max(abstract_total + concrete_total, 1))
    penalty = min(0.45, 0.08 * len(unresolved_questions) + 0.05 * len(claims_without_examples) + 0.04 * len(examples_without_takeaways))
    score = _clamp((mean(scores) if scores else 0.0) * 0.55 + balance * 0.45 - penalty)
    gaps.extend(
        {"segment_id": row["segment_id"], "gap_type": "unresolved_question", "explanation": row["issue"]}
        for row in unresolved_questions
    )
    gaps.extend(
        {"segment_id": row["segment_id"], "gap_type": "claim_without_example", "explanation": row["issue"]}
        for row in claims_without_examples[:20]
    )
    return {
        "analysis_status": STATUS_COMPLETE if segments else STATUS_LIMITED,
        "method": "deterministic_rhetorical_coherence_v1",
        "segment_modes": segment_modes,
        "mode_transitions": mode_transitions,
        "unresolved_questions": unresolved_questions,
        "claims_without_examples": claims_without_examples,
        "examples_without_takeaways": examples_without_takeaways,
        "abstract_concrete_balance": {
            "abstract_marker_count": abstract_total,
            "concrete_marker_count": concrete_total,
            "balance_score": balance,
        },
        "setup_payoff_links": setup_payoff_links,
        "rhetorical_coherence_score": score,
        "rhetorical_gap_explanations": gaps,
        "source_rhetorical_balance_score": (rhetorical_analysis or {}).get("rhetorical_balance_score"),
        "limitations": [
            "Rhetorical coherence is marker-based deterministic review evidence.",
            "It is not intent detection and does not guarantee semantic truth.",
        ],
    }
