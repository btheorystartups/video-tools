# Video Insight Bundler

## Phase V55 Portable Review Package

Corpus runs can now emit a self-contained portable review package:

```powershell
py -3.13 .\tools\video-insight-bundler\analyze_corpus.py --corpus "C:\Users\brian\Documents\Book-Agents\tools\video-insight-bundler\Videos\Brian\Corpus" --include "C:\Users\brian\Documents\Book-Agents\tools\video-insight-bundler\Videos\Brian\Why Should Anyone Listen to you Anyway - Brian Theory.mp4" --force --verbose --portable-export --zip-export
```

The export writes `Corpus_analysis/portable_review_package/index.html`, package manifests, validation reports, exclusion manifests, diff and size reports, and optionally `portable_review_package.zip`. The package is intended to open from `file://` with no server, repository checkout, source media, internet, CDN, Python process, or cloud APIs.

Raw videos and raw audio are excluded by default. Use `--portable-include-raw-media` only when redistribution is intentional; included media is copied under `media/` and clearly reported. When raw media is excluded, live source-video links are rewritten to an explanatory placeholder while original paths remain metadata only.

Additional export flags: `--portable-export-root`, `--portable-strict`, `--portable-allow-provenance-absolute-paths`, `--portable-max-file-size-warning-mb`, and `--portable-copy-mode copy`.

Standalone export is also available:

```powershell
py -3 -m tools.video_insight_bundler.portable_export_package --source "C:\path\to\Corpus_analysis" --dest "C:\path\to\portable_review_package" --zip
```

Classification remains operational beta+ / internal beta_plus.

## Phase V54

Phase V54 adds optional LLM-assisted expert interpretation and deterministic fallback enrichment for the actual generated HTML pages. The default mode is `deterministic_fallback`; tests and normal corpus generation do not require a cloud provider or network access.

The LLM layer is advisory explanatory text only. Deterministic artifacts remain authoritative for measurements, graph values, source evidence, recommendations, validation, governance state, blockers, readiness, snapshots, lineage, media, and timelines. Interpretation text is safety-scanned for forbidden claims and cannot resolve blockers, promote readiness, mutate media, mutate timelines, or make autonomous edits.

Corpus output now includes `llm_interpretation/` registries, `visualizations/llm_interpretation/` dashboards, actual HTML enrichment validation under `verification_evidence/`, and reports under `reports/`. All target pages visibly include expert explanation, current-value interpretation or fallback text, optimization guidance, evidence/recommendation sections, human review guidance, and limitations.

## Phase V51-53

Phase V51-53 restores graph-card clickthrough and explanatory graph detail UX, adds persistent static graph meaning, deterministic observed graph interpretation, graph-to-evidence and graph-to-recommendation linkage, offline interpretation packet export/import scaffolding, and configured-corpus multi-video comparison workbench outputs.

Phase V51-53B repairs the actual generated dashboard files that operators open. Core graph cards for Emotional Arc, Pacing Curve, Acoustic Energy, and Topic Timeline now wrap the graph image, graph title, and an explicit `Explain this graph` action in local-file links to `visualizations/graph_ux/detail/*_detail.html`. The detail pages include substantive sections for graph meaning, reading guidance, good/caution/concerning patterns, observed deterministic interpretation, optimization options, preservation guidance, limitations, evidence links, and human review notes.

`visualizations/graph_ux/graph_detail_index.html` lists graph pages by family with status, observed summaries, and links. The dashboard's Detailed Pages section is grouped by category while preserving existing links.

The repair and validation step parses actual HTML dashboards. It writes `graph_ux/dashboard_graph_clickthrough_audit.json`, `reports/dashboard_graph_clickthrough_audit_report.md`, and `verification_evidence/dashboard_graph_clickthrough_validation.json`, and fails when required core graph cards or explanatory sections are missing from the generated HTML.

Same-speaker comparison readiness is based on configured corpus context and artifact continuity, not biometric identity recognition. Imported interpretation is external/human-authored content with provenance and does not automatically change governance status.

`video-insight-bundler` is a standalone local-first command-line tool for turning a video file into a structured analysis bundle for humans and LLMs.

