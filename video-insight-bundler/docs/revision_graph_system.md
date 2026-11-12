# Revision Graph System

## Longitudinal Readiness Inputs

Release readiness now receives conservative longitudinal inputs after run-history writing: historical stability, confidence volatility, recurring issue pressure, persistent contradiction pressure, chronic weak-boundary pressure, longitudinal recommendation stability, and anomaly clustering pressure.

These inputs do not inflate readiness automatically. Stable repeated runs can only improve confidence indirectly and conservatively, while volatility, persistent issues, and anomaly pressure can hold readiness down or add a blocking issue.

Longitudinal and semantic-evolution outputs are deterministic historical-analysis heuristics intended for editorial review and system explainability. They are not semantic truth systems, predictive systems, or autonomous editorial agents.

The revision graph system records the completed analysis as an immutable observed revision and generates deterministic proposal-only editorial branches. It is local-first and artifact-based.

Revision graph outputs are planning and simulation artifacts. They do not apply edits, mutate media, change Resolve timelines, or guarantee publication readiness. They are deterministic decision-support artifacts for human review.

## Model

Each revision state includes a deterministic `revision_id`, parent/root IDs, status, type, source video SHA-256, analysis profile hash, input artifact hashes, proposed changes, simulated outputs, score summary, constraint summary, release readiness, mutation safety, warnings, and limitations.

Allowed statuses are:

- `observed`
- `proposed`
- `simulated`
- `applied_external`
- `rejected`
- `superseded`

This implementation writes one `observed` root state and simulated candidate states. It does not mark any branch as production-applied.

## Deterministic IDs

Revision IDs use `REV_<short sha256>`. Candidate IDs use `CAND_<short sha256>`. Seeds include stable inputs such as source video SHA, analysis profile hash, parent revision ID, candidate change set, and relevant artifact hashes. Timestamps are metadata only and do not affect identity.

## Candidates

The first generation contains:

- `Candidate_A_Minimal`: metadata/recommendation-only planning branch with no timing or render requirement.
- `Candidate_B_Conservative`: moderate human-review branch for segments, signposts, and constraints.
- `Candidate_C_Highest_Readiness`: stronger simulated branch that may score higher but carries identity, render, and reinsertion risk.
- `Candidate_D_No_Change`: baseline comparison branch.
- `Candidate_E_Visual_Reset_Review`: human-review-only visual reset planning branch for visually unsupported rhetorical boundaries or visual-only jumps.
- `Candidate_F_Rerender_Required_Visual_Intervention`: explicitly separated future visual-intervention branch that would require external rendering and reinsertion safeguards.

Candidates distinguish proposed changes from simulated revision states. All candidates remain unapplied.

## Deltas

`revision_deltas.json` separates:

- metadata changes
- recommendation changes
- timing changes
- media changes
- visualization/reporting changes
- analysis-only changes
- visual reset suggestions
- human-review-only visual issues
- rerender-required visual interventions

Each delta records affected segments, artifacts, metrics, score deltas, release readiness deltas, mutation safety deltas, identity preservation deltas, review requirement, and rollback complexity.

## Constraints

The constraint engine evaluates:

- `max_questionable_boundary_ratio`
- `min_transcript_quality`
- `min_recommendation_confidence`
- `max_topic_drift_score`
- `min_rhetorical_balance_score`
- `max_silence_ratio`
- `max_pacing_variability`
- `min_emotional_continuity`
- `min_segmentation_smoothness`
- `max_identity_change_risk`
- `minimum_consensus_score`
- `max_false_positive_boundary_ratio`
- `min_modality_agreement`
- `min_transition_confidence`
- `max_evidence_instability`
- `no_unlabeled_mutation`
- `no_render_required_for_minimal_candidate`
- `no_timing_change_without_explicit_flag`

Each constraint reports current value, threshold, direction, status, pressure score, affected artifacts, and evidence.

## Release Readiness

Release readiness is a conservative 0-1 heuristic over:

