"""Guided review session workflow registries and navigation."""

from __future__ import annotations

from pathlib import Path
from review_navigation_policy import is_analytical_review_target

from stability import deterministic_id, utc_now_iso, write_json


SESSION_DEFS = {
    "executive": ("Executive Review", "Orient leadership on state, readiness, and decisions.", "executive reviewer", ["index", "dashboard", "summary", "readiness", "recommendation"]),
    "recommendation": ("Recommendation Review", "Inspect recommendation quality, dependencies, and lineage.", "review lead", ["recommendation", "optimization", "lineage"]),
    "governance": ("Governance Review", "Check governance decisions, conflicts, validation, and adjudication.", "governance reviewer", ["governance", "conflict", "adjudication", "validation"]),
    "evidence": ("Evidence Review", "Verify supporting evidence and source traceability.", "evidence reviewer", ["evidence", "validation", "manifest"]),
    "interpretation": ("Interpretation Review", "Inspect interpretation outputs and ambiguity handling.", "interpretation reviewer", ["interpretation", "llm", "meaning", "ambiguity"]),
    "timeline": ("Timeline / Continuity Review", "Review temporal flow, continuity, and longitudinal context.", "continuity reviewer", ["continuity", "timeline", "sequence", "longitudinal"]),
    "audit": ("Audit Review", "Inspect audit, schema, manifest, and validation artifacts.", "auditor", ["audit", "validation", "schema", "integrity", "manifest"]),
    "diff": ("Diff / Regression Review", "Inspect deltas, regressions, snapshots, and replay evidence.", "regression reviewer", ["delta", "diff", "regression", "snapshot"]),
    "validation": ("Validation Review", "Inspect validation status and package integrity.", "validation reviewer", ["validation", "schema", "integrity", "manifest"]),
}