It does not use DaVinci Resolve, Resolve scripting, timelines, media pools, or project state.

Phase 47 adds deterministic operational replay and continuity proofing under `Corpus_analysis/replay/`. The replay layer remains browserless and static, with extreme-history fixtures, semantic accessibility linting, ARIA survivability checks, replay coverage, reproducibility scoring, and operational proof dashboards.

## Run

```powershell
py -3.13 .\tools\video-insight-bundler\analyze_video.py --video "C:\path\to\video.mp4" --output .\output\video_analysis --force --verbose
```

Useful options:

```text
--video             Required source video path.
--output            Root output directory. A <safe-video-stem>_analysis folder is created inside it.
--profile           Analysis profile JSON. Default: config/analysis_profile.default.json.
--sample-interval   Seconds between sampled frames.
--transcribe         Attempt local audio extraction and faster-whisper transcription. Default.
--no-transcribe      Skip transcription and continue with metadata/time-window analysis.
--transcript-import  Use OpenAI Whisper JSON or native transcript JSON and skip transcription.
--force             Reuse an existing per-video output folder.
--no-revision-graph Skip deterministic editorial revision graph generation.
--revision-profile  Revision graph profile JSON. Default: config/revision_profile.default.json.
--verbose           Print progress.
```

## Dependencies

Required for full local media analysis:

- Python 3.13 or compatible Python 3.x
- FFmpeg
- FFprobe

Optional:

- `faster-whisper` for local transcription
- Visualization/reporting extras:

```powershell
py -3 -m pip install -r .\tools\video-insight-bundler\requirements-visualization.txt
```

Current graph generation requires `matplotlib`. `networkx`, `wordcloud`, and `textstat` improve network, word cloud, and readability outputs. `librosa` enables local acoustic energy/rhythm summaries, `scikit-learn` enables TF-IDF topic analysis, `pillow` enables frame contact sheets, and `plotly` enables optional self-contained interactive HTML charts.
`opencv-python` and `numpy` enable deterministic local visual structure and shot-boundary evidence. Install with `py -3.13 -m pip install opencv-python` for the Python used to run `analyze_video.py`. If OpenCV is unavailable, the tool writes placeholder visual structure artifacts with structured warnings and keeps downstream outputs intact.

If `faster-whisper` is not installed, the tool writes `transcription_status: unavailable`, still probes metadata, samples frames, creates fallback segments, and writes LLM bundles.
Use `--transcript-import` to provide an existing transcript and preserve import provenance without running local transcription.

## Outputs

Corpus mode now includes Phase 46 operational resilience artifacts. A corpus run writes resilience registries under `Corpus_analysis/resilience/`, static resilience dashboards under `Corpus_analysis/visualizations/resilience/`, schemas under `Corpus_analysis/schemas/`, reports under `Corpus_analysis/reports/`, and validation evidence at `Corpus_analysis/verification_evidence/operational_resilience_validation.json`.

Phase 46 remains local-first and deterministic. It adds no cloud APIs, LLM runtime calls, embeddings, vector databases, servers, databases, frontend frameworks, hidden mutable runtime state, or autonomous editorial decisions.

For a video named `lecture.mp4`, the tool writes:

```text
output/video_analysis/lecture_analysis/
  manifest.json
  dependency_report.json
  validation_report.json
  transcript.json
  transcript.srt
  audio_features.json
  acoustic_features.json
  topic_analysis.json
  rhetorical_analysis.json
  visual_sample_index.json
  scene_segments.json
  emotional_arc.json
  persona_style_profile.json
  teaching_style_profile.json
  recommendations.md
  recommendations.json
  continuity/
  discourse/
  visual_structure/
  sequence/
  comparative/
  llm_context_bundle.md
  llm_context_bundle.json
  analysis_index.json
  analysis_index.md
  consensus/
  revision_graph/
  charts/
  interactive/
  visualizations/
  graphs/
  reports/
  static_assets/
  frames/
  verification_evidence/
```

