# Visual Structure System

## Longitudinal Visual Evidence

Longitudinal analysis tracks visual evidence evolution through visual continuity, visual boundary alignment, contradiction pressure, and anomaly clusters for unstable boundaries or unsupported visual jumps. These signals can influence readiness conservatively when recurring visual weakness or contradiction pressure persists across runs.

Visual longitudinal outputs use existing local pixel/color/edge evidence and retained run snapshots only. They do not perform object recognition, embeddings, CLIP, cloud inference, Resolve integration, or media mutation.

Longitudinal and semantic-evolution outputs are deterministic historical-analysis heuristics intended for editorial review and system explainability. They are not semantic truth systems, predictive systems, or autonomous editorial agents.

Phase 13 adds deterministic local visual structure and shot-boundary evidence for editorial review.

Visual structure outputs are deterministic pixel/color/edge-level evidence summaries for editorial review. They are not object recognition, identity detection, emotion recognition, or cinematic intent claims.

## Scope

The system uses optional local OpenCV and NumPy only. It samples video frames at a configurable interval and measures:

- frame histogram difference
- mean absolute pixel difference
- edge difference
- brightness and contrast change
- brightness, contrast, saturation proxy, edge density, complexity, motion proxy, negative-space proxy, and similarity

It does not use cloud APIs, LLMs, embeddings, vector databases, CLIP, face recognition, identity detection, emotion detection from faces, Resolve APIs, databases, servers, Electron, React, Vue, or media mutation.

If OpenCV is unavailable or the video cannot be opened, the system writes placeholder artifacts with explicit `analysis_status`, limitations, validation output, and downstream-compatible shape.

## Artifacts

The pass writes:

- `visual_structure/visual_structure.json`
- `visual_structure/shot_boundaries.json`
- `visual_structure/visual_continuity.json`
- `visual_structure/composition_features.json`
- `visual_structure/visual_boundary_alignment.json`
- `visual_structure/visual_structure_summary.json`
- `reports/visual_structure_report.md`
- `reports/shot_boundary_report.md`
- `reports/visual_continuity_report.md`
- `reports/composition_features_report.md`
- `reports/visual_boundary_alignment_report.md`
- `graphs/shot_boundary_curve.png`
- `graphs/visual_change_intensity.png`
- `graphs/visual_continuity_timeline.png`
- `graphs/composition_complexity_curve.png`
- `graphs/frame_difference_heatmap.png`
- `graphs/visual_boundary_alignment.png`
- `graphs/shot_contact_sheet.png`
- `visualizations/visual_structure.html`
- `visualizations/shot_boundaries.html`
- `visualizations/visual_continuity.html`
- `visualizations/composition_features.html`
- `visualizations/visual_boundary_alignment.html`
- `verification_evidence/visual_structure_validation.json`
- `verification_evidence/shot_boundary_sampling_log.json`

## Shot Boundaries

Shot-boundary candidates are generated when the combined visual change score crosses the configured threshold. The score combines histogram, pixel, edge, brightness, and contrast changes. Each candidate receives a deterministic `SHOT_<short sha256>` ID based on source hash, neighboring sample timestamps, and threshold.

No boundary is treated as cinematic intent. A candidate means only that sampled frames changed sharply according to local pixel/color/edge evidence.

Default sampling modes are conservative and can be adjusted in `config/analysis_profile.default.json` without adding CLI surface:

- `coarse`: 5.0 second samples, 0.52 boundary threshold
- `normal`: 2.0 second samples, 0.46 boundary threshold
- `dense`: 0.75 second samples, 0.42 boundary threshold

The default combined score weights are histogram difference `0.30`, mean absolute pixel difference `0.32`, edge difference `0.18`, and brightness/contrast change `0.20`. Brightness-only changes can cross the default threshold, but generally receive lower confidence than full color/edge scene changes.

## Visual Continuity

Visual continuity summarizes:

- change intensity over time
- stability regions
- abrupt transitions
- sustained similarity
- visual pacing
- reset candidates
- visual continuity score

Reset candidates are review prompts only. They do not rewrite transcript, segment, timeline, or media boundaries.

## Composition Features

Composition features are frame-level and segment-level deterministic proxies:

- brightness
- contrast
- saturation proxy
- edge density
- visual complexity
- motion proxy
- negative-space proxy
- frame similarity to previous sample
- segment visual energy, stillness, and abruptness

These features are not object, person, face, identity, emotion, or intent labels.

## Boundary Alignment

`visual_boundary_alignment.json` compares visual transition evidence against:

- `scene_segments.json`
- `continuity/boundary_diagnostics.json`
- `consensus/transition_confidence.json`
- `discourse/discourse_summary.json`
- `emotional_arc.json`
- local acoustic evidence

For each adjacent segment boundary, the artifact reports visual, transcript, rhetorical, discourse, acoustic, and topic support; visual contradiction; combined confidence; likely visual/nonvisual flags; evidence type; and suggested review action.

The system distinguishes transcript-only boundaries, visual-only boundaries, multimodal boundaries, discourse boundaries without visual reset, visual resets without transcript transition, and unsupported visual jumps.

## Downstream Effects

Visual evidence is additive:

- consensus includes visual support and contradiction when available
- boundary diagnostics include visual shift evidence
- recommendations include visual review actions and limitations
- release readiness includes visual continuity, alignment, completeness, contradiction pressure, and reset support
- revision graph candidates distinguish metadata-only fixes, transcript/discourse suggestions, visual reset suggestions, rerender-required visual interventions, and human-review-only visual issues

Readiness is not inflated automatically. Visual contradiction can lower readiness.

## Safety

The visual pass never mutates videos, rendered media, timelines, boundaries, databases, or server state. All outputs are proposal-only review evidence.
# Integrity Coverage

Visual structure outputs now participate in global reference validation and dashboard coverage checks. Referenced frame images, visual-alignment rows, graph assets, and static HTML pages are validated as local artifacts.
