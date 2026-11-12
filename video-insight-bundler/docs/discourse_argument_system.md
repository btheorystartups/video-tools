# Discourse And Argument System

Phase 12 adds deterministic hierarchical discourse and argument-state modeling for editorial review.

Discourse, argument, callback, and ambiguity outputs are deterministic editorial-review heuristics intended to improve explainability and human review. They are not semantic truth guarantees, intent detection systems, or autonomous editorial decisions.

## Longitudinal Discourse Evolution

Longitudinal analysis tracks discourse evolution through retained metrics for argument completeness, callback quality, ambiguity-adjusted continuity, unresolved discourse pressure, and contradiction pressure. Persistent-pattern detection marks chronic rhetorical gaps, unresolved claims, contradiction regions, and recurring discourse patterns when repeated deterministic evidence appears across retained runs.

This remains an editorial review layer. It does not infer intent, semantic truth, or author psychology.

Longitudinal and semantic-evolution outputs are deterministic historical-analysis heuristics intended for editorial review and system explainability. They are not semantic truth systems, predictive systems, or autonomous editorial agents.

## Scope

The system tracks discourse state across segments with local, deterministic evidence:

- active, inactive, persistent, expired, and unresolved concepts
- rhetorical promises, pending examples, unresolved questions, deferred claims, callbacks, and setup/payoff pairs
- abstract and concrete framing
- audience-address, instruction, and persuasion state
- claim/support/example/contrast/counterpoint/takeaway chains
- short, medium, and long narrative memory windows
- delayed resolutions, recurring concepts, narrative returns, and resurfacing concepts
- ambiguity classes for low-continuity regions

It does not use embeddings, vector databases, semantic transformers, CLIP, cloud APIs, LLM calls, a database, a server, Resolve integration, or autonomous editing.

## Artifacts

The discourse pass writes:

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

## Continuity Decomposition

`discourse/discourse_summary.json` decomposes continuity into:

- lexical continuity
- rhetorical continuity
- argument continuity
- callback continuity
- thematic persistence
- narrative continuity
- pacing continuity
- emotional continuity
- discourse-state continuity

The summary also records contradiction-adjusted continuity, ambiguity-adjusted continuity, narrative recovery, unresolved discourse pressure, argument completeness, and callback resolution quality.

## Ambiguity Classes

Low continuity can be classified as:

- `likely_intentional_tangent`
- `rhetorical_pivot`
- `illustrative_detour`
- `unresolved_drift`
- `exploratory_abstraction`
- `callback_supported_drift`
- `unsupported_drift`

These classes preserve uncertainty. They help reviewers distinguish possible incoherent drift from rhetorical moves supported by callbacks, examples, or narrative returns.

## Downstream Effects

Boundary diagnostics now include discourse continuation evidence, unresolved argument carryover, callback carryover, narrative continuity carryover, ambiguity overrides, and intentional tangent likelihood.

Visual-boundary alignment can add visual support or visual contradiction to boundary diagnostics. A discourse boundary can now be explicitly described as visually unsupported, and a visual reset can be flagged when it lacks transcript or discourse support.

Consensus now records discourse and visual inputs and can distinguish incoherent drift, intentional rhetorical drift, unresolved argument chains, delayed rhetorical payoff, exploratory tangent, recovered continuity, transcript-only boundaries, visual-only boundaries, multimodal boundaries, discourse boundaries without visual reset, visual resets without transcript transitions, and unsupported visual jumps.

Recommendations now include segment-specific discourse guidance, such as resolving deferred claims, adding payoff for setups, bridging rhetorical pivots, converting abstract framing into examples, and reducing unresolved discourse pressure. Visual recommendations may suggest reviewing a visual reset near a discourse boundary, reviewing an unsupported visual jump, or reducing visual complexity during dense explanations.

Release readiness now includes discourse continuity, argument completeness, callback resolution quality, narrative persistence, ambiguity-adjusted continuity, unresolved discourse pressure, contradiction clustering, visual continuity quality, visual boundary alignment quality, visual evidence completeness, visual contradiction pressure, and visual reset support.

## Limitations

- Concept tracking uses lexical recurrence and marker evidence, not semantic equivalence.
- Argument chains are adjacency and marker heuristics, not factual entailment.
- Callback resolution can miss paraphrased payoffs.
- Ambiguity interpretation is not intent detection.
- Visual structure outputs are deterministic pixel/color/edge-level evidence summaries for editorial review. They are not object recognition, identity detection, emotion recognition, or cinematic intent claims.
- All outputs are proposal-only review evidence and never mutate media, timelines, revisions, or boundaries automatically.
# Graph Consistency

The argument graph is now checked by the global graph-consistency validator for duplicate node IDs, dangling edges, unresolved segment references, and graph fragmentation. These checks are structural and do not infer semantic truth.