`visualizations/dashboard.html` is the portable master dashboard and opens directly from disk. `graphs/` contains PNG visualizations. `interactive/` contains optional self-contained Plotly exports when Plotly is installed. `reports/` contains quality and statistics reports. `charts/` contains CSV data for emotional arc and pacing summaries. `frames/` contains regular-interval JPEG samples. `verification_evidence/` preserves dependency diagnostics, raw FFprobe output, FFmpeg logs, transcription metadata, sampling logs, and schema validation results.

`consensus/` contains deterministic multimodal evidence-fusion artifacts: evidence consensus, modality agreement/disagreement, transition confidence, evidence strength, false-positive boundary flags, and continuity analysis. Companion pages are written under `visualizations/`, PNGs under `graphs/`, summaries under `reports/`, and validation evidence under `verification_evidence/`.

`continuity/` contains deterministic topic continuity, rhetorical coherence, boundary diagnostics, and summary artifacts. The pass uses rolling transcript windows, TF-IDF or frequency fallback, Jaccard/cosine similarity where available, marker-based rhetorical patterns, and cross-modal boundary evidence. It does not use embeddings, vector databases, CLIP, cloud APIs, LLM calls, or autonomous editing. Topic continuity and rhetorical coherence are deterministic local heuristics for editorial review. They are not semantic truth guarantees.

`discourse/` contains deterministic discourse-state, argument graph, narrative memory, callback resolution, editorial ambiguity, and continuity decomposition artifacts. These outputs improve explanation of topic drift, contradiction pressure, setup/payoff linkage, delayed resolution, and recommendation specificity. Discourse, argument, callback, and ambiguity outputs are deterministic editorial-review heuristics intended to improve explainability and human review. They are not semantic truth guarantees, intent detection systems, or autonomous editorial decisions.

`visual_structure/` contains deterministic local visual evidence: shot-boundary candidates, visual continuity, composition features, visual-boundary alignment, and a compact summary. Visual structure outputs are deterministic pixel/color/edge-level evidence summaries for editorial review. They are not object recognition, identity detection, emotion recognition, or cinematic intent claims.

`revision_graph/` contains deterministic editorial revision graph artifacts: immutable observed revision state, proposal-only candidate branches, deltas, lineage, constraints, release readiness, mutation safety, branch comparison, and revision recommendations. Companion static pages are written under `visualizations/`, PNGs under `graphs/`, and summaries under `reports/`.

Revision graph outputs are planning and simulation artifacts. They do not apply edits, mutate media, change Resolve timelines, or guarantee publication readiness. They are deterministic decision-support artifacts for human review.

`longitudinal/` contains deterministic multi-run historical intelligence: longitudinal analysis, trend analysis, confidence volatility, recommendation evolution, rule-based anomaly clusters, persistent patterns, semantic-evolution scaffolding, and a compact summary. Companion static pages are written under `visualizations/`, PNGs under `graphs/`, reports under `reports/`, schemas under `schemas/`, and validation evidence under `verification_evidence/longitudinal_validation.json`.

Longitudinal and semantic-evolution outputs are deterministic historical-analysis heuristics intended for editorial review and system explainability. They are not semantic truth systems, predictive systems, or autonomous editorial agents.

`sequence/` contains deterministic hierarchical temporal intelligence: sequence structure, scene hierarchy, temporal rhythm, narrative phase model, editorial pressure, recommendation dependencies, revision propagation, counterfactual simulation, revision forecasting, epistemic stability, and `sequence_summary.json`.

`comparative/` contains deterministic multi-video and creator-level comparative intelligence: multi-video analysis, style fingerprint, rhetorical fingerprint, pacing fingerprint, discourse fingerprint, creator evolution, structural pattern mining, comparative recommendations, semantic-equivalence scaffolding, and `comparative_summary.json`.

Temporal, propagation, comparative, fingerprint, and semantic-equivalence-scaffolding outputs are deterministic editorial-analysis heuristics intended for explainability and human review. They are not semantic truth systems, identity-recognition systems, predictive systems, or autonomous editorial agents.

## Corpus Analysis

Put corpus videos in `tools/video-insight-bundler/Videos/Brian/Corpus/` and run:

```powershell
py -3.13 .\tools\video-insight-bundler\analyze_corpus.py --corpus "C:\Users\brian\Documents\Book-Agents\tools\video-insight-bundler\Videos\Brian\Corpus" --include "C:\Users\brian\Documents\Book-Agents\tools\video-insight-bundler\Videos\Brian\Why Should Anyone Listen to you Anyway - Brian Theory.mp4" --force --verbose
```