- transcript quality
- segmentation smoothness
- acoustic completeness
- topic continuity
- rhetorical balance
- rhetorical coherence score
- boundary diagnostic quality
- unsupported shift penalty
- unresolved question penalty
- claim-without-example penalty
- recommendation confidence
- warning severity
- constraint pass rate
- mutation safety
- identity preservation
- modality agreement quality
- segmentation confidence
- evidence stability
- revision evidence quality
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

Classes are `not_ready`, `review_ready`, `dry_run_ready`, and `release_candidate`. The score is not publication approval.

The readiness report includes `confidence_change_explanation` and `consensus_inputs` so reviewers can see why confidence changed after consensus, continuity, rhetorical coherence, discourse pressure, argument completeness, callback quality, ambiguity-adjusted continuity, boundary diagnostics, false-positive boundary, contradiction clustering, and evidence-strength penalties were applied. These scores are intentionally conservative and should not be interpreted as publication approval.

## Formal Schemas

Revision and consensus artifacts are validated automatically against schemas under `schemas/` and deterministic custom integrity checks. Reports are written to:

- `verification_evidence/revision_schema_validation.json`
- `verification_evidence/consensus_validation.json`

Validation covers required fields, enum values, deterministic ID patterns, branch references, revision lineage consistency, candidate status consistency, mutation safety enums, release readiness enums, consensus class enums, and transition confidence class enums.

## Mutation Safety

Mutation classes are:

- `SAFE_ANALYSIS_ONLY`
- `SAFE_METADATA_ONLY`
- `SAFE_REPORT_ONLY`
- `REQUIRES_HUMAN_REVIEW`
- `REQUIRES_RERENDER`
- `REQUIRES_REINSERTION`
- `REQUIRES_TIMELINE_MUTATION`
- `UNSAFE_WITHOUT_BACKUP`

The contract lists allowed operations, forbidden operations, required preconditions, rollback requirements, and evidence required before any future external application.

## Branch Comparison

Branch comparison scores baseline and candidates on readiness, transcript confidence, segmentation quality, topic continuity, rhetorical balance, acoustic stability, recommendation confidence, identity preservation, mutation safety, human review burden, and rollback complexity. The recommended branch balances score against risk; more aggressive branches may be rejected even when their predicted readiness is higher.

## Limitations And Non-Claims

- No edits are applied.
- No source or rendered media is mutated.
- No Resolve timeline is read or changed.
- No cloud APIs or LLM calls are used.
- Visual candidates are proposal-only. Any actual visual reset, insert, or replacement would require external human approval, backups, rerender/reinsertion safeguards, and tools outside this analyzer.
- Visual structure outputs are deterministic pixel/color/edge-level evidence summaries for editorial review. They are not object recognition, identity detection, emotion recognition, or cinematic intent claims.
- Readiness and deltas are deterministic heuristics for planning.
- Human review is required before any editorial application outside this tool.
- Consensus outputs are deterministic evidence-fusion heuristics intended to improve explainability and editorial review. They are not semantic truth guarantees or autonomous editorial decisions.
- Discourse, argument, callback, and ambiguity outputs are deterministic editorial-review heuristics intended to improve explainability and human review. They are not semantic truth guarantees, intent detection systems, or autonomous editorial decisions.

## Future Extension Path

The lineage file supports multi-generation branches. Future passes can add configurable visual candidate generators, stricter output schemas, and explicit externally-applied revision import without changing the local-first artifact model.
# Integrity Coupling

Release readiness now incorporates structural integrity scores from artifact integrity, graph consistency, reference validation, lineage validation, and dashboard coverage. The revision graph remains proposal-only and non-mutating; integrity failures can downgrade readiness but never apply edits.

# Phase 19-22A Coupling

Recommendation dependency awareness, proposal-only revision propagation estimates, counterfactual simulation summaries, forecast uncertainty, and revision conflict awareness are generated under `sequence/` and copied into revision graph context when available. They never apply edits or mutate media.
