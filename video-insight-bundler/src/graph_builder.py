"""Static graph generation for local analysis workstations."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from pathlib import Path

from report_generator import MARKERS, keyword_counts, words

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover - optional dependency
    plt = None

try:
    import networkx as nx
except Exception:  # pragma: no cover - optional dependency
    nx = None

try:
    from wordcloud import WordCloud
except Exception:  # pragma: no cover - optional dependency
    WordCloud = None

THEME = {
    "bg": "#f7f7f4",
    "ink": "#242424",
    "grid": "#d8d8d2",
    "blue": "#386b8f",
    "green": "#5d7f62",
    "red": "#9c4f45",
    "gold": "#a7783a",
    "violet": "#6d668c",
}
TONE_COLORS = {
    "analytical": THEME["blue"],
    "instructional": THEME["green"],
    "motivational": THEME["gold"],
    "critical": THEME["red"],
    "reflective": THEME["violet"],
    "neutral": "#777777",
}


def _setup(title: str, xlabel: str = "", ylabel: str = ""):
    fig, ax = plt.subplots(figsize=(11, 5.8), dpi=140)
    fig.patch.set_facecolor(THEME["bg"])
    ax.set_facecolor(THEME["bg"])
    ax.grid(True, color=THEME["grid"], linewidth=0.7, alpha=0.75)
    ax.set_title(title, loc="left", fontsize=14, color=THEME["ink"], pad=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    for spine in ax.spines.values():
        spine.set_color("#c9c8c1")
    return fig, ax


def _placeholder(path: Path, title: str, message: str) -> None:
    if plt:
        fig, ax = _setup(title)
        ax.text(0.5, 0.5, message, ha="center", va="center", wrap=True, fontsize=12)
        ax.set_xticks([])
        ax.set_yticks([])
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
    else:
        try:
            from PIL import Image, ImageDraw
            image = Image.new("RGB", (1200, 640), THEME["bg"])
            draw = ImageDraw.Draw(image)
            draw.text((40, 40), title, fill=THEME["ink"])
            draw.text((40, 90), message[:900], fill=THEME["ink"])
            image.save(path)
        except Exception:
            path.write_text(f"{title}\n{message}\n", encoding="utf-8")


def _centers(rows: list[dict]) -> list[float]:
    return [(float(row.get("start_sec") or 0) + float(row.get("end_sec") or 0)) / 2.0 for row in rows]


def build_graphs(bundle, report_data: dict) -> dict:
    graphs_dir = bundle.output_dir / "graphs"
    graphs_dir.mkdir(exist_ok=True)
    if not plt:
        for name in GRAPH_NAMES:
            _placeholder(graphs_dir / name, name, "matplotlib unavailable; graph placeholder written.")
        return {"status": "limited", "graphs_dir": "graphs/", "reason": "matplotlib unavailable"}

    emotional = bundle.emotional_arc.get("segments") or []
    scene_segments = bundle.scene_segments.get("segments") or []
    rates = bundle.audio_features.get("segment_speech_rate") or []
    pauses = bundle.audio_features.get("pauses") or []
    text = bundle.transcript.get("text", "")
    _emotional_arc(graphs_dir / "emotional_arc.png", emotional)
    _pacing_curve(graphs_dir / "pacing_curve.png", rates)
    _transcript_density(graphs_dir / "transcript_density.png", rates, pauses, bundle.media_metadata.get("duration_sec"))
    _persona_radar(graphs_dir / "persona_radar.png", bundle.persona_profile, bundle.teaching_profile)
    _rhetorical_heatmap(graphs_dir / "rhetorical_heatmap.png", scene_segments)
    _segment_timeline(graphs_dir / "segment_timeline.png", scene_segments, emotional)
    _histogram(graphs_dir / "speaking_rate_distribution.png", [item.get("words_per_minute") for item in rates], "Speaking Rate Distribution", "Words per minute")
    _histogram(graphs_dir / "pause_distribution.png", [item.get("duration_sec") for item in pauses], "Pause Distribution", "Pause seconds")
    _marker_network(graphs_dir / "rhetorical_markers_network.png", text)
    _keyword_clusters(graphs_dir / "keyword_clusters.png", text)
    _wordcloud(graphs_dir / "wordcloud.png", text)
    _acoustic_energy_curve(graphs_dir / "acoustic_energy_curve.png", getattr(bundle, "acoustic_features", None) or {})
    _segment_energy_bars(graphs_dir / "segment_energy_bars.png", getattr(bundle, "acoustic_features", None) or {})
    _silence_ratio(graphs_dir / "silence_ratio.png", getattr(bundle, "acoustic_features", None) or {})
    _acoustic_variability(graphs_dir / "acoustic_variability.png", getattr(bundle, "acoustic_features", None) or {})
    _topic_timeline(graphs_dir / "topic_timeline.png", getattr(bundle, "topic_analysis", None) or {}, scene_segments)
    _topic_shift_heatmap(graphs_dir / "topic_shift_heatmap.png", getattr(bundle, "topic_analysis", None) or {})
    _keyword_importance(graphs_dir / "keyword_importance.png", getattr(bundle, "topic_analysis", None) or {})
    _concept_repetition(graphs_dir / "concept_repetition.png", getattr(bundle, "topic_analysis", None) or {})
    _rhetorical_mode_timeline(graphs_dir / "rhetorical_mode_timeline.png", getattr(bundle, "rhetorical_analysis", None) or {})
    _question_density(graphs_dir / "question_density.png", getattr(bundle, "rhetorical_analysis", None) or {})
    _claim_example_balance(graphs_dir / "claim_example_balance.png", getattr(bundle, "rhetorical_analysis", None) or {})
    _abstract_vs_concrete(graphs_dir / "abstract_vs_concrete.png", getattr(bundle, "rhetorical_analysis", None) or {})
    _audience_address_curve(graphs_dir / "audience_address_curve.png", getattr(bundle, "rhetorical_analysis", None) or {})
    _segment_boundary_confidence(graphs_dir / "segment_boundary_confidence.png", scene_segments)
    _frame_contact_sheet(graphs_dir / "frame_contact_sheet.png", bundle)
    consensus_outputs = getattr(bundle, "consensus_outputs", None) or {}
    _modality_heatmap(graphs_dir / "modality_agreement_heatmap.png", consensus_outputs.get("modality_agreement") or {}, "agreement_score", "Modality Agreement")
    _modality_heatmap(graphs_dir / "modality_disagreement_heatmap.png", consensus_outputs.get("modality_disagreement") or {}, "disagreement_score", "Modality Disagreement")
    _transition_confidence_curve(graphs_dir / "transition_confidence_curve.png", consensus_outputs.get("transition_confidence") or {})
    _evidence_strength_distribution(graphs_dir / "evidence_strength_distribution.png", consensus_outputs.get("evidence_score_summary") or {})
    _continuity_alignment(graphs_dir / "continuity_alignment.png", consensus_outputs.get("continuity_analysis") or {})
    _false_positive_boundaries(graphs_dir / "false_positive_boundaries.png", consensus_outputs.get("false_positive_boundaries") or {})
    _segmentation_confidence(graphs_dir / "segmentation_confidence.png", consensus_outputs.get("transition_confidence") or {}, scene_segments)
    _topic_continuity_curve(graphs_dir / "topic_continuity_curve.png", getattr(bundle, "topic_continuity", None) or {})
    _topic_bridge_map(graphs_dir / "topic_bridge_map.png", getattr(bundle, "topic_continuity", None) or {})
    _rhetorical_coherence_timeline(graphs_dir / "rhetorical_coherence_timeline.png", getattr(bundle, "rhetorical_coherence", None) or {})
    _claim_evidence_balance(graphs_dir / "claim_evidence_balance.png", getattr(bundle, "rhetorical_coherence", None) or {})
    _boundary_diagnostic_matrix(graphs_dir / "boundary_diagnostic_matrix.png", getattr(bundle, "boundary_diagnostics", None) or {})
    _discourse_flow_graph(graphs_dir / "discourse_flow_graph.png", getattr(bundle, "discourse_state", None) or {})
    _argument_chain_graph(graphs_dir / "argument_chain_graph.png", getattr(bundle, "argument_graph", None) or {})
    _callback_resolution_map(graphs_dir / "callback_resolution_map.png", getattr(bundle, "callback_resolution", None) or {})
    _narrative_memory_timeline(graphs_dir / "narrative_memory_timeline.png", getattr(bundle, "narrative_memory", None) or {}, scene_segments)
    _discourse_pressure_curve(graphs_dir / "discourse_pressure_curve.png", getattr(bundle, "discourse_state", None) or {})
    _ambiguity_distribution(graphs_dir / "ambiguity_distribution.png", getattr(bundle, "editorial_ambiguity", None) or {})
    _unresolved_argument_map(graphs_dir / "unresolved_argument_map.png", getattr(bundle, "argument_graph", None) or {})
    return {"status": "complete", "graphs_dir": "graphs/", "files": GRAPH_NAMES}


GRAPH_NAMES = [
    "emotional_arc.png",
    "pacing_curve.png",
    "transcript_density.png",
    "persona_radar.png",
    "rhetorical_heatmap.png",
    "segment_timeline.png",
    "speaking_rate_distribution.png",
    "pause_distribution.png",
    "rhetorical_markers_network.png",
    "keyword_clusters.png",
    "wordcloud.png",
    "acoustic_energy_curve.png",
    "segment_energy_bars.png",
    "silence_ratio.png",
    "acoustic_variability.png",
    "topic_timeline.png",
    "topic_shift_heatmap.png",
    "keyword_importance.png",
    "concept_repetition.png",
    "rhetorical_mode_timeline.png",
    "question_density.png",
    "claim_example_balance.png",
    "abstract_vs_concrete.png",
    "audience_address_curve.png",
    "segment_boundary_confidence.png",
    "frame_contact_sheet.png",
    "revision_score_evolution.png",
    "branch_comparison.png",
    "release_readiness_radar.png",
    "constraint_pressure.png",
    "mutation_safety_matrix.png",
    "editorial_evolution.png",
    "modality_agreement_heatmap.png",
    "modality_disagreement_heatmap.png",
    "transition_confidence_curve.png",
    "evidence_strength_distribution.png",
    "continuity_alignment.png",
    "false_positive_boundaries.png",
    "segmentation_confidence.png",
    "topic_continuity_curve.png",
    "topic_bridge_map.png",
    "rhetorical_coherence_timeline.png",
    "claim_evidence_balance.png",
    "boundary_diagnostic_matrix.png",
    "discourse_flow_graph.png",
    "argument_chain_graph.png",
    "callback_resolution_map.png",
    "narrative_memory_timeline.png",
    "discourse_pressure_curve.png",
    "ambiguity_distribution.png",
    "unresolved_argument_map.png",
    "shot_boundary_curve.png",
    "visual_change_intensity.png",
    "visual_continuity_timeline.png",
    "composition_complexity_curve.png",
    "frame_difference_heatmap.png",
    "visual_boundary_alignment.png",
    "shot_contact_sheet.png",
    "pacing_wave_timeline.png",
    "narrative_phase_map.png",
    "editorial_pressure_curve.png",
    "contradiction_pressure_curve.png",
    "recommendation_dependency_graph.png",
    "revision_propagation_graph.png",
    "revision_conflict_matrix.png",
    "sequence_hierarchy_map.png",
    "structural_transition_map.png",
    "epistemic_stability_curve.png",
    "revision_forecast_heatmap.png",
    "creator_evolution_timeline.png",
    "rhetorical_signature_map.png",
    "pacing_fingerprint_map.png",
    "discourse_signature_map.png",
    "comparative_continuity_matrix.png",
    "recurring_pattern_heatmap.png",
    "creator_stability_curve.png",
    "recommendation_convergence_graph.png",
    "stylistic_similarity_map.png",
    "semantic_equivalence_readiness_map.png",
]


def _emotional_arc(path: Path, rows: list[dict]) -> None:
    if not rows:
        return _placeholder(path, "Emotional Arc", "No emotional arc rows available.")
    x = _centers(rows)
    fig, ax = _setup("Emotional Arc", "Seconds", "Score")
    for row in rows:
        ax.axvspan(row.get("start_sec", 0), row.get("end_sec", 0), color=TONE_COLORS.get(row.get("dominant_tone"), "#777"), alpha=0.09)
    for key, color in [("energy", THEME["gold"]), ("valence", THEME["green"]), ("certainty", THEME["blue"]), ("intensity", THEME["red"])]:
        ax.plot(x, [row.get(key, 0) for row in rows], marker="o", linewidth=2, label=key.title(), color=color)
    for row, center in zip(rows, x):
        ax.text(center, min(1.03, float(row.get("intensity") or 0) + 0.05), row.get("dominant_tone", "neutral")[:11], fontsize=7, rotation=35)
    ax.set_ylim(0, 1.12)
    ax.legend(ncol=4, frameon=False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _pacing_curve(path: Path, rows: list[dict]) -> None:
    if not rows:
        return _placeholder(path, "Pacing Curve", "No transcript-timed speech rate rows available.")
    x = _centers(rows)
    y = [row.get("words_per_minute", 0) for row in rows]
    fig, ax = _setup("Pacing Curve", "Seconds", "Words per minute")
    ax.plot(x, y, marker="o", color=THEME["blue"], linewidth=2)
    ax.axhspan(95, 180, color=THEME["green"], alpha=0.12, label="Typical explanatory range")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _transcript_density(path: Path, rows: list[dict], pauses: list[dict], duration: float | None) -> None:
    if not rows:
        return _placeholder(path, "Transcript Density", "No transcript density rows available.")
    fig, ax = _setup("Transcript Density", "Seconds", "Words per minute")
    ax.bar(_centers(rows), [row.get("words_per_minute", 0) for row in rows], width=[max(row.get("duration_sec", 1), 0.5) for row in rows], color=THEME["blue"], alpha=0.62)
    ymax = max([row.get("words_per_minute", 0) for row in rows] + [1])
    for pause in pauses:
        ax.axvspan(pause.get("start_sec", 0), pause.get("end_sec", 0), color=THEME["red"], alpha=0.18)
    ax.set_xlim(0, max(float(duration or 0), max(row.get("end_sec", 0) for row in rows)))
    ax.set_ylim(0, ymax * 1.18)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _persona_radar(path: Path, persona: dict, teaching: dict) -> None:
    rows = (persona.get("top_categories") or [])[:5] + (teaching.get("top_categories") or [])[:5]
    labels = [row.get("label", row.get("category", "unknown"))[:22] for row in rows]
    values = [float(row.get("weight") or 0) for row in rows]
    if not rows:
        return _placeholder(path, "Persona / Style Radar", "No persona or style scores available.")
    angles = [n / float(len(labels)) * 2 * math.pi for n in range(len(labels))]
    values += values[:1]
    angles += angles[:1]
    fig = plt.figure(figsize=(8, 8), dpi=140)
    fig.patch.set_facecolor(THEME["bg"])
    ax = plt.subplot(111, polar=True)
    ax.set_facecolor(THEME["bg"])
    ax.plot(angles, values, color=THEME["blue"], linewidth=2)
    ax.fill(angles, values, color=THEME["blue"], alpha=0.18)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0, 1)
    ax.set_title("Persona / Style Radar", loc="left", pad=24)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _rhetorical_heatmap(path: Path, segments: list[dict]) -> None:
    labels = list(MARKERS.keys())
    if not segments:
        return _placeholder(path, "Rhetorical Heatmap", "No segments available.")
    matrix = []
    for segment in segments:
        lowered = (segment.get("text") or "").lower()
        matrix.append([sum(lowered.count(marker) for marker in MARKERS[label]) for label in labels])
    fig, ax = _setup("Rhetorical Marker Heatmap", "Marker", "Segment")
    image = ax.imshow(matrix, cmap="YlGnBu", aspect="auto")
    ax.set_xticks(range(len(labels)), labels, rotation=35, ha="right")
    ax.set_yticks(range(len(segments)), [str(i + 1) for i in range(len(segments))])
    fig.colorbar(image, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _segment_timeline(path: Path, segments: list[dict], emotional: list[dict]) -> None:
    if not segments:
        return _placeholder(path, "Segment Timeline", "No scene segments available.")
    tone_by_id = {row.get("segment_id"): row.get("dominant_tone") for row in emotional}
    fig, ax = _setup("Segment Timeline", "Seconds", "")
    for index, segment in enumerate(segments):
        tone = tone_by_id.get(segment.get("segment_id"), "neutral")
        ax.barh(index, segment.get("duration_sec", 0), left=segment.get("start_sec", 0), color=TONE_COLORS.get(tone, "#777"), alpha=0.7)
        label = ", ".join(segment.get("topic_markers") or []) or tone
        ax.text(segment.get("start_sec", 0) + 0.5, index, label[:42], va="center", fontsize=8, color="#111")
    ax.set_yticks(range(len(segments)), [str(i + 1) for i in range(len(segments))])
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _histogram(path: Path, values: list, title: str, xlabel: str) -> None:
    clean = [float(value) for value in values if value is not None]
    if not clean:
        return _placeholder(path, title, "No distribution values available.")
    fig, ax = _setup(title, xlabel, "Count")
    ax.hist(clean, bins=min(12, max(4, len(clean) // 2)), color=THEME["blue"], edgecolor="#ffffff", alpha=0.78)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _marker_network(path: Path, text: str) -> None:
    tokens = words(text)
    hits = [token for token in tokens if any(token in marker.split() for marker_group in MARKERS.values() for marker in marker_group)]
    if not hits:
        return _placeholder(path, "Rhetorical Markers Network", "No marker terms found.")
    pairs = Counter(zip(hits, hits[1:]))
    fig, ax = _setup("Rhetorical Markers Network")
    if nx:
        graph = nx.Graph()
        for (left, right), weight in pairs.items():
            if left != right:
                graph.add_edge(left, right, weight=weight)
        pos = nx.spring_layout(graph, seed=7)
        nx.draw_networkx_nodes(graph, pos, ax=ax, node_color=THEME["blue"], node_size=900, alpha=0.75)
        nx.draw_networkx_edges(graph, pos, ax=ax, edge_color="#777", width=[max(1, graph[u][v]["weight"]) for u, v in graph.edges()])
        nx.draw_networkx_labels(graph, pos, ax=ax, font_size=8)
        ax.axis("off")
    else:
        ax.bar([f"{a}->{b}" for (a, b), _ in pairs.most_common(12)], [v for _, v in pairs.most_common(12)], color=THEME["blue"])
        ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _keyword_clusters(path: Path, text: str) -> None:
    top = keyword_counts(text, 24)
    if not top:
        return _placeholder(path, "Keyword Clusters", "No keywords available.")
    fig, ax = _setup("Keyword Clusters", "Heuristic cluster", "Frequency")
    groups = defaultdict(list)
    for item in top:
        groups[item["term"][0]].append(item)
    labels = []
    values = []
    for key in sorted(groups):
        labels.append(key.upper())
        values.append(sum(item["count"] for item in groups[key]))
    ax.bar(labels, values, color=THEME["green"], alpha=0.75)
    for item in top[:12]:
        ax.text(labels.index(item["term"][0].upper()), item["count"], item["term"], fontsize=8, rotation=35)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _wordcloud(path: Path, text: str) -> None:
    if not text.strip():
        return _placeholder(path, "Word Cloud", "No transcript text available.")
    if WordCloud:
        cloud = WordCloud(width=1400, height=700, background_color="#f7f7f4", colormap="cividis", random_state=7, collocations=False).generate(text)
        fig, ax = plt.subplots(figsize=(11, 5.8), dpi=140)
        fig.patch.set_facecolor(THEME["bg"])
        ax.imshow(cloud, interpolation="bilinear")
        ax.axis("off")
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
    else:
        top = keyword_counts(text, 20)
        fig, ax = _setup("Word Cloud Fallback", "Count", "Term")
        ax.barh([item["term"] for item in reversed(top)], [item["count"] for item in reversed(top)], color=THEME["blue"])
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)


def _acoustic_energy_curve(path: Path, acoustic: dict) -> None:
    rows = acoustic.get("rms_energy_over_time") or []
    if not rows:
        return _placeholder(path, "Acoustic Energy Curve", acoustic.get("reason") or "No acoustic energy data available.")
    step = max(1, len(rows) // 900)
    sampled = rows[::step]
    fig, ax = _setup("Acoustic Energy Curve", "Seconds", "RMS energy")
    ax.plot([row["time_sec"] for row in sampled], [row["rms"] for row in sampled], color=THEME["blue"], linewidth=1.4)
    ax.set_ylim(bottom=0)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _segment_energy_bars(path: Path, acoustic: dict) -> None:
    rows = acoustic.get("segments") or []
    values = [row.get("average_energy") for row in rows if row.get("average_energy") is not None]
    if not values:
        return _placeholder(path, "Segment Energy Bars", acoustic.get("reason") or "No segment acoustic energy data available.")
    labels = [str(index + 1) for index in range(len(rows))]
    fig, ax = _setup("Segment Energy Bars", "Segment", "Average RMS")
    ax.bar(labels, [row.get("average_energy") or 0 for row in rows], color=THEME["green"], alpha=0.78)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _silence_ratio(path: Path, acoustic: dict) -> None:
    ratio = acoustic.get("silence_ratio")
    if ratio is None:
        return _placeholder(path, "Silence Ratio", acoustic.get("reason") or "No silence ratio available.")
    fig, ax = _setup("Silence Ratio")
    ax.pie([ratio, max(0, 1 - float(ratio))], labels=["low-energy", "voiced/active"], colors=[THEME["red"], THEME["blue"]], autopct="%1.1f%%")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _acoustic_variability(path: Path, acoustic: dict) -> None:
    rows = acoustic.get("segments") or []
    values = [row.get("energy_variability") for row in rows if row.get("energy_variability") is not None]
    if not values:
        return _placeholder(path, "Acoustic Variability", acoustic.get("reason") or "No acoustic variability data available.")
    fig, ax = _setup("Acoustic Variability", "Segment", "RMS stddev")
    ax.plot(range(1, len(values) + 1), values, marker="o", color=THEME["gold"], linewidth=2)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _topic_timeline(path: Path, topic: dict, segments: list[dict]) -> None:
    rows = topic.get("per_segment_keywords") or []
    if not rows:
        return _placeholder(path, "Topic Timeline", "No topic rows available.")
    fig, ax = _setup("Topic Timeline", "Seconds", "Segment")
    by_id = {segment.get("segment_id"): segment for segment in segments}
    for index, row in enumerate(rows):
        segment = by_id.get(row.get("segment_id"), {})
        start = float(segment.get("start_sec") or row.get("start_sec") or 0)
        end = float(segment.get("end_sec") or row.get("end_sec") or start)
        ax.barh(index, max(end - start, 0.001), left=start, color=THEME["violet"], alpha=0.64)
        ax.text(start + 0.3, index, (row.get("topic_label") or "")[:38], va="center", fontsize=8)
    ax.set_yticks(range(len(rows)), [str(i + 1) for i in range(len(rows))])
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _topic_shift_heatmap(path: Path, topic: dict) -> None:
    rows = topic.get("segment_to_segment_topic_continuity") or []
    if not rows:
        return _placeholder(path, "Topic Shift Heatmap", "No adjacent topic continuity data available.")
    matrix = [[row.get("shift_likelihood") or 0] for row in rows]
    fig, ax = _setup("Topic Shift Heatmap", "Shift likelihood", "Boundary")
    image = ax.imshow(matrix, cmap="YlOrRd", aspect="auto", vmin=0, vmax=1)
    ax.set_xticks([0], ["shift"])
    ax.set_yticks(range(len(rows)), [str(i + 1) for i in range(len(rows))])
    fig.colorbar(image, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _keyword_importance(path: Path, topic: dict) -> None:
    rows = topic.get("tfidf_weighted_terms") or topic.get("top_global_keywords") or []
    rows = rows[:18]
    if not rows:
        return _placeholder(path, "Keyword Importance", "No keyword importance data available.")
    labels = [row.get("term") for row in reversed(rows)]
    values = [row.get("weight", row.get("count", 0)) for row in reversed(rows)]
    fig, ax = _setup("Keyword Importance", "Weight / count", "")
    ax.barh(labels, values, color=THEME["blue"], alpha=0.78)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _concept_repetition(path: Path, topic: dict) -> None:
    rows = (topic.get("repeated_concepts") or [])[:18]
    if not rows:
        return _placeholder(path, "Concept Repetition", "No repeated concepts available.")
    fig, ax = _setup("Concept Repetition", "Count", "")
    ax.barh([row["term"] for row in reversed(rows)], [row["count"] for row in reversed(rows)], color=THEME["green"], alpha=0.78)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _rhetorical_mode_timeline(path: Path, rhetoric: dict) -> None:
    rows = rhetoric.get("segments") or []
    if not rows:
        return _placeholder(path, "Rhetorical Mode Timeline", "No rhetorical segment data available.")
    modes = {mode: index for index, mode in enumerate(sorted({row.get("rhetorical_mode", "unknown") for row in rows}))}
    fig, ax = _setup("Rhetorical Mode Timeline", "Seconds", "Mode")
    for row in rows:
        mode = row.get("rhetorical_mode", "unknown")
        start = float(row.get("start_sec") or 0)
        end = float(row.get("end_sec") or start)
        ax.barh(modes[mode], max(end - start, 0.001), left=start, color=THEME["gold"], alpha=0.74)
    ax.set_yticks(list(modes.values()), list(modes.keys()))
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _question_density(path: Path, rhetoric: dict) -> None:
    rows = rhetoric.get("segments") or []
    values = [row.get("question_density") for row in rows if row.get("question_density") is not None]
    if not values:
        return _placeholder(path, "Question Density", "No question density data available.")
    fig, ax = _setup("Question Density", "Segment", "Questions per 100 words")
    ax.plot(range(1, len(values) + 1), values, marker="o", color=THEME["blue"], linewidth=2)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _claim_example_balance(path: Path, rhetoric: dict) -> None:
    rows = rhetoric.get("segments") or []
    if not rows:
        return _placeholder(path, "Claim / Example Balance", "No rhetorical data available.")
    fig, ax = _setup("Claim / Example Balance", "Segment", "Density per 100 words")
    ax.plot(range(1, len(rows) + 1), [row.get("claim_density") or 0 for row in rows], marker="o", label="claim", color=THEME["red"])
    ax.plot(range(1, len(rows) + 1), [row.get("example_density") or 0 for row in rows], marker="o", label="example", color=THEME["green"])
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _abstract_vs_concrete(path: Path, rhetoric: dict) -> None:
    rows = rhetoric.get("segments") or []
    if not rows:
        return _placeholder(path, "Abstract vs Concrete", "No rhetorical data available.")
    fig, ax = _setup("Abstract vs Concrete", "Segment", "Marker count")
    x = range(1, len(rows) + 1)
    ax.bar([value - 0.18 for value in x], [row.get("philosophical_abstract_markers") or 0 for row in rows], width=0.36, label="abstract", color=THEME["violet"])
    ax.bar([value + 0.18 for value in x], [row.get("concrete_actionable_markers") or 0 for row in rows], width=0.36, label="concrete", color=THEME["green"])
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _audience_address_curve(path: Path, rhetoric: dict) -> None:
    rows = rhetoric.get("segments") or []
    values = [row.get("audience_address_markers") for row in rows]
    if not rows:
        return _placeholder(path, "Audience Address Curve", "No audience-address data available.")
    fig, ax = _setup("Audience Address Curve", "Segment", "Marker count")
    ax.plot(range(1, len(values) + 1), values, marker="o", color=THEME["blue"], linewidth=2)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _segment_boundary_confidence(path: Path, segments: list[dict]) -> None:
    if not segments:
        return _placeholder(path, "Segment Boundary Confidence", "No segments available.")
    values = [segment.get("boundary_confidence", 0) for segment in segments]
    fig, ax = _setup("Segment Boundary Confidence", "Segment", "Confidence")
    colors = [THEME["red"] if value < 0.6 else THEME["green"] for value in values]
    ax.bar(range(1, len(values) + 1), values, color=colors, alpha=0.78)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _frame_contact_sheet(path: Path, bundle) -> None:
    samples = (bundle.visual_index.get("samples") or [])[:24]
    if not samples:
        return _placeholder(path, "Frame Contact Sheet", "No sampled frames available.")
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return _placeholder(path, "Frame Contact Sheet", "Pillow unavailable; contact sheet could not be generated.")
    thumbs = []
    for sample in samples:
        frame_path = Path(sample.get("image_path", ""))
        if not frame_path.is_absolute():
            frame_path = bundle.output_dir / frame_path
        if not frame_path.exists():
            continue
        try:
            image = Image.open(frame_path).convert("RGB")
            image.thumbnail((220, 124))
            thumbs.append((sample, image.copy()))
        except Exception:
            continue
    if not thumbs:
        return _placeholder(path, "Frame Contact Sheet", "No readable sampled frame files were available.")
    cols = 4
    cell_w, cell_h = 240, 170
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "#f7f7f4")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except Exception:
        font = ImageFont.load_default()
    for index, (sample, image) in enumerate(thumbs):
        col = index % cols
        row = index // cols
        x = col * cell_w + 10
        y = row * cell_h + 10
        sheet.paste(image, (x, y))
        label = f"{sample.get('sample_id', index)} | {sample.get('timestamp')}s"
        draw.text((x, y + 130), label[:34], fill="#242424", font=font)
        draw.text((x, y + 146), str(sample.get("reason", "sample"))[:34], fill="#666a6d", font=font)
    sheet.save(path)


def _modality_heatmap(path: Path, data: dict, value_key: str, title: str) -> None:
    rows = data.get("modality_pairs") or []
    if not rows:
        return _placeholder(path, title, "No modality pair rows available.")
    labels = [row.get("modality_pair", "") for row in rows]
    matrix = [[row.get(value_key) or 0.0] for row in rows]
    fig, ax = _setup(title, "Score", "Modality pair")
    image = ax.imshow(matrix, cmap="YlGnBu" if value_key == "agreement_score" else "YlOrRd", aspect="auto", vmin=0, vmax=1)
    ax.set_xticks([0], [value_key.replace("_", " ")])
    ax.set_yticks(range(len(labels)), labels)
    fig.colorbar(image, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _transition_confidence_curve(path: Path, data: dict) -> None:
    rows = data.get("transitions") or []
    if not rows:
        return _placeholder(path, "Transition Confidence Curve", "No transition confidence rows available.")
    fig, ax = _setup("Transition Confidence Curve", "Transition", "Confidence")
    x = range(1, len(rows) + 1)
    ax.plot(x, [row.get("confidence_score") or 0.0 for row in rows], marker="o", color=THEME["blue"], linewidth=2)
    for index, row in enumerate(rows, start=1):
        if row.get("likely_false_positive"):
            ax.scatter([index], [row.get("confidence_score") or 0.0], color=THEME["red"], s=80, zorder=4)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _evidence_strength_distribution(path: Path, data: dict) -> None:
    scores = data.get("modality_scores") or {}
    if not scores:
        return _placeholder(path, "Evidence Strength Distribution", "No evidence score summary available.")
    labels = list(scores)
    values = [scores[key].get("score") or 0.0 for key in labels]
    fig, ax = _setup("Evidence Strength Distribution", "Modality", "Strength")
    ax.bar(labels, values, color=THEME["green"], alpha=0.78)
    ax.tick_params(axis="x", rotation=35)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _continuity_alignment(path: Path, data: dict) -> None:
    rows = data.get("continuity_rows") or []
    if not rows:
        return _placeholder(path, "Continuity Alignment", "No continuity rows available.")
    fig, ax = _setup("Continuity Alignment", "Transition", "Continuity")
    x = range(1, len(rows) + 1)
    for key, color in [
        ("topic_continuity", THEME["blue"]),
        ("rhetorical_continuity", THEME["green"]),
        ("emotional_continuity", THEME["gold"]),
        ("pacing_continuity", THEME["red"]),
        ("acoustic_continuity", THEME["violet"]),
    ]:
        ax.plot(x, [row.get(key) or 0.0 for row in rows], marker="o", linewidth=1.6, label=key.replace("_", " "), color=color)
    ax.set_ylim(0, 1)
    ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _false_positive_boundaries(path: Path, data: dict) -> None:
    rows = data.get("boundaries") or []
    if not rows:
        return _placeholder(path, "False-Positive Boundaries", "No false-positive boundary rows available.")
    values = [row.get("false_positive_probability") or 0.0 for row in rows]
    colors = [THEME["red"] if row.get("likely_false_boundary") else THEME["green"] for row in rows]
    fig, ax = _setup("False-Positive Boundaries", "Transition", "Probability")
    ax.bar(range(1, len(values) + 1), values, color=colors, alpha=0.78)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _segmentation_confidence(path: Path, transition_data: dict, segments: list[dict]) -> None:
    rows = transition_data.get("transitions") or []
    if not rows and not segments:
        return _placeholder(path, "Segmentation Confidence", "No segmentation confidence rows available.")
    fig, ax = _setup("Segmentation Confidence", "Boundary / segment", "Confidence")
    if rows:
        ax.plot(range(1, len(rows) + 1), [row.get("confidence_score") or 0.0 for row in rows], marker="o", color=THEME["blue"], label="transition")
    if segments:
        ax.plot(range(1, len(segments) + 1), [segment.get("boundary_confidence") or 0.0 for segment in segments], marker="s", color=THEME["gold"], label="original boundary")
    ax.set_ylim(0, 1)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _topic_continuity_curve(path: Path, data: dict) -> None:
    rows = data.get("topic_bridge_terms") or []
    if not rows:
        return _placeholder(path, "Topic Continuity Curve", "No topic continuity rows available.")
    fig, ax = _setup("Topic Continuity Curve", "Boundary", "Continuity")
    ax.plot(range(1, len(rows) + 1), [row.get("continuity_score") or 0 for row in rows], marker="o", color=THEME["blue"], linewidth=2)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _topic_bridge_map(path: Path, data: dict) -> None:
    rows = data.get("topic_bridge_terms") or []
    if not rows:
        return _placeholder(path, "Topic Bridge Map", "No bridge terms available.")
    labels = [f"{row.get('from_segment_id')}->{row.get('to_segment_id')}" for row in rows]
    values = [row.get("bridge_strength") or 0 for row in rows]
    fig, ax = _setup("Topic Bridge Map", "Boundary", "Bridge strength")
    ax.bar(labels, values, color=THEME["green"], alpha=0.78)
    ax.tick_params(axis="x", rotation=45)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _rhetorical_coherence_timeline(path: Path, data: dict) -> None:
    rows = data.get("segment_modes") or []
    if not rows:
        return _placeholder(path, "Rhetorical Coherence Timeline", "No rhetorical coherence rows available.")
    fig, ax = _setup("Rhetorical Coherence Timeline", "Segment", "Support")
    ax.plot(range(1, len(rows) + 1), [row.get("support_score") or 0 for row in rows], marker="o", color=THEME["gold"], linewidth=2)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _claim_evidence_balance(path: Path, data: dict) -> None:
    rows = data.get("segment_modes") or []
    if not rows:
        return _placeholder(path, "Claim Evidence Balance", "No rhetorical coherence rows available.")
    x = range(1, len(rows) + 1)
    fig, ax = _setup("Claim Evidence Balance", "Segment", "Present")
    ax.bar([value - 0.2 for value in x], [1 if row.get("has_claim") else 0 for row in rows], width=0.2, label="claim", color=THEME["red"])
    ax.bar(x, [1 if row.get("has_example") else 0 for row in rows], width=0.2, label="example", color=THEME["green"])
    ax.bar([value + 0.2 for value in x], [1 if row.get("has_takeaway") else 0 for row in rows], width=0.2, label="takeaway", color=THEME["blue"])
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _boundary_diagnostic_matrix(path: Path, data: dict) -> None:
    rows = data.get("boundaries") or []
    if not rows:
        return _placeholder(path, "Boundary Diagnostic Matrix", "No boundary diagnostic rows available.")
    keys = ["transcript_pause_evidence", "sentence_completion_evidence", "topic_shift_evidence", "rhetorical_shift_evidence", "acoustic_shift_evidence", "pacing_shift_evidence", "emotional_shift_evidence"]
    matrix = [[(row.get(key) or {}).get("score") or 0 for key in keys] for row in rows]
    fig, ax = _setup("Boundary Diagnostic Matrix", "Evidence", "Boundary")
    image = ax.imshow(matrix, cmap="YlGnBu", aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(len(keys)), [key.replace("_evidence", "").replace("_", " ") for key in keys], rotation=35, ha="right")
    ax.set_yticks(range(len(rows)), [str(i + 1) for i in range(len(rows))])
    fig.colorbar(image, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _discourse_flow_graph(path: Path, data: dict) -> None:
    rows = data.get("discourse_transitions") or []
    if not rows:
        return _placeholder(path, "Discourse Flow Graph", "No discourse transitions available.")
    fig, ax = _setup("Discourse Flow Graph", "Transition", "Continuation / pressure")
    x = range(1, len(rows) + 1)
    ax.plot(x, [row.get("discourse_continuation_evidence") or 0 for row in rows], marker="o", color=THEME["blue"], label="continuation")
    ax.plot(x, [row.get("unresolved_pressure_carryover") or 0 for row in rows], marker="s", color=THEME["red"], label="pressure")
    ax.set_ylim(0, 1)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _argument_chain_graph(path: Path, data: dict) -> None:
    nodes = data.get("nodes") or []
    edges = data.get("edges") or []
    if not nodes:
        return _placeholder(path, "Argument Chain Graph", "No argument nodes available.")
    fig, ax = _setup("Argument Chain Graph")
    if nx and edges:
        graph = nx.DiGraph()
        for node in nodes:
            graph.add_node(node.get("node_id"), label=node.get("segment_id"), node_type=node.get("node_type"))
        for edge in edges:
            graph.add_edge(edge.get("from_node_id"), edge.get("to_node_id"), edge_type=edge.get("edge_type"), weight=edge.get("edge_strength") or 0.2)
        pos = nx.spring_layout(graph, seed=11)
        colors = [THEME["green"] if graph.nodes[node].get("node_type") in {"example", "takeaway"} else THEME["red"] if graph.nodes[node].get("node_type") in {"contrast", "counterpoint", "unresolved_claim"} else THEME["blue"] for node in graph.nodes]
        nx.draw_networkx_nodes(graph, pos, ax=ax, node_color=colors, node_size=900, alpha=0.78)
        nx.draw_networkx_edges(graph, pos, ax=ax, arrows=True, edge_color="#777777")
        nx.draw_networkx_labels(graph, pos, ax=ax, labels={node.get("node_id"): str(node.get("segment_id"))[-6:] for node in nodes}, font_size=7)
        ax.axis("off")
    else:
        ax.bar([node.get("segment_id") for node in nodes], [1 if node.get("support_state") == "supported" else 0.45 for node in nodes], color=THEME["blue"])
        ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _callback_resolution_map(path: Path, data: dict) -> None:
    rows = data.get("callback_pairs") or []
    if not rows:
        return _placeholder(path, "Callback Resolution Map", "No callback pairs available.")
    fig, ax = _setup("Callback Resolution Map", "Callback", "Latency / quality")
    x = range(1, len(rows) + 1)
    ax.bar([value - 0.18 for value in x], [row.get("latency_segments") or 0 for row in rows], width=0.36, color=THEME["gold"], label="latency")
    ax.plot(x, [row.get("payoff_quality") or 0 for row in rows], marker="o", color=THEME["green"], label="payoff quality")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _narrative_memory_timeline(path: Path, data: dict, segments: list[dict]) -> None:
    themes = data.get("persistent_themes") or []
    if not themes:
        return _placeholder(path, "Narrative Memory Timeline", "No persistent themes available.")
    id_to_index = {segment.get("segment_id"): index for index, segment in enumerate(segments)}
    fig, ax = _setup("Narrative Memory Timeline", "Segment", "Theme")
    for row_index, theme in enumerate(themes[:18]):
        indexes = [id_to_index[sid] for sid in theme.get("segment_ids", []) if sid in id_to_index]
        if indexes:
            ax.scatter(indexes, [row_index] * len(indexes), color=THEME["violet"], s=45)
            ax.plot(indexes, [row_index] * len(indexes), color=THEME["violet"], alpha=0.35)
    ax.set_yticks(range(min(len(themes), 18)), [row.get("term") for row in themes[:18]])
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _discourse_pressure_curve(path: Path, data: dict) -> None:
    rows = data.get("segment_discourse_states") or []
    if not rows:
        return _placeholder(path, "Discourse Pressure Curve", "No segment discourse state rows available.")
    fig, ax = _setup("Discourse Pressure Curve", "Segment", "Score")
    x = range(1, len(rows) + 1)
    ax.plot(x, [row.get("discourse_pressure_score") or 0 for row in rows], marker="o", color=THEME["red"], label="pressure")
    ax.plot(x, [row.get("discourse_continuity_score") or 0 for row in rows], marker="s", color=THEME["blue"], label="continuity")
    ax.set_ylim(0, 1)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _ambiguity_distribution(path: Path, data: dict) -> None:
    counts = data.get("ambiguity_class_counts") or {}
    if not counts:
        return _placeholder(path, "Ambiguity Distribution", "No ambiguity regions available.")
    fig, ax = _setup("Ambiguity Distribution", "Class", "Count")
    ax.bar(list(counts), list(counts.values()), color=THEME["gold"], alpha=0.78)
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _unresolved_argument_map(path: Path, data: dict) -> None:
    rows = data.get("unresolved_chains") or []
    if not rows:
        return _placeholder(path, "Unresolved Argument Map", "No unresolved chains available.")
    labels = [row.get("chain_id", "")[-8:] for row in rows]
    values = [1.0 - float(row.get("chain_strength") or 0.0) for row in rows]
    fig, ax = _setup("Unresolved Argument Map", "Chain", "Unresolved pressure")
    ax.bar(labels, values, color=THEME["red"], alpha=0.76)
    ax.tick_params(axis="x", rotation=45)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
