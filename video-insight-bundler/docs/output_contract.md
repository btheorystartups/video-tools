# Output Contract

## Phase V55 Portable Package Outputs

`--portable-export` writes a static offline review deliverable at `Corpus_analysis/portable_review_package/`. Required files include `index.html`, `PACKAGE_SUMMARY.md`, `portable_package_manifest.json`, `portable_package_validation_report.json`, `package_diff_report.json`, `package_size_report.json`, `exclusion_manifest.json`, `manifests/asset_dependency_report.json`, `validation/portable_package_validation_report.json`, `validation/portable_integrity_report.json`, `validation/offline_dashboard_hardening_report.json`, and `validation/portable_privacy_scan_report.json`.

`--zip-export` writes `Corpus_analysis/portable_review_package.zip`.

The portable package includes dashboards, pages, graphs, images, boards, storyboards, inspection assets, JSON artifacts, Markdown reports, manifests, schemas, workflows, timelines, evidence, recommendations, governance artifacts, review sheets/templates, interpretations, validation evidence, provenance records, snapshots, diffs, replay artifacts, and local assets required for display.

Raw video/audio is excluded by default and documented in `exclusion_manifest.json`. Source-video live links are replaced by a placeholder page. If `--portable-include-raw-media` is explicitly provided, media is copied under `media/` and reported in the manifest and summary.

No absolute path is allowed as a live link. Historical absolute paths are allowed only as provenance metadata and do not satisfy display/navigation references.

## Phase V54 Interpretation Outputs

Corpus runs write optional/advisory interpretation artifacts under `llm_interpretation/`, dashboards under `visualizations/llm_interpretation/`, validation evidence under `verification_evidence/`, reports under `reports/`, and schemas under `schemas/`.

Required V54 artifacts include page, graph, prompt, response, provenance, validation, safety, deterministic fallback, page-enrichment audit, page-family, evidence-link, and recommendation-link registries. Actual HTML validation records every target page, visible required sections, forbidden-claim scan status, link validity, fingerprint limitation language, multi-video limitation language, and governance non-auto-resolution language.

Interpretation text is advisory only. It does not mutate media, timelines, recommendations, governance status, blockers, or readiness, and it does not infer identity, recognize faces, diagnose emotion, or predict viewer behavior with certainty.

The tool creates one directory per source video under the configured output root.
The directory name is `<safe source video stem>_analysis`, where characters that are invalid in common filesystems are replaced with `_`.

## Required Artifacts

