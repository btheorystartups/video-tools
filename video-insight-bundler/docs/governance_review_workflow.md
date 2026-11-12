# Governance Review Workflow

Phase 29 adds deterministic human-review workflow artifacts for Tier 1 governance review.

The workflow is:

1. Open `visualizations/corpus_dashboard.html`.
2. Use `reviewer_focus_queue.html` to inspect the shortest high-impact Tier 1 path first.
3. Use `review_navigation_index.html` and `workbench/tier_1_evidence_navigation.json` to jump from blocker family to video, segment, evidence refs, and raw review queue refs.
4. Use `reviewer_decision_support.html` to understand likely dispositions, minimum evidence, caution notes, and possible governance consequences.
5. Record evidence-backed human decisions in `review_input/reviewer_decisions.json` using the generated templates.
6. Rerun corpus analysis and inspect decision validation, reconciliation, ledger, provenance, and reassessment gatekeeper pages.

Phase 30 removes the need to edit raw governance artifacts. Incomplete or unsupported decisions are rejected into `governance/rejected_human_decisions.json` and remain audit-only.
6. Rerun corpus analysis to regenerate reassessment, delta, history, and replay artifacts.

`governance/governance_review_session.json` captures the current reviewer session state. If no reviewer decisions exist, the session remains empty but valid. The system does not invent decisions.

Governance reassessment artifacts are deterministic review and audit artifacts. They do not automatically resolve blockers, apply edits, accept risk, classify false positives, or make autonomous release decisions. Human review is required.

## Limits

The workflow is local-first and static. It does not use cloud APIs, LLM runtime calls, embeddings, vector databases, Resolve integration, servers, databases, or media/timeline mutation.