The corpus runner creates per-video sibling analysis folders and a corpus-level `Corpus_analysis/` folder with `corpus/`, `audit/`, `workbench/`, `governance/`, `reports/`, `graphs/`, `visualizations/`, `schemas/`, and `verification_evidence/`.

Corpus, workbench, audit, governance, and release-candidate outputs are deterministic editorial-review artifacts. They do not perform autonomous editing, semantic inference, identity recognition, cloud analysis, or media/timeline mutation.

Phase 27 RC hardening adds `workbench/compressed_review_queue.json`, `workbench/review_queue_tiers.json`, `workbench/review_queue_clusters.json`, `workbench/next_best_human_actions.json`, `governance/governance_diagnostics.json`, `governance/rc_threshold_analysis.json`, `governance/blocker_analysis.json`, `governance/rc_promotion_path.json`, and `remediation/` review-planning artifacts. The static dashboard links these pages directly from disk and keeps links back to the original raw queue.

RC hardening and remediation outputs are deterministic review-planning artifacts. They do not apply edits, mutate media, change timelines, perform semantic inference, or make autonomous release decisions.

Phase 29 governance review workflow adds `governance/governance_review_session.json`, `governance/governance_reassessment.json`, `governance/governance_reassessment_delta.json`, `governance/governance_history.json`, `governance/reviewer_decision_support.json`, `governance/governance_replay_log.json`, `governance/governance_snapshot_registry.json`, `workbench/review_navigation_index.json`, `workbench/tier_1_evidence_navigation.json`, `workbench/reviewer_focus_queue.json`, and `workbench/reviewer_session_summary.json`.

Phase 30 human decision intake adds deterministic local reviewer templates under `review_input/`, validates canonical `reviewer_decisions.json`, writes `governance/validated_human_decisions.json`, `governance/rejected_human_decisions.json`, `governance/decision_reconciliation.json`, `governance/reassessment_gatekeeper.json`, `governance/governance_ledger.json`, and `governance/decision_provenance.json`, then exposes status pages in the static dashboard. Human decision intake artifacts are deterministic local governance-review artifacts. They do not apply edits, mutate media, accept risk automatically, classify false positives automatically, or make autonomous release decisions. Only explicit, schema-valid human decisions can influence reassessment.

Governance reassessment artifacts are deterministic review and audit artifacts. They do not automatically resolve blockers, apply edits, accept risk, classify false positives, or make autonomous release decisions. Human review is required.

Phase 42 longitudinal narratives add `narratives/longitudinal_review_narratives.json`, `operational_milestone_registry.json`, `change_explanation_registry.json`, `historical_significance_registry.json`, `operator_memory_restore_registry.json`, `timeline_narrative_registry.json`, governance/adjudication/queue evolution narratives, compressed history, drift explanations, cross-session memory, review bookmarks, and history compression registries. Static dashboards are written under `visualizations/narratives/`.

These outputs deterministically compress existing append-only longitudinal artifacts into operator-readable memory and timeline views. They do not call cloud APIs, LLMs, embeddings, vector databases, servers, databases, or hidden runtime services, and they do not make autonomous historical or editorial decisions.

Phase 43 narrative navigation adds `recall/historical_recall_paths.json`, `operator_handoff_registry.json`, `historical_lens_registry.json`, `contextual_stitching_registry.json`, continuity registries, related-event links, rapid context restore, operational memory traversal, narrative linkage graphs, handoff packet registries, operational-state transitions, and compressed recall navigation. Static dashboards are written under `visualizations/recall/`.

These outputs turn Phase 42 memory into deterministic navigation and handoff surfaces. They preserve append-only lineage and visible source references, and they do not call cloud APIs, LLMs, embeddings, vector databases, servers, databases, or hidden runtime services.

Phase 44 recall wayfinding adds `wayfinding/layered_recall_drilldown.json`, breadcrumb, graph cross-highlight, continuity sync, history pagination, compressed node grouping, filtered continuity, historical scope, navigation completeness, orphaned state, continuity path validation, operational wayfinding, drilldown continuity, contextual deep-link, and navigation survivability registries. Static dashboards are written under `visualizations/wayfinding/`.