- `manifest.json`: artifact paths, generation time, and subsystem statuses.
- `dependency_report.json`: local dependency availability, versions, paths, and capabilities.
- `validation_report.json`: schema validation status and errors for `llm_context_bundle.json`.
- `transcript.json`: transcript status, text, and timestamped segments when available.
- `transcript.srt`: SRT subtitles or a one-line unavailable marker.
- `audio_features.json`: word count, speech rate, pause list, and limitations.
- `acoustic_features.json`: local audio RMS energy, silence ratio, spectral summaries, segment energy, trend, and limitations when local audio and `librosa` are available; otherwise an explicit unavailable placeholder.
- `topic_analysis.json`: deterministic local transcript topic/concept analysis using TF-IDF when `scikit-learn` is available or frequency fallback when it is not.
- `rhetorical_analysis.json`: marker-based rhetorical densities, modes, transitions, balance score, and evidence snippets.
- `continuity/topic_continuity.json`: rolling transcript-window topic vectors, bridge terms, repeated concepts, re-entry points, abrupt shifts, unsupported shifts, continuity score, and limitations.
- `continuity/rhetorical_coherence.json`: segment modes, mode transitions, unresolved questions, claim/example balance, setup/payoff links, rhetorical coherence score, gap explanations, and limitations.
- `continuity/boundary_diagnostics.json`: per-boundary transcript pause, sentence completion, topic, rhetorical, acoustic, pacing, emotional, consensus, contradiction, and review-action evidence.
- `continuity/continuity_summary.json`: compact topic, rhetorical, boundary, and penalty summary.
- `discourse/discourse_state.json`: segment entering/exiting discourse state, persistent concepts, expirations, unresolved discourse items, transitions, pressure score, and continuity score.
- `discourse/argument_graph.json`: deterministic claim/support/example/contrast/takeaway nodes, edges, argument chains, unresolved chains, fragmented chains, recovered chains, contradiction clusters, completeness, and fragmentation scores.
- `discourse/narrative_memory.json`: short/medium/long memory windows, persistent themes, callback references, delayed resolutions, resurfacing concepts, narrative drift, persistence, and recovery scores.
- `discourse/callback_resolution.json`: setup/payoff pairs, latency, resolution confidence, unresolved setups, weak callback evidence, callback strength, and payoff quality.
- `discourse/editorial_ambiguity.json`: ambiguity regions, classes, supporting/conflicting evidence, continuity reinterpretation, and recommendation impact.
- `discourse/discourse_summary.json`: decomposed continuity scores, strongest/weakest dimensions, contradiction-adjusted continuity, ambiguity-adjusted continuity, and narrative recovery.
- `visual_structure/visual_structure.json`: compact visual structure summary, evidence completeness, continuity score, alignment quality, contradiction pressure, reset support, and limitations.
- `visual_structure/shot_boundaries.json`: deterministic local shot-boundary candidates from frame histogram, pixel, edge, brightness, and contrast changes.
- `visual_structure/visual_continuity.json`: visual change intensity, stability regions, abrupt transitions, sustained similarity, visual pacing, reset candidates, and continuity score.
- `visual_structure/composition_features.json`: frame and segment brightness, contrast, saturation proxy, edge density, complexity, motion proxy, negative-space proxy, and stillness/abruptness summaries.
- `visual_structure/visual_boundary_alignment.json`: segment-boundary comparison of visual, transcript, rhetorical, discourse, acoustic, and topic support without rewriting boundaries.
- `visual_structure/visual_structure_summary.json`: compact visual evidence rollup for readiness, recommendations, and review.
- `visual_sample_index.json`: sampled frame paths with timestamps and sampling reasons.
- `scene_segments.json`: transcript-derived or time-window segments.
- `emotional_arc.json`: per-segment heuristic scores and evidence.
- `persona_style_profile.json`: weighted communication persona observations.
- `teaching_style_profile.json`: weighted teaching/communication style observations.
- `recommendations.md`: human-readable improvement suggestions.
- `recommendations.json`: evidence-ranked editorial guidance with issue type, severity, confidence, affected segments, evidence, suggested edit, and supporting metrics.
- `llm_context_bundle.md`: pasteable LLM context.
- `llm_context_bundle.json`: structured LLM context.
- `analysis_index.json`: machine-readable map of generated artifacts, statuses, warnings, key metrics, and recommended review files.
- `analysis_index.md`: human-readable artifact map.
- `consensus/`: deterministic multimodal evidence consensus, modality agreement/disagreement, transition confidence, evidence scoring, false-positive boundary flags, and continuity analysis.
- `continuity/`: deterministic topic continuity, rhetorical coherence, and boundary diagnostics.
- `discourse/`: deterministic discourse state, argument graph, narrative memory, callback resolution, ambiguity interpretation, and continuity decomposition.
- `visual_structure/`: deterministic pixel/color/edge-level visual structure evidence.
- `revision_graph/`: deterministic revision states, proposal-only candidates, lineage, deltas, constraints, release readiness, mutation safety, branch comparison, and revision recommendations.
- `charts/`: CSV chart data.
- `visualizations/`: portable static HTML workstation pages.
- `graphs/`: PNG visualizations for emotional arc, pacing, acoustic energy, topics, rhetorical modes, segment quality, frame contact sheet, persona, keywords, and distributions.
- `interactive/`: optional self-contained Plotly HTML charts when `plotly` is available.
- `reports/`: quality report and subsystem statistics JSON.
- `static_assets/`: local CSS and JavaScript used by the HTML reports.
- `frames/`: sampled images.
- `verification_evidence/`: raw diagnostics and reproducibility evidence.

## Longitudinal Outputs

