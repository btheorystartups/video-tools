"""Deterministic callback and setup/payoff resolution analysis."""

from __future__ import annotations

import re
from statistics import mean

from report_generator import STOPWORDS, words
from rhetorical_coherence import EXAMPLE_RE, PAYOFF_RE, QUESTION_RE, SETUP_RE, TAKEAWAY_RE
from stability import STATUS_COMPLETE, STATUS_LIMITED, deterministic_id


CLARIFY_RE = re.compile(r"\b(in other words|to be clear|meaning|that means|the answer|because|therefore)\b", re.I)
CALLBACK_RE = re.compile(r"\b(earlier|before|remember|back to|again|return to|as i said)\b", re.I)


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 3)


def _tokens(text: str) -> set[str]:
    return {token for token in words(text) if len(token) > 2 and token not in STOPWORDS}


def _setup_type(text: str) -> str:
    if QUESTION_RE.search(text or ""):
        return "question"
    if SETUP_RE.search(text or ""):
        return "setup"
    if re.search(r"\b(problem|promise|first|start|begin)\b", text or "", re.I):
        return "rhetorical_setup"
    return "concept_introduction"


def _payoff_type(text: str) -> str:
    if PAYOFF_RE.search(text or "") or TAKEAWAY_RE.search(text or ""):
        return "payoff"
    if EXAMPLE_RE.search(text or ""):
        return "delayed_example"
    if CLARIFY_RE.search(text or ""):
        return "delayed_clarification"
    return "concept_callback"


def analyze_callback_resolution(
    scene_segments: dict,
    discourse_state: dict | None = None,
    rhetorical_coherence: dict | None = None,
    narrative_memory: dict | None = None,
) -> dict:
    segments = scene_segments.get("segments") or []
    if not segments:
        return {
            "analysis_status": STATUS_LIMITED,
            "method": "deterministic_callback_resolution_v1",
            "callback_pairs": [],
            "setup_payoff_latency": [],
            "unresolved_setups": [],
            "weak_callback_evidence": [],
            "callback_strength_score": 0.0,
            "payoff_quality_score": 0.0,
            "limitations": ["No segments were available for callback resolution analysis."],
        }

    setups = []
    pairs = []
    weak = []
    for index, segment in enumerate(segments):
        text = segment.get("text", "")
        tokens = _tokens(text)
        is_setup = bool(QUESTION_RE.search(text or "") or SETUP_RE.search(text or "") or (tokens and index == 0))
        is_payoff = bool(PAYOFF_RE.search(text or "") or TAKEAWAY_RE.search(text or "") or EXAMPLE_RE.search(text or "") or CLARIFY_RE.search(text or "") or CALLBACK_RE.search(text or ""))
        if is_setup:
            setups.append(
                {
                    "setup_id": deterministic_id("CBS", segment.get("segment_id"), text[:90]),
                    "segment_id": segment.get("segment_id"),
                    "segment_index": index,
                    "setup_type": _setup_type(text),
                    "concept_terms": sorted(tokens)[:12],
                    "resolved": False,
                }
            )
        if not is_payoff:
            continue
        best = None
        best_score = 0.0
        for setup in setups:
            if setup["resolved"] or setup["segment_index"] >= index:
                continue
            shared = set(setup["concept_terms"]) & tokens
            marker_bonus = 0.28 if PAYOFF_RE.search(text or "") or TAKEAWAY_RE.search(text or "") else 0.12
            explicit_bonus = 0.22 if CALLBACK_RE.search(text or "") or CLARIFY_RE.search(text or "") else 0.0
            score = _clamp(len(shared) / max(len(setup["concept_terms"]), 1) + marker_bonus + explicit_bonus)
            if score > best_score:
                best = setup
                best_score = score
        if best and best_score >= 0.22:
            best["resolved"] = True
            latency = index - best["segment_index"]
            quality = _clamp(best_score * 0.72 + (0.18 if latency <= 3 else 0.08) + (0.1 if EXAMPLE_RE.search(text or "") else 0.0))
            pairs.append(
                {
                    "callback_id": deterministic_id("CBP", best["setup_id"], segment.get("segment_id")),
                    "setup_segment_id": best["segment_id"],
                    "payoff_segment_id": segment.get("segment_id"),
                    "setup_type": best["setup_type"],
                    "payoff_type": _payoff_type(text),
                    "setup_terms": best["concept_terms"],
                    "payoff_terms": sorted(tokens)[:12],
                    "shared_terms": sorted(set(best["concept_terms"]) & tokens)[:12],
                    "latency_segments": latency,
                    "resolution_confidence": best_score,
                    "payoff_quality": quality,
                    "strength_class": "strong_payoff" if quality >= 0.68 else "weak_payoff" if quality < 0.42 else "moderate_payoff",
                }
            )
        elif is_payoff:
            weak.append(
                {
                    "segment_id": segment.get("segment_id"),
                    "evidence_type": _payoff_type(text),
                    "reason": "Payoff or callback marker lacked a strong earlier setup match.",
                    "concept_terms": sorted(tokens)[:12],
                }
            )

    unresolved = [
        {
            "setup_id": setup["setup_id"],
            "setup_segment_id": setup["segment_id"],
            "setup_type": setup["setup_type"],
            "concept_terms": setup["concept_terms"],
            "recommendation_hint": f"Add payoff for setup introduced in segment {setup['segment_id']}.",
        }
        for setup in setups
        if not setup.get("resolved")
    ]
    latency = [
        {
            "callback_id": pair["callback_id"],
            "setup_segment_id": pair["setup_segment_id"],
            "payoff_segment_id": pair["payoff_segment_id"],
            "latency_segments": pair["latency_segments"],
            "resolution_confidence": pair["resolution_confidence"],
        }
        for pair in pairs
    ]
    callback_score = _clamp(mean([pair["resolution_confidence"] for pair in pairs]) if pairs else 0.0)
    payoff_score = _clamp(mean([pair["payoff_quality"] for pair in pairs]) if pairs else 0.0)
    return {
        "analysis_status": STATUS_COMPLETE if any(segment.get("text") for segment in segments) else STATUS_LIMITED,
        "method": "deterministic_callback_resolution_v1",
        "callback_pairs": pairs,
        "setup_payoff_latency": latency,
        "resolution_confidence": callback_score,
        "unresolved_setups": unresolved[:80],
        "weak_callback_evidence": weak[:80],
        "source_setup_payoff_links": (rhetorical_coherence or {}).get("setup_payoff_links", [])[:40],
        "narrative_callback_references": (narrative_memory or {}).get("callback_references", [])[:40],
        "callback_strength_score": callback_score,
        "payoff_quality_score": payoff_score,
        "limitations": [
            "Callback resolution uses deterministic marker and lexical recurrence evidence.",
            "Weak or missing callbacks are editorial review prompts, not proof of audience confusion.",
        ],
    }