These outputs make large historical recall paths more drillable and survivable for operators. They preserve deterministic source references, append-only lineage, visible limitation language, and local-only execution. They do not call cloud APIs, LLMs, embeddings, vector databases, servers, databases, or hidden runtime services, and they do not make autonomous editorial decisions.

Phase 31 expert dashboards add `dashboard/dashboard_explanation_catalog.json`, `dashboard/visualization_catalog.json`, `dashboard/graph_interpretation_index.json`, `dashboard/optimization_guidance_index.json`, `dashboard/expert_metric_ranges.json`, `dashboard/dashboard_layout_manifest.json`, detail pages under `visualizations/detail/`, and dashboard UX validation under `verification_evidence/dashboard_ux_validation.json`.

Dashboard interpretation and optimization guidance are deterministic editorial-review aids. They do not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous creative decisions. Human review is required before production or editing changes.

Phase 32 expert review UI adds `dashboard/metric_card_registry.json`, `dashboard/benchmark_comparison_registry.json`, `dashboard/recommendation_ranking.json`, `dashboard/optimization_effort_estimates.json`, `dashboard/segment_drilldown_index.json`, `dashboard/compare_workflow_registry.json`, `dashboard/threshold_overlay_registry.json`, and `dashboard/dashboard_navigation_manifest.json`. Static pages include metric card galleries, benchmark comparisons, recommendation priority, optimization effort, compare workflows, and segment drilldowns.

The expert dashboard system provides deterministic editorial-review guidance and optimization interpretation. It does not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict audience behavior, or make autonomous creative decisions. Human review is required before production or editorial changes.

Phase 34 timeline workstation polish adds `workstation/workstation_manifest.json`, minimap, overlay lane/filter, context panel, inline evidence preview, recommendation drawer, temporal heatmap, compare readability, review state, and crosslink registries. Static pages are generated under `visualizations/workstation/` and enhanced timeline pages under `visualizations/timeline/`. The timeline workstation system provides deterministic editorial-review guidance and workflow navigation. It does not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous creative decisions. Human review is required before production or editorial changes.

## Use With GPT/Codex

Use `llm_context_bundle.md` when you want a pasteable summary. Use `llm_context_bundle.json` when you want structured context for an agent, evaluator, or future pipeline.

The bundle separates measured facts from heuristic inferences. All acoustic, rhetorical, persona, emotional, and topic outputs are heuristic evidence summaries for human review. They are not psychological, clinical, identity, or intent claims.

## Phase 38 Operational Adjudication

Corpus runs write human adjudication event artifacts to `Corpus_analysis/adjudication_events/` and operational scalability artifacts to `Corpus_analysis/operations/`.

Key additions:

- append-only adjudication event import, validation, lineage, provenance, and history
- governance escalation event import and adjudication outcome registry
- generation dependency tracking and deterministic rebuild manifests
- validation index and artifact-hash-aware validation cache registry
- selective regeneration and scoped rerun registries
- operational dashboards under `visualizations/operations/`

Limitation: This system provides deterministic operational review, adjudication, and validation workflow support. It does not autonomously resolve reviewer disagreements, infer identity, diagnose emotion, predict viewer behavior, or make autonomous editorial decisions. Human review is required.

## Current Scope

Implemented:

