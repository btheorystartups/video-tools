"""Deterministic local transcript topic and concept analysis."""

from __future__ import annotations

import math
import re
from collections import Counter

from report_generator import STOPWORDS, keyword_counts, words
from stability import STATUS_COMPLETE, STATUS_LIMITED

QUESTION_WORDS = {"what", "why", "how", "when", "where", "who", "which"}


def _segment_keywords(text: str, limit: int = 8) -> list[dict]:
    return keyword_counts(text, limit)


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    return len(left & right) / max(len(left | right), 1)


def _question_concepts(transcript_segments: list[dict]) -> list[dict]:
    counts: Counter[str] = Counter()
    for segment in transcript_segments:
        text = segment.get("text", "")
        if "?" not in text and not any(text.lower().strip().startswith(word + " ") for word in QUESTION_WORDS):
            continue
        counts.update(token for token in words(text) if len(token) > 2 and token not in STOPWORDS)
    return [{"term": term, "count": count} for term, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:20]]


def _fallback_topic_analysis(transcript: dict, scene_segments: dict, limitation: str | None = None) -> dict:
    text = transcript.get("text", "")
    segments = scene_segments.get("segments") or []
    per_segment = []
    sets = []
    for segment in segments:
        kws = _segment_keywords(segment.get("text", ""))
        keyword_set = {item["term"] for item in kws}
        sets.append(keyword_set)
        per_segment.append(
            {
                "segment_id": segment.get("segment_id"),
                "start_sec": segment.get("start_sec"),
                "end_sec": segment.get("end_sec"),
                "keywords": kws,
                "topic_label": ", ".join(item["term"] for item in kws[:3]) or "no transcript terms",
            }
        )
    continuity = []
    for left, right, left_seg, right_seg in zip(sets, sets[1:], segments, segments[1:]):
        score = round(_jaccard(left, right), 6)
        continuity.append(
            {
                "from_segment_id": left_seg.get("segment_id"),
                "to_segment_id": right_seg.get("segment_id"),
                "continuity_score": score,
                "shift_likelihood": round(1.0 - score, 6),
            }
        )
    drift = round(sum(item["shift_likelihood"] for item in continuity) / max(len(continuity), 1), 6) if continuity else 0.0
    repeated = [
        {"term": item["term"], "count": item["count"]}
        for item in keyword_counts(text, 80)
        if item["count"] > 1
    ][:30]
    limitations = ["Frequency fallback does not model semantic similarity."]
    if limitation:
        limitations.insert(0, limitation)
    return {
        "analysis_status": STATUS_LIMITED if limitation else STATUS_COMPLETE,
        "method": "deterministic_frequency_keywords",
        "top_global_keywords": keyword_counts(text, 30),
        "per_segment_keywords": per_segment,
        "tfidf_weighted_terms": [],
        "repeated_concepts": repeated,
        "question_heavy_concepts": _question_concepts(transcript.get("segments") or []),
        "segment_to_segment_topic_continuity": continuity,
        "likely_topic_shifts": [item for item in continuity if item["shift_likelihood"] >= 0.72],
        "topic_drift_score": drift,
        "topic_cluster_labels": [],
        "limitations": limitations,
    }


