# Adjudication Lineage System

Phase 38 adds event-level lineage through `adjudication_event_lineage.json`. Event lineage points back to Phase 37 adjudication lineage, event validation, and append-only history so human adjudication imports remain traceable.

Adjudication lineage connects reviewer import, reconciliation pass, detected conflict, adjudication record, consensus workflow, and final operational state.

The final operational state is recorded as unchanged and pending human resolution unless a separate explicit human process records a disposition. Existing lineage entries are not mutated or erased.

Lineage records are intended for audit review, arbitration packets, and operational traceability.