- `longitudinal/longitudinal_analysis.json`: run lineage, evolution windows, stable/unstable metrics, recurring issues, persistent strengths, confidence, and limitations.
- `longitudinal/trend_analysis.json`: readiness, continuity, contradiction, discourse, graph, integrity, and recommendation trends classified as improving, stable, degrading, volatile, or inconclusive.
- `longitudinal/confidence_volatility.json`: unstable metrics, volatility regions, causes, clusters, and confidence-collapse regions.
- `longitudinal/recommendation_evolution.json`: recurring, resolved, persistent, volatile, and contradictory recommendation evidence.
- `longitudinal/anomaly_clusters.json`: rule-based clusters for contradictions, weak continuity, unstable boundaries, callbacks, drift, and recommendation hotspots.
- `longitudinal/persistent_patterns.json`: chronic weak boundaries, rhetorical gaps, continuity failures, unresolved claims, contradiction regions, and discourse patterns.
- `longitudinal/semantic_evolution.json`: future semantic continuity hooks and deterministic authority rules without embeddings or model inference.
- `longitudinal/longitudinal_summary.json`: compact status, pressure, and classification guidance summary.
- `verification_evidence/longitudinal_validation.json`: schema and run-reference validation for longitudinal outputs.

Longitudinal and semantic-evolution outputs are deterministic historical-analysis heuristics intended for editorial review and system explainability. They are not semantic truth systems, predictive systems, or autonomous editorial agents.

## Manifest Required Fields

`manifest.json` includes:

- `tool_version`
- `generation_timestamp_utc`
- `source_video_sha256`
- `source_video_size_bytes`
- `analysis_profile_hash`
- `subsystem_statuses`
- `dependency_versions`
- `execution_duration_sec`
- `warnings`
- `limitations`

`subsystem_statuses` includes:

- `media_probe`
- `audio_extract`
- `transcription`
- `segmentation`
- `emotional_arc`
- `persona_classification`
- `visual_sampling`
- `bundle_generation`
- `reporting`
- `graphs`
- `acoustic_analysis`
- `topic_analysis`
- `rhetorical_analysis`
- `revision_graph`
- `evidence_consensus`
- `revision_schema_validation`
- `discourse_state`
- `argument_graph`
- `narrative_memory`
- `callback_resolution`
- `editorial_ambiguity`
- `discourse`
- `continuity_schema_validation` is recorded in `verification_evidence/continuity_schema_validation.json`.
- `discourse_schema_validation` is recorded in `verification_evidence/discourse_schema_validation.json`.
- `visual_structure` records deterministic visual structure status.
- `visual_structure_validation` is recorded in `verification_evidence/visual_structure_validation.json`.

## Status Fields

Status values are explicit so downstream agents can detect partial analysis:

- `complete`: feature ran and produced usable output.
- `limited`: feature ran with reduced evidence.
- `unavailable`: dependency or input was missing.
- `error`: feature attempted to run but failed.
- `skipped`: user disabled the feature.

Subsystem statuses must use only these values.

## Verification Evidence

The `verification_evidence/` directory preserves debugging inputs and command logs:

- `ffprobe_raw_output.json`
- `ffmpeg_audio_extract.log` when audio extraction is attempted
- `ffmpeg_frame_sampling.log` when visual sampling is attempted
- `analysis_audio.wav` when audio extraction succeeds
- `transcription_metadata.json`
- `sampling_logs.json`
- `schema_validation_results.json`
- `dependency_report.json`
- `revision_schema_validation.json`
- `consensus_validation.json`
- `continuity_schema_validation.json`
- `discourse_schema_validation.json`
- `shot_boundary_sampling_log.json`
- `visual_structure_validation.json`

When an artifact cannot be produced, the tool still writes placeholder JSON/SRT/Markdown outputs with explicit status and reason fields wherever possible.

## Direct Measurements

- File size
- SHA-256 hash
- Container and stream metadata from FFprobe
- Frame samples extracted by FFmpeg
- Transcript timestamps when faster-whisper is available
- Imported transcript provenance when `--transcript-import` is supplied
- Local acoustic energy and spectral summaries when local audio and `librosa` are available
- Local visual frame histogram, pixel-difference, edge-density, brightness, contrast, saturation proxy, complexity, motion proxy, and continuity summaries when OpenCV is available

## Heuristic Inferences

- Topic and scene segmentation
- Topic continuity and drift
- Rhetorical mode and balance
- Rhetorical coherence, question resolution, claim/example support, and boundary diagnostic quality
- Emotional arc scores
- Tonal shifts
- Persona/style categories
- Teaching style categories
- Recommendations
- Multimodal consensus and transition confidence
- Discourse state, argument-chain, callback, narrative memory, ambiguity, and continuity decomposition outputs
- Visual boundary alignment, visual reset candidates, visual contradiction pressure, and visual recommendations