def analyze_topics(transcript: dict, scene_segments: dict) -> dict:
    segments = scene_segments.get("segments") or []
    texts = [segment.get("text", "") for segment in segments]
    if not any(text.strip() for text in texts):
        result = _fallback_topic_analysis(transcript, scene_segments)
        result["analysis_status"] = STATUS_LIMITED
        result["limitations"].insert(0, "Transcript text is unavailable; topic analysis has no language evidence.")
        return result

    try:
        from sklearn.cluster import KMeans
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except Exception as exc:  # pragma: no cover - optional dependency
        return _fallback_topic_analysis(transcript, scene_segments, f"scikit-learn unavailable; used deterministic fallback: {exc}")

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words=sorted(STOPWORDS),
        token_pattern=r"(?u)\b[a-zA-Z][\w']{2,}\b",
        ngram_range=(1, 2),
        max_features=80,
    )
    try:
        matrix = vectorizer.fit_transform(texts)
    except ValueError as exc:
        return _fallback_topic_analysis(transcript, scene_segments, f"TF-IDF could not be fit; used fallback: {exc}")

    terms = vectorizer.get_feature_names_out()
    sums = matrix.sum(axis=0).A1
    global_terms = [
        {"term": str(term), "weight": round(float(weight), 6)}
        for term, weight in sorted(zip(terms, sums), key=lambda item: (-float(item[1]), str(item[0])))[:30]
    ]
    per_segment = []
    for row_index, segment in enumerate(segments):
        row = matrix.getrow(row_index)
        pairs = [(terms[index], row[0, index]) for index in row.indices]
        top = [
            {"term": str(term), "weight": round(float(weight), 6)}
            for term, weight in sorted(pairs, key=lambda item: (-float(item[1]), str(item[0])))[:8]
        ]
        per_segment.append(
            {
                "segment_id": segment.get("segment_id"),
                "start_sec": segment.get("start_sec"),
                "end_sec": segment.get("end_sec"),
                "keywords": top,
                "topic_label": ", ".join(item["term"] for item in top[:3]) or "no transcript terms",
            }
        )

    similarity = cosine_similarity(matrix)
    continuity = []
    for index, (left, right) in enumerate(zip(segments, segments[1:])):
        score = round(float(similarity[index, index + 1]), 6)
        continuity.append(
            {
                "from_segment_id": left.get("segment_id"),
                "to_segment_id": right.get("segment_id"),
                "continuity_score": score,
                "shift_likelihood": round(1.0 - score, 6),
            }
        )
    drift = round(sum(item["shift_likelihood"] for item in continuity) / max(len(continuity), 1), 6) if continuity else 0.0

    labels = []
    if len(segments) >= 3 and matrix.shape[0] >= 3:
        cluster_count = min(4, max(2, int(math.sqrt(len(segments)))))
        try:
            model = KMeans(n_clusters=cluster_count, random_state=7, n_init=10)
            assigned = model.fit_predict(matrix)
            for cluster in range(cluster_count):
                members = [segments[i].get("segment_id") for i, value in enumerate(assigned) if value == cluster]
                center = model.cluster_centers_[cluster]
                top_indices = center.argsort()[::-1][:4]
                labels.append(
                    {
                        "cluster_id": f"topic_cluster_{cluster + 1}",
                        "label": ", ".join(str(terms[i]) for i in top_indices if center[i] > 0) or "low evidence",
                        "segment_ids": members,
                    }
                )
        except Exception:
            labels = []

    repeated_counts = Counter(token for token in words(transcript.get("text", "")) if len(token) > 2 and token not in STOPWORDS)
    return {
        "analysis_status": STATUS_COMPLETE,
        "method": "local_tfidf_deterministic",
        "top_global_keywords": keyword_counts(transcript.get("text", ""), 30),
        "per_segment_keywords": per_segment,
        "tfidf_weighted_terms": global_terms,
        "repeated_concepts": [
            {"term": term, "count": count}
            for term, count in sorted(repeated_counts.items(), key=lambda item: (-item[1], item[0]))
            if count > 1
        ][:30],
        "question_heavy_concepts": _question_concepts(transcript.get("segments") or []),
        "segment_to_segment_topic_continuity": continuity,
        "likely_topic_shifts": [item for item in continuity if item["shift_likelihood"] >= 0.68],
        "topic_drift_score": drift,
        "topic_cluster_labels": labels,
        "limitations": [
            "TF-IDF keywords reflect surface terms, not embedding-level semantic meaning.",
            "Topic shifts are deterministic similarity heuristics for human review.",
        ],
    }
