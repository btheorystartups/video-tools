"""Reviewer workspace registry for static portable packages."""

from __future__ import annotations

from pathlib import Path
from html import escape
from static_review_notes import notes_panel

from review_checklist_engine import build_review_checklists
from review_handoff_engine import build_review_handoff_registry
from review_progress_tracking import build_review_progress_templates
from stability import deterministic_id, utc_now_iso, write_json


def build_reviewer_workspace(package_root: Path, synthesis: dict, priorities: dict, sessions: dict | None = None, *, enabled: bool = True, checklists_enabled: bool = True, handoff_enabled: bool = True) -> dict:
    checklists = build_review_checklists(priorities, sessions) if checklists_enabled else {"checklists": []}
    handoffs = build_review_handoff_registry(synthesis, checklists) if handoff_enabled else {"handoffs": []}
    progress = build_review_progress_templates(checklists)
    workspaces = []
    for checklist in checklists.get("checklists") or []:
        workflow = checklist.get("workflow")
        workspaces.append(
            {
                "workspace_id": deterministic_id("RWORK", workflow),
                "workflow": workflow,
                "enabled": enabled,
                "workspace_link": f"review/{workflow}_workspace.html",
                "checklist_id": checklist.get("checklist_id"),
                "handoff_id": next((row.get("handoff_id") for row in handoffs.get("handoffs", []) if row.get("workflow") == workflow), None),
                "recommended_next_actions": checklist.get("follow_up_recommendations") or [],
            }
        )
        _write_workspace_page(package_root, workflow, checklist)
    registry = {"analysis_status": "complete", "method": "reviewer_workspace_v76", "generated_at_utc": utc_now_iso(), "workspaces": workspaces, "summary": {"workspace_count": len(workspaces), "enabled": enabled}}
    for rel, payload in [
        ("review_workspace_registry.json", registry),
        ("review_checklists.json", checklists),
        ("review_handoff_registry.json", handoffs),
        ("review_progress_templates.json", progress),
    ]:
        write_json(package_root / rel, payload)
        write_json(package_root / "review" / rel, payload)
    return {"review_workspace_registry": registry, "review_checklists": checklists, "review_handoff_registry": handoffs, "review_progress_templates": progress}


def _write_workspace_page(package_root: Path, workflow: str, checklist: dict) -> None:
    items = "".join(f"<li><label><input type='checkbox'> {escape(str(row.get('item')))}</label></li>" for row in checklist.get("review_complete_checklist") or [])
    html = f"<!doctype html><html><head><meta charset='utf-8'><title>{workflow.title()} Workspace</title></head><body><main><p><a href='../index.html'>Index</a></p><h1>{workflow.title()} Workspace</h1><section><h2>Checklist</h2><ul>{items}</ul></section>{notes_panel()}<section><h2>Handoff</h2><pre>Decision:\nEvidence checked:\nOpen risks:\nRecommended next action:</pre></section></main></body></html>"
    path = package_root / "review" / f"{workflow}_workspace.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