Heuristic outputs include evidence fields and limitations. They should be reviewed by a human before being used as final editorial judgment.

All acoustic, rhetorical, persona, emotional, and topic outputs are heuristic evidence summaries for human review. They are not psychological, clinical, identity, or intent claims.

Consensus outputs are deterministic evidence-fusion heuristics intended to improve explainability and editorial review. They are not semantic truth guarantees or autonomous editorial decisions.

Topic continuity and rhetorical coherence are deterministic local heuristics for editorial review. They are not semantic truth guarantees.

Discourse, argument, callback, and ambiguity outputs are deterministic editorial-review heuristics intended to improve explainability and human review. They are not semantic truth guarantees, intent detection systems, or autonomous editorial decisions.

Visual structure outputs are deterministic pixel/color/edge-level evidence summaries for editorial review. They are not object recognition, identity detection, emotion recognition, or cinematic intent claims.

## Visual Structure Artifacts

Phase 13 adds:

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

The visual pass is additive. It may lower readiness when visual evidence contradicts transcript/discourse structure. It never mutates media, changes timelines, calls Resolve, uses cloud APIs, calls LLMs, uses embeddings, or applies edits.

## Discourse Artifacts

Phase 12 adds:

- `discourse/discourse_state.json`
- `discourse/argument_graph.json`
- `discourse/narrative_memory.json`
- `discourse/callback_resolution.json`
- `discourse/editorial_ambiguity.json`
- `discourse/discourse_summary.json`
- `reports/discourse_state_report.md`
- `reports/argument_graph_report.md`
- `reports/narrative_memory_report.md`
- `reports/callback_resolution_report.md`
- `reports/editorial_ambiguity_report.md`
- `graphs/discourse_flow_graph.png`
- `graphs/argument_chain_graph.png`
- `graphs/callback_resolution_map.png`
- `graphs/narrative_memory_timeline.png`
- `graphs/discourse_pressure_curve.png`
- `graphs/ambiguity_distribution.png`
- `graphs/unresolved_argument_map.png`
- `visualizations/discourse_state.html`
- `visualizations/argument_graph.html`
- `visualizations/narrative_memory.html`
- `visualizations/callback_resolution.html`
- `visualizations/editorial_ambiguity.html`
- `verification_evidence/discourse_schema_validation.json`

The discourse pass is additive. It may add review evidence to recommendations, consensus, boundary diagnostics, and release readiness, but it never rewrites boundaries, mutates revisions, mutates media, changes timelines, calls Resolve, or applies edits.

## Continuity Artifacts

Phase 11 adds:

- `continuity/topic_continuity.json`
- `continuity/rhetorical_coherence.json`
- `continuity/boundary_diagnostics.json`
- `continuity/continuity_summary.json`
- `reports/topic_continuity_report.md`
- `reports/rhetorical_coherence_report.md`
- `reports/boundary_diagnostics_report.md`
- `graphs/topic_continuity_curve.png`
- `graphs/topic_bridge_map.png`
- `graphs/rhetorical_coherence_timeline.png`
- `graphs/claim_evidence_balance.png`
- `graphs/boundary_diagnostic_matrix.png`
- `visualizations/topic_continuity.html`
- `visualizations/rhetorical_coherence.html`
- `visualizations/boundary_diagnostics.html`
- `verification_evidence/continuity_schema_validation.json`

The continuity pass is additive. `scene_segments.json` may include a non-breaking `boundary_diagnostic` object on segments after the first segment. Boundaries are never rewritten automatically.

## Consensus Artifacts

The consensus system adds:

- `consensus/evidence_consensus.json`
- `consensus/modality_agreement.json`
- `consensus/modality_disagreement.json`
- `consensus/transition_confidence.json`
- `consensus/evidence_score_summary.json`
- `consensus/false_positive_boundaries.json`
- `consensus/continuity_analysis.json`
- `reports/evidence_consensus_report.md`
- `reports/evidence_consensus_report.json`
- `reports/continuity_report.md`
- `reports/continuity_report.json`
- `reports/segmentation_confidence_report.md`
- `reports/segmentation_confidence_report.json`
- `visualizations/evidence_consensus.html`
- `visualizations/continuity_analysis.html`
- `visualizations/segmentation_confidence.html`
- `visualizations/modality_alignment.html`
- `graphs/modality_agreement_heatmap.png`
- `graphs/modality_disagreement_heatmap.png`
- `graphs/transition_confidence_curve.png`
- `graphs/evidence_strength_distribution.png`
- `graphs/continuity_alignment.png`
- `graphs/false_positive_boundaries.png`
- `graphs/segmentation_confidence.png`

