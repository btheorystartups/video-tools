# Evidence Consensus System

The evidence consensus system is a deterministic architectural pass that fuses existing local analysis streams without adding opaque AI behavior.

Consensus outputs are deterministic evidence-fusion heuristics intended to improve explainability and editorial review. They are not semantic truth guarantees or autonomous editorial decisions.

## Longitudinal Consensus Inputs

Evidence consensus now records historical agreement stability, recurring contradiction regions, chronic continuity patterns, volatility-adjusted confidence, anomaly clustering context, and persistent-weakness penalties. The adjustment is conservative and explainable: disagreement or weak-agreement rows receive the strongest confidence reduction, while stronger agreement rows receive only a small historical caution.

The consensus system remains deterministic evidence fusion for review. It does not change boundaries, media, timelines, recommendations, or source artifacts.

Longitudinal and semantic-evolution outputs are deterministic historical-analysis heuristics intended for editorial review and system explainability. They are not semantic truth systems, predictive systems, or autonomous editorial agents.

## Inputs

The engine uses only existing local artifacts:

- transcript timing and pause evidence
- segmentation boundary confidence
- acoustic energy and contrast
- deterministic topic continuity
- topic bridge support and unsupported shift counts
- marker-based rhetorical transitions
- deterministic rhetorical coherence score and rhetorical gap counts
- deterministic discourse continuity, argument completeness, callback strength, narrative persistence, and ambiguity interpretation
- deterministic visual structure evidence, shot-boundary candidates, visual continuity, visual reset candidates, visual-boundary alignment, and visual contradiction pressure
- boundary diagnostic support and contradiction counts
- pacing shifts
- transparent emotional arc signals
- recommendation evidence counts and confidence
- revision artifact completeness

It does not use embeddings, vector databases, CLIP, face recognition, identity detection, emotion recognition from faces, cloud APIs, LLM calls, a database, a web server, Resolve integration, or autonomous editing.

## Core Artifacts

- `consensus/evidence_consensus.json`: per-transition consensus score, class, supporting/conflicting modalities, evidence strength, continuity confidence, false-positive probability, notes, and limitations.
- `continuity/boundary_diagnostics.json`: boundary-level review diagnostics used to explain support, contradictions, and human-review actions.
- `consensus/transition_confidence.json`: fused boundary confidence from transcript pauses, topic shifts, rhetorical shifts, acoustic changes, pacing shifts, and emotional transitions.
- `consensus/false_positive_boundaries.json`: boundaries likely caused by isolated or weak evidence such as pacing-only shifts, transcript-pause-only shifts, or isolated acoustic spikes.
- `consensus/continuity_analysis.json`: topic, rhetorical, emotional, pacing, acoustic, and cross-modal continuity agreement.
- `consensus/modality_agreement.json` and `consensus/modality_disagreement.json`: pairwise modality alignment for topic/rhetoric, rhetoric/acoustic, acoustic/pacing, emotional/rhetoric, topic/emotional, and pacing/segmentation.
- `consensus/evidence_score_summary.json`: interpretable evidence strength scores for transcript, segmentation, acoustic, rhetorical, topic, emotional, recommendation, and revision evidence.
  Visual evidence strength is included when `visual_structure/` artifacts are present.

## Scoring Logic

Transition confidence is a weighted visible-signal average:

- transcript pause evidence
- rhetorical shift evidence
- topic shift evidence
- acoustic energy change
- pacing shift
- emotional transition
- visual boundary support, when available, is integrated after visual-boundary alignment

Continuity overrides reduce confidence when topic and rhetorical continuity remain high while only pause, pacing, or acoustic evidence suggests a boundary.

Consensus distinguishes transcript-only boundaries, visual-only boundaries, multimodal boundaries, discourse boundaries without visual reset, visual resets without transcript transitions, and unsupported visual jumps through `visual_boundary_alignment` evidence fields.

False-positive boundary reporting is conservative. It never removes or rewrites boundaries. It flags likely review targets when transition support is isolated, weak, or contradicted by continuity evidence.

Consensus interpretations distinguish true transitions, weak transitions, incoherent drift, intentional rhetorical drift, unresolved argument chains, delayed rhetorical payoff, exploratory tangent, recovered continuity, rhetorical continuation despite topic shift, topic continuation despite acoustic shift, and boundaries needing human review. These labels are deterministic review aids, not edit commands.

## Release Readiness

Release readiness now includes:

- modality agreement quality
- segmentation confidence
- evidence stability
- revision evidence quality
- false-positive boundary penalties
- weak-evidence penalties
- topic continuity score
- rhetorical coherence score
- boundary diagnostic quality
- discourse continuity
- argument completeness
- callback resolution quality
- narrative persistence
- ambiguity-adjusted continuity
- unresolved discourse pressure
- contradiction cluster pressure
- visual continuity quality
- visual boundary alignment quality
- visual evidence completeness
- visual contradiction pressure
- visual reset support
- unsupported shift, unresolved question, and claim-without-example penalties

The report explains confidence changes through `confidence_change_explanation` and records consensus inputs so a reviewer can see why readiness moved.

## Recommendations

Recommendations are enriched with:

- consensus backing
- modality agreement strength
- conflicting evidence warnings
- continuity impact
- false-positive risk
- confidence downgrade reasons
- discourse state, argument-chain, callback, ambiguity, and continuity-decomposition evidence
- visual evidence, affected boundary IDs, visual review actions, and limitations

Recommendations remain proposal-only editorial review notes. They do not apply edits or mutate media.

Discourse, argument, callback, and ambiguity outputs are deterministic editorial-review heuristics intended to improve explainability and human review. They are not semantic truth guarantees, intent detection systems, or autonomous editorial decisions.

## Formal Schemas

Revision and consensus validation runs automatically and writes:

- `verification_evidence/revision_schema_validation.json`
- `verification_evidence/consensus_validation.json`

Schemas validate required fields and enum values. Additional deterministic integrity checks validate ID patterns, lineage consistency, candidate status consistency, mutation safety enums, release readiness enums, consensus classes, and transition confidence classes.

## Limitations

- Topic continuity is surface-term and TF-IDF based; it is not embedding semantics.
- Rhetorical continuity is marker based; it is not intent detection.
- Acoustic continuity is waveform-energy based; it is not emotion detection.
- Visual continuity is pixel/color/edge based; it is not object recognition, identity detection, emotion recognition, or cinematic intent analysis.
- Emotional arc signals are lexical and pacing heuristics; they are not psychological claims.
- Consensus can improve review prioritization but cannot guarantee editorial truth.
# Integrity Inputs

Evidence consensus remains deterministic evidence fusion. Phase 14 adds downstream integrity checks that validate whether consensus references remain resolvable across segments, transitions, reports, dashboards, and revision artifacts.
