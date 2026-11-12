# Adjudication Event Ingestion

Phase 38 adds deterministic local ingestion for human adjudication events.

Generated artifacts live under `Corpus_analysis/adjudication_events/`.

The import model is append-only. Events reference existing Phase 37 conflicts and adjudication records, preserve canonical hashes, and never apply an autonomous resolution. Invalid events are recorded in validation output instead of being silently accepted.

Limitation: This system provides deterministic operational review, adjudication, and validation workflow support. It does not autonomously resolve reviewer disagreements, infer identity, diagnose emotion, predict viewer behavior, or make autonomous editorial decisions. Human review is required.
