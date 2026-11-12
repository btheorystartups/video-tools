# Topic And Rhetorical Continuity

Phase 11 adds deterministic local diagnostics for topic continuity, rhetorical coherence, and boundary review. Phase 12 adds deterministic discourse-state, argument-chain, narrative-memory, callback-resolution, ambiguity-interpretation, and continuity-decomposition evidence on top of those diagnostics.

Topic continuity and rhetorical coherence are deterministic local heuristics for editorial review. They are not semantic truth guarantees.

Discourse, argument, callback, and ambiguity outputs are deterministic editorial-review heuristics intended to improve explainability and human review. They are not semantic truth guarantees, intent detection systems, or autonomous editorial decisions.

## Scope

The continuity pass uses:

- rolling transcript windows
- TF-IDF terms when `scikit-learn` is available
- frequency/keyphrase fallback when optional libraries are unavailable
- Jaccard overlap
- cosine similarity when TF-IDF vectors are available
- repeated concept tracking
- topic bridge detection
- topic re-entry detection
- abrupt and unsupported shift flags
- marker-based rhetorical mode and support checks
- boundary-level cross-modal diagnostics
- discourse continuation evidence
- unresolved argument carryover
- callback and narrative continuity carryover
- ambiguity override and intentional tangent likelihood

It does not use embeddings, vector databases, CLIP, cloud APIs, LLM calls, databases, web servers, Resolve integration, or autonomous editing.

## Artifacts

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
- `discourse/discourse_summary.json`
- `visualizations/discourse_state.html`
- `visualizations/argument_graph.html`
- `visualizations/narrative_memory.html`
- `visualizations/callback_resolution.html`
- `visualizations/editorial_ambiguity.html`
- `verification_evidence/discourse_schema_validation.json`

## Human Review Use

Use unsupported topic shifts to find places where a bridge sentence may be needed. Use unresolved questions and claims without examples to find rhetorical gaps. Use boundary diagnostics to inspect segment boundaries where sentence continuity, topic shift, acoustic shift, pacing, or rhetorical evidence contradict each other.

Use discourse pressure to find deferred claims, pending examples, and unresolved questions that should be resolved before major transitions. Use argument completeness to distinguish unsupported claims from recovered chains. Use callback resolution to identify setups that need payoffs. Use ambiguity classes to avoid treating every low-continuity region as incoherence when callback, example, or rhetorical-pivot evidence supports an intentional detour.

The tool never rewrites boundaries, mutates media, changes timelines, calls Resolve, or applies edits.