- FFprobe media metadata and SHA-256 hash
- FFmpeg audio extraction
- Optional faster-whisper transcription
- Transcript JSON and SRT writing
- Transcript-derived pacing and pause features
- Local acoustic energy/rhythm summaries when `librosa` is available
- Deterministic transcript topic/concept analysis
- Deterministic topic continuity diagnostics with bridge, re-entry, abrupt shift, and unsupported shift evidence
- Marker-based rhetorical deep dive
- Deterministic rhetorical coherence diagnostics for question/answer, claim/example, setup/payoff, and abstract/concrete balance
- Deterministic boundary diagnostics for human review without rewriting boundaries
- Deterministic hierarchical discourse-state tracking, argument-chain modeling, narrative memory, callback/setup-payoff tracking, editorial ambiguity classification, and continuity decomposition
- Deterministic local visual structure evidence, shot-boundary candidates, visual continuity, composition feature summaries, visual-boundary alignment, visual recommendations, and visual readiness inputs
- Deterministic hierarchical temporal intelligence, pacing-wave modeling, narrative phase structure, editorial pressure, recommendation dependencies, revision propagation, counterfactual simulation, and epistemic stability
- Deterministic multi-video comparative intelligence, creator evolution, structural pattern mining, editorial style fingerprints, rhetorical/pacing/discourse signatures, and semantic-equivalence scaffolding without embeddings
- Deterministic corpus runner, corpus fingerprints, editorial archetypes, audit trail, validation replay, provenance reconstruction, review queue, static editorial workbench, governance policy, readiness arbitration, and release-candidate checklist
- Deterministic RC hardening: compressed review queue tiers, governance threshold gaps, RC promotion path, blocker analysis, remediation tracker, archetype remediation, and next-best human actions
- Deterministic expert dashboard UX: graph explanation cards, graph detail pages, conservative metric ranges, optimization guidance, limitation panels, and visualization catalogs
- Deterministic expert review UI architecture: metric cards, benchmark comparisons, recommendation ranking, optimization effort estimates, segment drilldowns, compare workflows, threshold overlays, and sticky navigation
- Deterministic temporal review intelligence: timeline review pages, timeline overlays, recommendation pins, metric spikes, segment context panels, temporal evidence indexing, recommendation traceability, recommendation lineage, profile benchmark packs, temporal compare workflows, and guided review journeys
- Deterministic timeline workstation: enhanced timeline pages, minimaps, overlay lane grouping/filtering, persistent context panels, inline evidence previews, recommendation drawers, temporal heatmaps, compare readability summaries, review-flow shortcuts, review-state summaries, and workstation crosslinks
- Deterministic review continuity: reviewer annotations, review-state tracking, session memory, checkpoints, resume navigation, operational queues, follow-ups, escalations, reviewer rationale capture, activity history, and printable review packets
- Deterministic longitudinal review narratives: operational milestones, what-changed/why summaries, historical significance, operator memory restoration, narrative timelines, compressed history, drift explanations, cross-session memory, and review bookmarks
- Regular-interval frame sampling
- Transcript-aware or fixed-window segmentation
- Segment boundary confidence and quality reporting
- Heuristic emotional arc scoring
- Heuristic persona/style and teaching-style classification
- Evidence-ranked recommendations markdown and JSON
- Analysis index JSON and Markdown artifact maps
- LLM-ready markdown and JSON bundles
- Deterministic proposal-only editorial revision graph, release readiness, mutation safety, and branch comparison outputs
- Deterministic multimodal evidence consensus, transition confidence, continuity analysis, modality agreement/disagreement, continuity schema validation, and formal revision schema validation
- Discourse schema validation, discourse-specific reports, static HTML pages, and PNG graphs for discourse flow, argument chains, callbacks, narrative memory, ambiguity, and unresolved arguments

Stubbed or intentionally limited:

- Face, pose, object, identity, and visual emotion analysis
- Cloud transcription or cloud LLM analysis
- Applying edits, mutating rendered media, or modifying Resolve timelines

Consensus outputs are deterministic evidence-fusion heuristics intended to improve explainability and editorial review. They are not semantic truth guarantees or autonomous editorial decisions.

The temporal review system provides deterministic editorial-review guidance and timeline-linked evidence navigation. It does not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous creative decisions. Human review is required before production or editorial changes.

## Phase 35 Review Continuity

Phase 35 writes `review_sessions/`, `annotations/`, `queues/`, `handoff/`, `visualizations/review/`, and `visualizations/review/packets/` outputs for persistent editorial-review operations. These artifacts make reviewer memory explicit and auditable through JSON registries, static dashboards, checkpoint/resume links, follow-up and escalation workflows, rationale records, and printable handoff packets.

The review continuity system provides deterministic editorial-review workflow support and audit-preserving operational review continuity. It does not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous creative decisions. Human review is required before production or governance changes.
# Integrity And Semantic Readiness

