# Expert Dashboard System

Phase V54 extends the expert dashboard from graph clickthrough into full actual-HTML page enrichment. The dashboard now links to interpretation, validation, provenance, fallback, audit, page-family, recommendation, evidence, comparison, snapshot, and diff surfaces where present.

Graph/detail cards are no longer treated as shallow links only: V54 adds explanatory summaries, interpretation status, related recommendation counts, and explicit `Explain this graph/page` actions. Interpretation remains advisory and cannot mutate media, timelines, blockers, governance state, or readiness.

Phase V51-53 restores graph cards as explanatory navigation surfaces. Top-level dashboard cards now link into graph-specific detail pages, packet dashboards, and comparison workbenches while preserving deterministic static HTML output.

Phase V51-53B repairs the dashboard generator used by the actual user-facing per-video dashboards. Core graph cards now expose three clickable affordances: the image, the title, and an `Explain this graph` link. The links use local-file relative paths and target graph-specific pages in `visualizations/graph_ux/detail/`.

The Detailed Pages section is grouped into categories such as Core Analysis, Speech / Pacing, Acoustic, Rhetorical / Discourse, Visual, Segment / Timeline, Recommendations, Governance / Readiness, Operational / Validation, Longitudinal / Snapshot, and Comparison. Existing detail links are preserved and reorganized.

The dashboard validation step parses generated HTML and records whether graph image links, title links, detail targets, explanatory sections, limitation language, grouped detail pages, and graph-detail-index links are present. Registry-only validation is not sufficient for graph clickthrough restoration.

The dashboard remains local-first and non-mutating. It does not infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous editorial decisions.
