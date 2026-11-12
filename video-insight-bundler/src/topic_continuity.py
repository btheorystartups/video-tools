"""Deterministic topic continuity diagnostics."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from report_generator import STOPWORDS, keyword_counts, words
from stability import STATUS_COMPLETE, STATUS_LIMITED, deterministic_id


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 3)


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    return len(left & right) / max(len(left | right), 1)


def _tokens(text: str) -> list[str]:
    return [token for token in words(text) if len(token) > 2 and token not in STOPWORDS]


def _cosine_vectors(texts: list[str]) -> tuple[list[dict[str, float]], list[str], str, list[str]]:
    limitations: list[str] = []
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
    except Exception as exc:  # pragma: no cover - optional dependency
        limitations.append(f"scikit-learn unavailable; cosine similarity uses term-frequency fallback: {exc}")
        vectors = []
        vocabulary = sorted({token for text in texts for token in _tokens(text)})
        for text in texts:
            counts = Counter(_tokens(text))
            total = max(sum(counts.values()), 1)
            vectors.append({term: round(counts.get(term, 0) / total, 6) for term in vocabulary if counts.get(term)})
        return vectors, vocabulary, "frequency_jaccard_fallback", limitations

    try:
        vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words=sorted(STOPWORDS),
            token_pattern=r"(?u)\b[a-zA-Z][\w']{2,}\b",
            ngram_range=(1, 2),
            max_features=120,
        )
        matrix = vectorizer.fit_transform(texts)
        terms = list(vectorizer.get_feature_names_out())
        vectors = []
        for index in range(matrix.shape[0]):
            row = matrix.getrow(index)
            vectors.append({str(terms[col]): round(float(row[0, col]), 6) for col in row.indices})
        return vectors, terms, "local_tfidf_with_cosine", limitations
    except Exception as exc:
        limitations.append(f"TF-IDF could not be fit; used term-frequency fallback: {exc}")
        vectors = []
        vocabulary = sorted({token for text in texts for token in _tokens(text)})
        for text in texts:
            counts = Counter(_tokens(text))
            total = max(sum(counts.values()), 1)
            vectors.append({term: round(counts.get(term, 0) / total, 6) for term in vocabulary if counts.get(term)})
        return vectors, vocabulary, "frequency_jaccard_fallback", limitations


def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
    keys = set(left) | set(right)
    if not keys:
        return 1.0
    dot = sum(left.get(key, 0.0) * right.get(key, 0.0) for key in keys)
    left_mag = sum(value * value for value in left.values()) ** 0.5
    right_mag = sum(value * value for value in right.values()) ** 0.5
    if not left_mag or not right_mag:
        return 0.0
    return dot / (left_mag * right_mag)


def analyze_topic_continuity(transcript: dict, scene_segments: dict, topic_analysis: dict | None = None) -> dict:
    segments = scene_segments.get("segments") or []
    texts = [segment.get("text", "") for segment in segments]
    vectors, _terms, method, limitations = _cosine_vectors(texts) if texts else ([], [], "no_segments", [])
    if not any(text.strip() for text in texts):
        limitations.append("Transcript text is unavailable; continuity uses empty language evidence.")

    segment_vectors = []
    term_sets = []
    for segment, vector in zip(segments, vectors):
        top = sorted(vector.items(), key=lambda item: (-item[1], item[0]))[:12]
        term_set = {term for term, value in top if value > 0}
        term_sets.append(term_set)
        segment_vectors.append(
            {
                "segment_id": segment.get("segment_id"),
                "start_sec": segment.get("start_sec"),
                "end_sec": segment.get("end_sec"),
                "terms": [{"term": term, "weight": weight} for term, weight in top],
                "topic_label": ", ".join(term for term, _ in top[:3]) or "limited transcript evidence",
            }
        )

    windows = []
    for index in range(len(segments)):
        start = max(0, index - 1)
        end = min(len(segments), index + 2)
        text = " ".join(texts[start:end])
        windows.append(
            {
                "window_id": deterministic_id("TCW", start + 1, end),
                "segment_ids": [segments[row].get("segment_id") for row in range(start, end)],
                "top_terms": keyword_counts(text, 10),
            }
        )

    repeated_counts = Counter(token for text in texts for token in _tokens(text))
    repeated = [
        {"term": term, "count": count, "segment_ids": [seg.get("segment_id") for seg, text in zip(segments, texts) if term in set(_tokens(text))]}
        for term, count in sorted(repeated_counts.items(), key=lambda item: (-item[1], item[0]))
        if count > 1
    ][:40]

    bridge_terms = []
    abrupt = []
    unsupported = []
    reentry = []
    seen_terms: defaultdict[str, list[int]] = defaultdict(list)
    pair_scores = []
    for index, (left, right) in enumerate(zip(segments, segments[1:])):
        left_terms = term_sets[index] if index < len(term_sets) else set(_tokens(left.get("text", "")))
        right_terms = term_sets[index + 1] if index + 1 < len(term_sets) else set(_tokens(right.get("text", "")))
        shared = sorted(left_terms & right_terms)
        jaccard = _jaccard(left_terms, right_terms)
        cosine = _cosine(vectors[index], vectors[index + 1]) if index + 1 < len(vectors) else jaccard
        continuity = _clamp((jaccard * 0.45) + (cosine * 0.55))
        pair_scores.append(continuity)
        bridge_terms.append(
            {
                "from_segment_id": left.get("segment_id"),
                "to_segment_id": right.get("segment_id"),
                "bridge_terms": shared[:12],
                "bridge_strength": _clamp(len(shared) / max(len(left_terms | right_terms), 1)),
                "jaccard_similarity": round(jaccard, 6),
                "cosine_similarity": round(cosine, 6),
                "continuity_score": continuity,
            }
        )
        if continuity < 0.34:
            row = {
                "from_segment_id": left.get("segment_id"),
                "to_segment_id": right.get("segment_id"),
                "continuity_score": continuity,
                "shift_likelihood": _clamp(1.0 - continuity),
                "explanation": "Adjacent segments share little surface topic vocabulary.",
            }
            abrupt.append(row)
            if len(shared) <= 1:
                unsupported.append({**row, "support_gap": "No clear repeated bridge terms were detected."})
        for term in right_terms:
            previous = seen_terms.get(term, [])
            if previous and index - previous[-1] > 1:
                reentry.append(
                    {
                        "term": term,
                        "reentered_segment_id": right.get("segment_id"),
                        "previous_segment_id": segments[previous[-1]].get("segment_id"),
                    }
                )
        for term in left_terms:
            seen_terms[term].append(index)
    if segments:
        for term in term_sets[-1] if term_sets else set():
            seen_terms[term].append(len(segments) - 1)

    score = _clamp(mean(pair_scores) if pair_scores else (1.0 if segments else 0.0))
    drift_explanation = "Topic continuity is stable across adjacent transcript windows."
    if unsupported:
        drift_explanation = f"{len(unsupported)} unsupported topic shift(s) need human bridge review."
    elif abrupt:
        drift_explanation = f"{len(abrupt)} abrupt topic shift(s) were detected by surface-term continuity."
    return {
        "analysis_status": STATUS_COMPLETE if any(text.strip() for text in texts) else STATUS_LIMITED,
        "method": method,
        "segment_topic_vectors": segment_vectors,
        "rolling_window_topics": windows,
        "topic_bridge_terms": bridge_terms,
        "repeated_concepts": repeated,
        "topic_reentry_points": sorted(reentry, key=lambda row: (row["reentered_segment_id"], row["term"]))[:50],
        "abrupt_topic_shifts": abrupt,
        "unsupported_topic_shifts": unsupported,
        "topic_continuity_score": score,
        "topic_drift_explanation": drift_explanation,
        "source_topic_drift_score": (topic_analysis or {}).get("topic_drift_score"),
        "limitations": limitations
        + [
            "Topic continuity is deterministic surface-language evidence for editorial review.",
            "It is not a semantic truth guarantee and uses no embeddings or cloud models.",
        ],
    }
