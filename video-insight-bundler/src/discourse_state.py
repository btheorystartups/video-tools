"""Deterministic discourse-state tracking across transcript segments."""

from __future__ import annotations

import re
from collections import Counter
from statistics import mean
from typing import Any

from report_generator import STOPWORDS, keyword_counts, words
from rhetorical_coherence import (
    CLAIM_RE,
    EXAMPLE_RE,
    QUESTION_RE,
    SETUP_RE,
    TAKEAWAY_RE,
)
from stability import STATUS_COMPLETE, STATUS_LIMITED, deterministic_id


ABSTRACT_TERMS = {"meaning", "truth", "identity", "belief", "value", "principle", "why", "purpose", "idea"}
CONCRETE_TERMS = {"example", "step", "make", "write", "show", "ask", "practice", "cut", "listen", "try"}
AUDIENCE_RE = re.compile(r"\b(you|your|you're|you've|anyone|people|viewer|audience)\b", re.I)
INSTRUCTION_RE = re.compile(r"\b(should|need to|have to|try|do this|make sure|start|stop|remember)\b", re.I)
PERSUASION_RE = re.compile(r"\b(because|therefore|so|that's why|means that|important|the point)\b", re.I)
DEFER_RE = re.compile(r"\b(later|come back|we'll return|hold that|for now|defer|before we answer)\b", re.I)
CALLBACK_RE = re.compile(r"\b(as i said|earlier|before|back to|remember|return to|again|that question)\b", re.I)


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 3)


def _tokens(text: str) -> list[str]:
    return [token for token in words(text) if len(token) > 2 and token not in STOPWORDS]


def _state_counts(text: str) -> dict[str, int]:
    tokens = _tokens(text)
    token_set = set(tokens)
    return {
        "claim": 1 if CLAIM_RE.search(text or "") else 0,
        "example": 1 if EXAMPLE_RE.search(text or "") else 0,
        "question": 1 if QUESTION_RE.search(text or "") else 0,
        "setup": 1 if SETUP_RE.search(text or "") else 0,
        "takeaway": 1 if TAKEAWAY_RE.search(text or "") else 0,
        "abstract": sum(1 for token in tokens if token in ABSTRACT_TERMS),
        "concrete": sum(1 for token in tokens if token in CONCRETE_TERMS),
        "audience": 1 if AUDIENCE_RE.search(text or "") else 0,
        "instruction": 1 if INSTRUCTION_RE.search(text or "") else 0,
        "persuasion": 1 if PERSUASION_RE.search(text or "") else 0,
        "deferred": 1 if DEFER_RE.search(text or "") else 0,
        "callback": 1 if CALLBACK_RE.search(text or "") else 0,
        "concept_count": len(token_set),
    }


def _compact_items(rows: list[dict], limit: int = 24) -> list[dict]:
    return sorted(rows, key=lambda row: (row.get("segment_id") or "", row.get("item_id") or ""))[:limit]


def _snapshot(active: dict[str, int], unresolved: list[dict], rhetorical_promises: list[dict], pending_examples: list[dict], questions: list[dict], deferred: list[dict], callbacks: list[dict], counts: dict[str, int]) -> dict:
    active_terms = sorted(active, key=lambda term: (-active[term], term))
    return {
        "active_concepts": active_terms[:18],
        "inactive_concepts": active_terms[18:36],
        "unresolved_concepts": sorted({item.get("concept") for item in unresolved if item.get("concept")})[:18],
        "rhetorical_promises": _compact_items(rhetorical_promises),
        "pending_examples": _compact_items(pending_examples),
        "unresolved_questions": _compact_items(questions),
        "callbacks": _compact_items(callbacks),
        "deferred_claims": _compact_items(deferred),
        "abstract_frames": counts.get("abstract", 0),
        "concrete_frames": counts.get("concrete", 0),
        "audience_address_state": "active" if counts.get("audience") else "inactive",
        "instruction_state": "active" if counts.get("instruction") else "inactive",
        "persuasion_state": "active" if counts.get("persuasion") else "inactive",
    }


