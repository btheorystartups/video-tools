# Timeline Review System

Phase 33 adds a static timeline review environment that links corpus overview, video timelines, segment context, metric spikes, recommendation pins, evidence, and optimization guidance.

The system writes timeline artifacts under `Corpus_analysis/timeline/` and static pages under `Corpus_analysis/visualizations/` and `Corpus_analysis/visualizations/timeline/`.

The temporal review system provides deterministic editorial-review guidance and timeline-linked evidence navigation. It does not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous creative decisions. Human review is required before production or editorial changes.

## Outputs

- `timeline/timeline_review_index.json`
- `timeline/timeline_overlay_registry.json`
- `timeline/timeline_recommendation_pins.json`
- `timeline/timeline_metric_spikes.json`
- `timeline/segment_context_panels.json`
- `visualizations/timeline_review_index.html`
- `visualizations/timeline/corpus_timeline_overview.html`
- `visualizations/timeline/video_timeline_*.html`
- `visualizations/timeline/segment_context_*.html`

## Overlay Types

The overlay registry supports speech pacing, acoustic energy, silence, rhetorical pressure, topic continuity, visual reset, boundary diagnostics, recommendations, blockers, archetypes, and governance overlays. Current overlays are generated only from evidence already present in local analysis artifacts.

## Phase 34 Workstation Polish

Enhanced timeline pages add minimaps, overlay lane controls, severity legends, compact segment cards, inline evidence previews, recommendation drawer links, persistent context panels, quick-jump controls, compare links, optimization links, and governance links. These additions improve reviewer speed without adding new semantic analysis capability or mutating source timelines.