The bundler now writes deterministic integrity artifacts under `integrity/`, including artifact integrity, graph consistency, reference validation, lineage validation, dashboard coverage, migration registry, and semantic readiness. Semantic readiness is scaffolding only: it does not generate embeddings, use vector databases, call LLMs, or perform semantic inference.
## Human Review Ingestion And Reconciliation

Phase 36 adds human review ingestion and reconciliation:

- reviewer worksheet templates in `templates/`
- canonical imported reviewer JSON in `review_imports/`
- import validation, provenance, and merge results
- reconciliation conflicts, resolutions, diffs, audit logs, and merge lineage in `reconciliation/`
- unresolved conflict, reconciliation-required, and imported follow-up queues
- static dashboards in `visualizations/reconciliation/`

Imports are append-preserving. Invalid or duplicate imports are surfaced explicitly, and conflicting reviewer decisions are queued for human reconciliation instead of being silently merged.

## Reviewer Adjudication And Arbitration

Phase 37 adds governed conflict adjudication:

- conflict resolution workflows in `adjudication/conflict_resolution_registry.json`
- reviewer adjudication records in `adjudication/reviewer_adjudication_registry.json`
- rationale diffs and reviewer disagreement views
- governance conflict analysis and unresolved ambiguity tracking
- consensus-required workflow scaffolding
- adjudication queues in `queues/`
- arbitration packets and dashboards in `visualizations/adjudication/`
- append-only adjudication lineage in `adjudication/adjudication_lineage.json`

Adjudication artifacts are workflow support only. They preserve disagreement, rationale, ambiguity, escalation state, governance impact, and lineage. They do not auto-resolve conflicts, auto-consensus reviewers, silently prefer imports, mutate operational state, add cloud APIs, call LLMs, use embeddings, or mutate media/timelines.

## Phase 39 Operator Workflows And Profiling

Phase 39 writes operator workflow outputs to `operator_imports/` and performance observability outputs to `performance/`. Static dashboards are generated in `visualizations/operator/` and `visualizations/performance/`.

The new outputs cover rich Markdown worksheet ingestion, import previews, validation previews, reconciliation previews, operator review cards, validation timing, rebuild-cost estimates, artifact density, dashboard render density, queue scaling simulation, throughput analysis, workload heatmaps, and scalability warnings. All estimates are deterministic local operational aids and require human review.

## Phase 40 Long-Session Operator Ergonomics

Phase 40 writes long-session workflow outputs to `session_ergonomics/`, benchmark history outputs to `benchmarks/`, and static pages to `visualizations/ergonomics/` and `visualizations/benchmarks/`.

New artifacts cover session pressure, fatigue reduction, progressive disclosure, compact navigation, queue chunking, bookmarks, focus restoration, interruption recovery, dense-dashboard pagination, operator attention heatmaps, empirical benchmark history, repeated snapshots, local baselines, benchmark comparisons, and performance drift. They are deterministic, local-first, and governance-preserving; they do not add servers, databases, cloud APIs, LLM runtime calls, embeddings, hidden mutable runtime state, or autonomous workflow management.

## Phase 41 Longitudinal Operational Intelligence

Phase 41 writes longitudinal outputs to `longitudinal/`, reports to `reports/`, schemas to `schemas/`, validation evidence to `verification_evidence/`, and static dashboards to `visualizations/longitudinal/`.

New artifacts cover persistent benchmark lineage, cross-session analytics, operational trends, governance drift, workload evolution, queue growth, escalation trends, ambiguity accumulation, artifact growth, rebuild-cost history, historical throughput, review survivability, operational regressions, session comparisons, and longitudinal heatmaps.

This system provides deterministic operational workflow and longitudinal observability support. It does not autonomously resolve reviewer disagreements, infer identity, diagnose emotion, predict viewer behavior, or make autonomous editorial decisions. Human review is required.

## Phase V67-V72 Operating Layer

Portable export adds `--cache-mode`, `--zip-mode`, `--delta-zip`, `--base-export`, `--topology-simplify`, `--review-session`, `--ci-smoke`, and `--benchmark-export`.