def analyze_discourse_state(
    transcript: dict,
    scene_segments: dict,
    topic_analysis: dict | None = None,
    rhetorical_analysis: dict | None = None,
    topic_continuity: dict | None = None,
    rhetorical_coherence: dict | None = None,
) -> dict:
    """Track local discourse state using deterministic surface markers."""

    segments = scene_segments.get("segments") or []
    if not segments:
        return {
            "analysis_status": STATUS_LIMITED,
            "method": "deterministic_discourse_state_v1",
            "segment_discourse_states": [],
            "persistent_concepts": [],
            "concept_expiration": [],
            "unresolved_discourse_items": [],
            "discourse_transitions": [],
            "discourse_pressure_score": 0.0,
            "discourse_continuity_score": 0.0,
            "limitations": ["No segments were available for discourse-state tracking."],
        }

    active: Counter[str] = Counter()
    last_seen: dict[str, int] = {}
    concept_segments: dict[str, list[str]] = {}
    unresolved: list[dict] = []
    rhetorical_promises: list[dict] = []
    pending_examples: list[dict] = []
    unresolved_questions: list[dict] = []
    callbacks: list[dict] = []
    deferred_claims: list[dict] = []
    segment_states = []
    expired_rows = []
    pressure_scores = []
    continuity_scores = []
    previous_exit: dict[str, Any] | None = None

    for index, segment in enumerate(segments):
        segment_id = segment.get("segment_id")
        text = segment.get("text", "")
        counts = _state_counts(text)
        terms = sorted(set(_tokens(text)))
        entering = _snapshot(active, unresolved, rhetorical_promises, pending_examples, unresolved_questions, deferred_claims, callbacks, counts)

        for term in terms:
            active[term] += 1
            last_seen[term] = index
            concept_segments.setdefault(term, []).append(segment_id)

        expired = []
        for term, seen_index in sorted(list(last_seen.items())):
            if index - seen_index > 3:
                expired.append(term)
                active.pop(term, None)
                last_seen.pop(term, None)
        for term in expired:
            expired_rows.append(
                {
                    "concept": term,
                    "expired_after_segment_id": segment_id,
                    "expiration_window_segments": 3,
                }
            )

        primary_concept = terms[0] if terms else "limited_transcript_evidence"
        if counts["question"]:
            unresolved_questions.append(
                {
                    "item_id": deterministic_id("DSQ", segment_id, text[:80]),
                    "segment_id": segment_id,
                    "concept": primary_concept,
                    "item_type": "unresolved_question",
                }
            )
        if counts["claim"] and not counts["example"]:
            pending_examples.append(
                {
                    "item_id": deterministic_id("DPE", segment_id, text[:80]),
                    "segment_id": segment_id,
                    "concept": primary_concept,
                    "item_type": "pending_example",
                }
            )
        if counts["setup"]:
            rhetorical_promises.append(
                {
                    "item_id": deterministic_id("DSP", segment_id, text[:80]),
                    "segment_id": segment_id,
                    "concept": primary_concept,
                    "item_type": "rhetorical_promise",
                }
            )
        if counts["deferred"] or (counts["claim"] and counts["abstract"] and not counts["concrete"]):
            deferred_claims.append(
                {
                    "item_id": deterministic_id("DDC", segment_id, text[:80]),
                    "segment_id": segment_id,
                    "concept": primary_concept,
                    "item_type": "deferred_claim",
                }
            )

        if counts["example"] or counts["takeaway"]:
            pending_examples = pending_examples[1:] if pending_examples else pending_examples
        if counts["takeaway"] or re.search(r"\b(answer|because|therefore|so)\b", text or "", re.I):
            unresolved_questions = unresolved_questions[1:] if unresolved_questions else unresolved_questions
            rhetorical_promises = rhetorical_promises[1:] if rhetorical_promises else rhetorical_promises
            deferred_claims = deferred_claims[1:] if deferred_claims else deferred_claims
        if counts["callback"] or any(term in active for term in terms if index - last_seen.get(term, index) > 1):
            callbacks.append(
                {
                    "item_id": deterministic_id("DCB", segment_id, ",".join(terms[:5])),
                    "segment_id": segment_id,
                    "concepts": terms[:6],
                    "callback_type": "explicit" if counts["callback"] else "concept_resurfacing",
                }
            )

        unresolved = rhetorical_promises + pending_examples + unresolved_questions + deferred_claims
        pressure = _clamp(
            min(len(unresolved), 10) / 10.0 * 0.55
            + min(counts["abstract"] / 4.0, 1.0) * 0.2
            + (0.15 if counts["question"] else 0.0)
            + (0.1 if counts["deferred"] else 0.0)
        )
        pressure_scores.append(pressure)
        exiting = _snapshot(active, unresolved, rhetorical_promises, pending_examples, unresolved_questions, deferred_claims, callbacks, counts)
        if previous_exit:
            left_terms = set(previous_exit.get("active_concepts") or [])
            right_terms = set(exiting.get("active_concepts") or [])
            continuity = _clamp(len(left_terms & right_terms) / max(len(left_terms | right_terms), 1))
        else:
            continuity = 1.0
        continuity_scores.append(continuity)
        segment_states.append(
            {
                "state_id": deterministic_id("DST", segment_id, index),
                "segment_id": segment_id,
                "start_sec": segment.get("start_sec"),
                "end_sec": segment.get("end_sec"),
                "entering_state": entering,
                "exiting_state": exiting,
                "state_events": {
                    "introduced_concepts": terms[:12],
                    "expired_concepts": expired[:12],
                    "has_claim": bool(counts["claim"]),
                    "has_example": bool(counts["example"]),
                    "has_question": bool(counts["question"]),
                    "has_takeaway": bool(counts["takeaway"]),
                    "has_callback": bool(counts["callback"]),
                },
                "discourse_pressure_score": pressure,
                "discourse_continuity_score": continuity,
            }
        )
        previous_exit = exiting

    transitions = []
    bridge_by_pair = {
        (row.get("from_segment_id"), row.get("to_segment_id")): row
        for row in (topic_continuity or {}).get("topic_bridge_terms", [])
    }
    for left, right in zip(segment_states, segment_states[1:]):
        pair = (left["segment_id"], right["segment_id"])
        topic_bridge = bridge_by_pair.get(pair, {})
        carryover = sorted(set(left["exiting_state"].get("active_concepts", [])) & set(right["entering_state"].get("active_concepts", [])))
        transitions.append(
            {
                "transition_id": deterministic_id("DTR", left["segment_id"], right["segment_id"]),
                "from_segment_id": left["segment_id"],
                "to_segment_id": right["segment_id"],
                "carryover_concepts": carryover[:12],
                "topic_bridge_terms": topic_bridge.get("bridge_terms", [])[:12],
                "discourse_continuation_evidence": _clamp((len(carryover) / 8.0) + float(topic_bridge.get("bridge_strength") or 0.0) * 0.5),
                "unresolved_pressure_carryover": _clamp((left["discourse_pressure_score"] + right["discourse_pressure_score"]) / 2.0),
            }
        )

    repeated = Counter(term for term, ids in concept_segments.items() if len(set(ids)) > 1)
    persistent = [
        {
            "concept": term,
            "segment_ids": sorted(set(ids)),
            "persistence_count": len(set(ids)),
        }
        for term, ids in sorted(concept_segments.items(), key=lambda item: (-len(set(item[1])), item[0]))
        if len(set(ids)) > 1
    ][:40]
    unresolved_items = _compact_items(unresolved, 60)
    return {
        "analysis_status": STATUS_COMPLETE if any(segment.get("text") for segment in segments) else STATUS_LIMITED,
        "method": "deterministic_discourse_state_v1",
        "segment_discourse_states": segment_states,
        "persistent_concepts": persistent,
        "concept_expiration": expired_rows[:80],
        "unresolved_discourse_items": unresolved_items,
        "discourse_transitions": transitions,
        "discourse_pressure_score": _clamp(mean(pressure_scores) if pressure_scores else 0.0),
        "discourse_continuity_score": _clamp(mean(continuity_scores) if continuity_scores else 0.0),
        "source_repeated_concepts": (topic_analysis or {}).get("repeated_concepts", [])[:20] or keyword_counts(transcript.get("text", ""), 20),
        "source_rhetorical_gaps": (rhetorical_coherence or {}).get("rhetorical_gap_explanations", [])[:30],
        "limitations": [
            "Discourse state is deterministic marker and term-window evidence for editorial review.",
            "It is not semantic truth, intent detection, or an autonomous edit decision.",
        ],
    }