def build_review_sessions(package_root: Path, governance: dict | None, topology: dict | None) -> dict:
    rows = (governance or {}).get("dashboard_governance_registry", {}).get("dashboards", [])
    optimization = (topology or {}).get("review_path_optimization", {})
    sessions = []
    templates = []
    navigation = []
    for name, (title, purpose, audience, tokens) in SESSION_DEFS.items():
        selected = _select(rows, tokens)
        ordered = [row["package_path"] for row in selected[:12]]
        critical = [row["package_path"] for row in selected if row.get("review_priority") in {"critical", "high"}][:5]
        session_id = deterministic_id("REVSESS", name, ordered)
        session = {
            "session_id": session_id,
            "session_type": f"{name}_review_session",
            "title": title,
            "purpose": purpose,
            "intended_audience": audience,
            "ordered_steps": _ordered_steps(name, ordered),
            "required_pages": ordered[: max(1, min(6, len(ordered)))],
            "optional_pages": [row["package_path"] for row in selected[12:24]],
            "critical_artifacts": critical,
            "decision_points": _decision_points(name),
            "review_questions": _review_questions(name),
            "completion_checklist": _completion_checklist(name),
            "bookmark_targets": ordered[:5],
            "notes_template": _notes_template(title),
            "handoff_summary_template": _handoff_template(title),
            "ordered_dashboards": ordered,
            "estimated_duration_minutes": max(8, min(120, len(ordered) * 6 + len(critical) * 4)),
            "required_checkpoints": _checkpoints(name, ordered),
            "critical_findings": critical,
            "optional_deep_dives": [row["package_path"] for row in selected[12:24]],
            "progress_state": {"started": False, "current_dashboard": ordered[0] if ordered else None, "completed_dashboards": []},
            "completion_markers": [{"dashboard": path, "completed": False} for path in ordered],
            "bookmark_state": {"bookmarked_dashboards": [], "resume_dashboard": ordered[0] if ordered else optimization.get("recommended_next_dashboard")},
            "reviewer_notes_support": {"enabled": True, "storage": "downloadable_static_notes_template", "notes_artifact": f"review_notes/{name}.md"},
        }
        sessions.append(session)
        templates.append(
            {
                "template_id": deterministic_id("REVTPL", name),
                "session_type": f"{name}_review_session",
                "title": title,
                "dashboard_selection_tokens": tokens,
                "default_duration_minutes": session["estimated_duration_minutes"],
                "checkpoint_count": len(session["required_checkpoints"]),
            }
        )
        navigation.append(
            {
                "session_type": f"{name}_review_session",
                "title": title,
                "estimated_duration_minutes": session["estimated_duration_minutes"],
                "resume_review": session["bookmark_state"]["resume_dashboard"],
                "recent_dashboards": ordered[:3],
                "recommended_next_dashboard": ordered[1] if len(ordered) > 1 else session["bookmark_state"]["resume_dashboard"],
                "navigation_links": ordered,
            }
        )
    registry = {
        "analysis_status": "complete",
        "method": "review_session_registry_v65",
        "generated_at_utc": utc_now_iso(),
        "sessions": sessions,
        "summary": {"session_count": len(sessions), "guided_dashboard_count": sum(len(row["ordered_dashboards"]) for row in sessions)},
    }
    template_registry = {
        "analysis_status": "complete",
        "method": "review_session_templates_v65",
        "generated_at_utc": utc_now_iso(),
        "templates": templates,
    }
    navigation_registry = {
        "analysis_status": "complete",
        "method": "review_session_navigation_v65",
        "generated_at_utc": utc_now_iso(),
        "sessions": navigation,
        "resume_review": navigation[0]["resume_review"] if navigation else None,
        "recommended_next_dashboard": navigation[0]["recommended_next_dashboard"] if navigation else None,
    }
    step_index = {
        "analysis_status": "complete",
        "method": "review_session_step_index_v70",
        "generated_at_utc": utc_now_iso(),
        "steps": [step | {"session_id": session["session_id"], "session_type": session["session_type"]} for session in sessions for step in session["ordered_steps"]],
    }
    checklists = {
        "analysis_status": "complete",
        "method": "review_session_checklists_v70",
        "generated_at_utc": utc_now_iso(),
        "sessions": [{"session_id": row["session_id"], "session_type": row["session_type"], "completion_checklist": row["completion_checklist"]} for row in sessions],
    }
    handoff_md = "\n\n".join(f"## {row['title']}\n\n{row['handoff_summary_template']}" for row in sessions)
    for name, payload in [
        ("review_session_registry.json", registry),
        ("review_session_templates.json", template_registry),
        ("review_session_navigation.json", navigation_registry),
        ("review_session_step_index.json", step_index),
        ("review_session_checklists.json", checklists),
    ]:
        write_json(package_root / name, payload)
        write_json(package_root / "review" / name, payload)
    (package_root / "review_session_handoff_templates.md").write_text(handoff_md + "\n", encoding="utf-8")
    (package_root / "review" / "review_session_handoff_templates.md").write_text(handoff_md + "\n", encoding="utf-8")
    (package_root / "review_session_workbench.html").write_text(render_review_session_workbench(registry), encoding="utf-8")
    return {
        "review_session_registry": registry,
        "review_session_templates": template_registry,
        "review_session_navigation": navigation_registry,
        "review_session_step_index": step_index,
        "review_session_checklists": checklists,
    }


def render_review_session_index(sessions: dict) -> str:
    nav = sessions.get("review_session_navigation", {})
    rows = nav.get("sessions") or []
    if not rows:
        return "<p>Review sessions are unavailable.</p>"
    items = []
    for row in rows:
        links = "".join(f"<li><a href=\"{path}\">{path}</a></li>" for path in row.get("navigation_links", [])[:8])
        items.append(
            f"<details><summary>{row.get('title') or row['session_type'].replace('_', ' ').title()} ({row.get('estimated_duration_minutes', 0)} min)</summary>"
            f"<p class=\"meta\">Resume Review: {row.get('resume_review') or 'none'} | Recommended Next Step: {row.get('recommended_next_dashboard') or 'none'}</p>"
            f"<ol>{links}</ol></details>"
        )
    return "".join(items)