```powershell
python tools/video-insight-bundler/src/portable_export_package.py --source output/Corpus_analysis --export-profile review --validation-tier standard --generation-mode hybrid --cache-mode auto --zip --zip-mode optimized --topology-simplify safe --ci-smoke --benchmark-export
```

Classification remains `operational beta+ / internal beta_plus`; RC promotion is not recommended yet.

## Phase V56 Portable Export

Use `export_new_video.py` for the simplest new-video workflow:

```powershell
py -3.13 .\tools\video-insight-bundler\export_new_video.py `
  --video "C:\path\to\new_video.mp4" `
  --corpus "C:\path\to\Corpus" `
  --output-root "C:\path\to\Exports" `
  --package-name "my_new_video_analysis" `
  --export-profile review `
  --zip `
  --validate-extracted
```

Profiles are `minimal`, `review`, `audit`, and `full`; `review` is the default. Raw media is excluded unless `--include-raw-media` is set. The final console summary shows the `index.html` to open first and the zip to send.

## Phase 49 Fine-Grained Delta Provenance

Phase 49 extends cross-run diffing into artifact-level, route-level, panel-level, continuity-chain-level, evidence-chain-level, and recommendation-lineage-level drilldowns.

The corpus runner writes Phase 49 artifacts under `delta_provenance/`, reports under `reports/`, schemas under `schemas/`, validation evidence at `verification_evidence/fine_grained_delta_validation.json`, static dashboards under `visualizations/delta_provenance/`, and drilldown pages under `visualizations/delta_provenance/drilldowns/`.

These outputs explain what changed, where it changed, which preserved artifacts support the comparison, and which deltas require human review. They do not resolve regressions, overwrite historical lineage, mutate media or timelines, call external runtimes, or make autonomous editorial decisions.

## Phase 50 Historical Snapshot Archives

Phase 50 strengthens cross-run history by writing explicit run snapshots and selected artifact archives. New artifacts live under `snapshots/`, with persistent archived manifests and copied high-value artifacts under `snapshot_archive/`.

The phase records snapshot provenance, historical artifact lookup data, archived replay state, continuity state, dashboard panel state, evidence chains, recommendation lineage, validation evidence, snapshot comparison pairs, deterministic baseline choices, multi-run artifact lineage, retention metadata, integrity checks, and corpus/video comparison readiness. Forced reruns preserve `snapshot_archive/` and do not silently overwrite existing snapshot folders.

Every snapshot page includes the deterministic operational limitation language. Corpus/video readiness pages also state that same-speaker comparison readiness is based on configured corpus context and artifact continuity, not biometric identity recognition.

## Phase 48 Implementation Update

Added deterministic cross-run diff modules for artifact diffing, replay regression analysis, continuity drift analysis, rerun reproducibility comparison, operational delta proofing, replay evolution summaries, continuity evolution scoring, survivability deltas, operational equivalence validation, lineage comparison, replay proof deltas, rerun narratives, operational drift explainability, and deterministic rerun intelligence.

The corpus runner writes Phase 48 artifacts under `diffs/`, reports under `reports/`, schemas under `schemas/`, validation evidence at `verification_evidence/operational_diff_validation.json`, and static dashboards under `visualizations/diffs/`.

This system provides deterministic operational workflow and longitudinal observability support. It does not autonomously resolve reviewer disagreements, infer identity, diagnose emotion, predict viewer behavior, or make autonomous editorial decisions. Human review is required.

## Phase 45 Static Interaction And Review Acceleration

Phase 45 writes static interaction outputs to `interaction/`, reports to `reports/`, schemas to `schemas/`, validation evidence to `verification_evidence/interaction_efficiency_validation.json`, and dashboards to `visualizations/interaction/`.

New artifacts cover sortable tables, filterable lenses, compact routing, graph navigation affordances, continuity-priority traversal, orphan remediation review packets, route survivability, dashboard integrity, interaction compression, linked review pathways, continuity repair queues, review acceleration summaries, compact navigation layers, throughput indicators, and high-density interaction affordances.

This system provides deterministic operational workflow and longitudinal observability support. It does not autonomously resolve reviewer disagreements, infer identity, diagnose emotion, predict viewer behavior, or make autonomous editorial decisions. Human review is required.