Consensus classes are `strong_agreement`, `moderate_agreement`, `weak_agreement`, `disagreement`, and `insufficient_evidence`. Transition confidence classes are `high`, `moderate`, `weak`, and `ambiguous`.

## Revision Graph Artifacts

The revision graph system adds:

- `revision_graph/revision_graph.json`
- `revision_graph/revision_graph.md`
- `revision_graph/revision_states.json`
- `revision_graph/revision_lineage.json`
- `revision_graph/revision_candidates.json`
- `revision_graph/revision_deltas.json`
- `revision_graph/editorial_constraints.json`
- `revision_graph/release_readiness_report.json`
- `revision_graph/mutation_safety_contract.json`
- `revision_graph/branch_comparison_report.json`
- `revision_graph/revision_recommendations.json`
- `visualizations/revision_graph.html`
- `visualizations/revision_comparison.html`
- `visualizations/release_readiness.html`
- `visualizations/mutation_safety.html`
- `visualizations/editorial_evolution.html`
- `graphs/revision_score_evolution.png`
- `graphs/branch_comparison.png`
- `graphs/release_readiness_radar.png`
- `graphs/constraint_pressure.png`
- `graphs/mutation_safety_matrix.png`
- `graphs/editorial_evolution.png`
- `reports/revision_graph_summary.md`
- `reports/revision_graph_summary.json`
- `reports/release_readiness_summary.md`
- `reports/branch_comparison_summary.md`
- `reports/mutation_safety_summary.md`

Revision statuses are `observed`, `proposed`, `simulated`, `applied_external`, `rejected`, or `superseded`. This implementation generates observed and simulated states only; candidates are proposal records. Revision IDs use `REV_<short sha256>` from stable source SHA, profile hash, parent revision, candidate change set, and artifact hashes. Timestamps are metadata and do not affect IDs.

Revision graph outputs are planning and simulation artifacts. They do not apply edits, mutate media, change Resolve timelines, or guarantee publication readiness. They are deterministic decision-support artifacts for human review.
# Integrity Outputs

Phase 14 adds the `integrity/` artifact family:

- `artifact_integrity.json`
- `graph_consistency.json`
- `reference_validation.json`
- `lineage_validation.json`
- `dashboard_coverage.json`
- `artifact_dependency_graph.json`
- `migration_registry.json`
- `semantic_readiness.json`

These outputs are deterministic, local-first, and schema-backed. They do not call cloud APIs, LLMs, embedding models, vector databases, or media editors.

# Sequence And Comparative Outputs

Phase 19-22A adds:

- `sequence/sequence_structure.json`
- `sequence/scene_hierarchy.json`
- `sequence/temporal_rhythm.json`
- `sequence/narrative_phase_model.json`
- `sequence/editorial_pressure.json`
- `sequence/recommendation_dependencies.json`
- `sequence/revision_propagation.json`
- `sequence/counterfactual_simulation.json`
- `sequence/revision_forecasting.json`
- `sequence/epistemic_stability.json`
- `sequence/sequence_summary.json`
- `comparative/multi_video_analysis.json`
- `comparative/style_fingerprint.json`
- `comparative/rhetorical_fingerprint.json`
- `comparative/pacing_fingerprint.json`
- `comparative/discourse_fingerprint.json`
- `comparative/creator_evolution.json`
- `comparative/structural_pattern_mining.json`
- `comparative/comparative_recommendations.json`
- `comparative/semantic_equivalence_scaffolding.json`
- `comparative/comparative_summary.json`

Companion reports, graphs, static local HTML pages, schemas, and validation records are generated under `reports/`, `graphs/`, `visualizations/`, `schemas/`, and `verification_evidence/`.

