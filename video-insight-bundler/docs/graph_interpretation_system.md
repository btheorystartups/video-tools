# Graph Interpretation System

Phase V54 adds optional LLM-assisted and deterministic fallback interpretation to graph/page detail pages. The generated HTML visibly separates measured deterministic evidence from advisory interpretation and includes limitation language on every target page.

LLM-assisted text is safety-scanned and provenance-captured. Unsafe output falls back to deterministic interpretation and cannot alter graph values, recommendations, governance, blockers, media, timelines, or readiness.

Phase V51-53 separates static graph meaning from observed deterministic interpretation.

- Static meaning explains what each graph measures, how to read it, good/caution/concern patterns, common false positives, and what not to infer.
- Observed interpretation summarizes available artifacts without runtime LLM calls.
- Detail pages link graph evidence, recommendations, optimization guidance, and limitations.

Phase V51-53B makes this separation visible in the generated dashboards. The graph card is a navigation surface; the detail page is the explanatory surface. Static meaning is persistent text describing graph semantics. Observed interpretation is deterministic text derived from available generated values, file presence, and local artifacts. External interpretation packets are offline/human-authored companion artifacts and remain separate from these local pages.

The four required core detail pages are:

- `visualizations/graph_ux/detail/emotional_arc_detail.html`
- `visualizations/graph_ux/detail/pacing_curve_detail.html`
- `visualizations/graph_ux/detail/acoustic_energy_detail.html`
- `visualizations/graph_ux/detail/topic_timeline_detail.html`

Each page includes limitation language. Emotional Arc is an editorial tone proxy, not true emotion recognition. Acoustic Energy is RMS-style audio evidence, not emotion diagnosis. Topic Timeline is deterministic transcript-term extraction and may miss nuance. Pacing values can reflect intentional delivery, pauses, segmentation, or dense argumentation and require human review.

All graph interpretation is deterministic editorial-review support. Human review remains required.