def render_review_session_workbench(registry: dict) -> str:
    cards = []
    for session in registry.get("sessions") or []:
        steps = "".join(f"<li>{step['label']}: <a href=\"{step.get('page') or '#'}\">{step.get('page') or 'notes'}</a></li>" for step in session.get("ordered_steps", [])[:8])
        cards.append(
            f"<section><h2>{session['title']}</h2><p>{session['purpose']}</p>"
            f"<p>Audience: {session['intended_audience']} | Estimated time: {session['estimated_duration_minutes']} minutes</p>"
            f"<h3>Choose Review Pathway</h3><ol>{steps}</ol>"
            f"<h3>Decision Points</h3><ul>{''.join(f'<li>{item}</li>' for item in session['decision_points'])}</ul></section>"
        )
    return "<!doctype html><html><head><meta charset=\"utf-8\"><title>Review Session Workbench</title></head><body><main><h1>Start a Guided Review</h1>" + "".join(cards) + "</main></body></html>"


def _select(rows: list[dict], tokens: list[str]) -> list[dict]:
    rows = [row for row in rows if is_analytical_review_target(row.get("package_path"))]
    selected = []
    for row in rows:
        haystack = f"{row.get('package_path')} {row.get('title')} {' '.join(row.get('tags') or [])} {row.get('category')}".lower()
        if any(token in haystack for token in tokens):
            selected.append(row)
    if not selected:
        selected = rows[:8]
    return sorted(selected, key=lambda item: (item.get("navigation_priority_score", 0), item.get("review_importance_score", 0)), reverse=True)


def _checkpoints(name: str, ordered: list[str]) -> list[dict]:
    labels = ["orientation", "critical_findings", "decision", "notes", "completion"]
    return [
        {
            "checkpoint_id": deterministic_id("CHK", name, label),
            "label": label,
            "required": label in {"orientation", "decision", "completion"},
            "dashboard": ordered[min(index, len(ordered) - 1)] if ordered else None,
            "completed": False,
        }
        for index, label in enumerate(labels)
    ]


def _ordered_steps(name: str, ordered: list[str]) -> list[dict]:
    labels = ["Orient", "Inspect Primary Evidence", "Review Risks", "Record Decision", "Prepare Handoff"]
    return [
        {
            "step_id": deterministic_id("REVSTEP", name, index, label),
            "step_number": index + 1,
            "label": label,
            "page": ordered[min(index, len(ordered) - 1)] if ordered else None,
            "required": index in {0, 1, 3, 4},
        }
        for index, label in enumerate(labels)
    ]


def _decision_points(name: str) -> list[str]:
    return [
        f"Is the {name} evidence sufficient for the next internal review?",
        "Are any blockers unresolved?",
        "What should be handed off or re-run?",
    ]


def _review_questions(name: str) -> list[str]:
    return [
        f"What changed or matters most in this {name} pathway?",
        "Which artifacts support the conclusion?",
        "Which uncertainty should be preserved in the handoff?",
    ]


def _completion_checklist(name: str) -> list[dict]:
    return [
        {"item": "Primary pages reviewed", "completed": False},
        {"item": "Critical artifacts checked", "completed": False},
        {"item": "Decision points answered", "completed": False},
        {"item": "Handoff summary prepared", "completed": False},
    ]


def _notes_template(title: str) -> str:
    return f"# {title} Notes\n\n## Observations\n\n## Decisions\n\n## Follow-ups\n"


def _handoff_template(title: str) -> str:
    return f"Summary for {title}:\n\nDecision:\nEvidence checked:\nRisks/blockers:\nRecommended next step:\n"