Temporal, propagation, comparative, fingerprint, and semantic-equivalence-scaffolding outputs are deterministic editorial-analysis heuristics intended for explainability and human review. They are not semantic truth systems, identity-recognition systems, predictive systems, or autonomous editorial agents.

# Corpus, Audit, Workbench, And Governance Outputs

Phase 23-26 adds a corpus-level `Corpus_analysis/` folder with:

- `corpus/corpus_index.json`
- `corpus/corpus_run_manifest.json`
- `corpus/corpus_intelligence.json`
- `corpus/corpus_fingerprint.json`
- `corpus/editorial_archetypes.json`
- `corpus/comparative_stabilization.json`
- `corpus/corpus_recommendations.json`
- `corpus/corpus_readiness.json`
- `corpus/corpus_summary.json`
- `audit/audit_trail.json`
- `audit/validation_replay.json`
- `audit/provenance_reconstruction.json`
- `audit/artifact_replay_index.json`
- `audit/evidence_traceability.json`
- `workbench/review_queue.json`
- `workbench/priority_review_items.json`
- `workbench/editorial_workbench.json`
- `workbench/segment_review_index.json`
- `workbench/recommendation_review_index.json`
- `workbench/pressure_review_index.json`
- `governance/governance_policy.json`
- `governance/readiness_arbitration.json`
- `governance/rc_assessment.json`
- `governance/release_candidate_checklist.json`
- `governance/governance_summary.json`

Corpus, workbench, audit, governance, and release-candidate outputs are deterministic editorial-review artifacts. They do not perform autonomous editing, semantic inference, identity recognition, cloud analysis, or media/timeline mutation.

# RC Hardening Outputs

Phase 27 adds:

- `workbench/compressed_review_queue.json`
- `workbench/review_queue_tiers.json`
- `workbench/review_queue_clusters.json`
- `workbench/review_queue_summary.json`
- `workbench/next_best_human_actions.json`
- `governance/governance_diagnostics.json`
- `governance/governance_failure_explanations.json`
- `governance/rc_threshold_analysis.json`
- `governance/blocker_analysis.json`
- `governance/rc_promotion_path.json`
- `remediation/remediation_tracker.json`
- `remediation/recurring_pressure_remediation.json`
- `remediation/archetype_remediation.json`
- `remediation/readiness_blocker_remediation.json`
- `remediation/remediation_summary.json`
- `verification_evidence/rc_hardening_validation.json`

Companion reports, graphs, schemas, and static local HTML pages are generated under `reports/`, `graphs/`, `schemas/`, and `visualizations/`.

RC hardening and remediation outputs are deterministic review-planning artifacts. They do not apply edits, mutate media, change timelines, perform semantic inference, or make autonomous release decisions.

# Expert Dashboard Outputs

Phase 31 adds:

- `dashboard/dashboard_explanation_catalog.json`
- `dashboard/visualization_catalog.json`
- `dashboard/graph_interpretation_index.json`
- `dashboard/optimization_guidance_index.json`
- `dashboard/expert_metric_ranges.json`
- `dashboard/dashboard_layout_manifest.json`
- `reports/dashboard_explanation_report.md`
- `reports/graph_interpretation_report.md`
- `reports/optimization_guidance_report.md`
- `reports/visualization_catalog_report.md`
- `visualizations/dashboard_explanation_index.html`
- `visualizations/graph_interpretation_index.html`
- `visualizations/optimization_guidance_index.html`
- `visualizations/expert_metric_ranges.html`
- `visualizations/detail/*.html`
- `verification_evidence/dashboard_ux_validation.json`

The expert dashboard pages remain static, relative-link safe, and local-first. Graph interpretations include what each graph measures, why it matters, how to read it, good/caution/concern guidance, current observed values when available, optimization guidance, evidence references, and what not to infer.

Dashboard interpretation and optimization guidance are deterministic editorial-review aids. They do not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous creative decisions. Human review is required before production or editing changes.

# Expert Review UI Outputs

Phase 32 adds:

- `dashboard/metric_card_registry.json`
- `dashboard/benchmark_comparison_registry.json`
- `dashboard/recommendation_ranking.json`
- `dashboard/optimization_effort_estimates.json`
- `dashboard/segment_drilldown_index.json`
- `dashboard/compare_workflow_registry.json`
- `dashboard/threshold_overlay_registry.json`
- `dashboard/dashboard_navigation_manifest.json`
- `reports/metric_card_system_report.md`
- `reports/benchmark_comparison_report.md`
- `reports/recommendation_ranking_report.md`
- `reports/optimization_effort_report.md`
- `reports/segment_drilldown_report.md`
- `reports/compare_workflow_report.md`
- `visualizations/metric_card_gallery.html`
- `visualizations/benchmark_comparison_index.html`
- `visualizations/recommendation_priority_dashboard.html`
- `visualizations/optimization_effort_dashboard.html`
- `visualizations/compare_workflows.html`
- `visualizations/segment_drilldown_index.html`
- `visualizations/detail/segment_drilldown_*.html`
- `visualizations/detail/compare_*.html`
- `visualizations/detail/benchmark_*.html`
- `verification_evidence/expert_review_ui_validation.json`

The expert review UI outputs are static local review aids. They add metric cards, benchmark comparisons, recommendation ranking, optimization effort estimates, segment drilldowns, compare workflows, threshold overlays, tooltip definitions, sticky navigation, and progressive-disclosure pages without adding a runtime service.

The expert dashboard system provides deterministic editorial-review guidance and optimization interpretation. It does not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict audience behavior, or make autonomous creative decisions. Human review is required before production or editorial changes.
## Phase 33 Temporal Review Outputs

Corpus runs now write static temporal review artifacts under `timeline/`, recommendation traceability artifacts under `recommendations/`, profile scaffolds under `benchmarks/`, navigation manifests under `dashboard/`, reports under `reports/`, schemas under `schemas/`, and HTML pages under `visualizations/`.

The temporal review system provides deterministic editorial-review guidance and timeline-linked evidence navigation. It does not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous creative decisions. Human review is required before production or editorial changes.

## Phase 34 Timeline Workstation Outputs

Phase 34 adds `workstation/workstation_manifest.json`, `timeline_minimap_registry.json`, `overlay_lane_registry.json`, `overlay_filter_registry.json`, `review_flow_shortcuts.json`, `persistent_context_registry.json`, `inline_evidence_preview_index.json`, `recommendation_drawer_index.json`, `temporal_heatmap_registry.json`, `compare_readability_registry.json`, `review_state_summary.json`, and `workstation_crosslink_index.json`.

Static pages are generated under `visualizations/workstation/` and enhanced timeline pages are generated under `visualizations/timeline/` as `enhanced_video_timeline_*.html`, `enhanced_corpus_timeline_overview.html`, `timeline_minimap_*.html`, `overlay_lane_view_*.html`, and `timeline_heatmap_*.html`.

The timeline workstation system provides deterministic editorial-review guidance and workflow navigation. It does not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous creative decisions. Human review is required before production or editorial changes.

## Phase 35 Review Continuity Outputs

Phase 35 adds:

- `review_sessions/review_session_registry.json`, `review_state_registry.json`, `review_checkpoints.json`, `review_resume_index.json`, `review_progress_summary.json`, `review_activity_history.json`, `review_completion_registry.json`, `review_followup_registry.json`, `review_escalation_registry.json`, and `reviewer_rationale_registry.json`
- `annotations/reviewer_annotations.json`, `annotation_timeline_markers.json`, `annotation_group_registry.json`, `annotation_filter_registry.json`, `annotation_review_index.json`, and `annotation_crosslinks.json`
- `queues/review_queue_registry.json` plus high-priority, low-effort/high-impact, unresolved blocker, escalation, governance, pacing, and rhetorical queue subsets
- `handoff/review_handoff_packets.json`, `governance_review_packets.json`, `escalation_packets.json`, `printable_review_packets.json`, and `review_packet_export_registry.json`
- static review dashboards under `visualizations/review/` and packet pages under `visualizations/review/packets/`

The review continuity system provides deterministic editorial-review workflow support and audit-preserving operational review continuity. It does not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous creative decisions. Human review is required before production or governance changes.

## Phase V56 Portable Export Outputs

V56 adds `portable_reachability_report.json`, `portable_export_audit_report.json`, `portable_export_audit_report.md`, `portable_deduplication_report.json`, and `portable_export_timing_report.json`.

The manifest distinguishes human-review, display, analysis-inspection, audit, validation, optional, and generated artifacts. Raw media is excluded by default.
