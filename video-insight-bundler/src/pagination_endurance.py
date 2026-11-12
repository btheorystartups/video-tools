"""Deterministic pagination endurance validation."""

from __future__ import annotations

from phase46_resilience_common import phase46_artifact, render_resilience_page, stable_row_id


def build_pagination_endurance_registry(outputs: dict) -> dict:
    pages = (outputs.get("history_pagination_registry") or {}).get("pages") or []
    rows = []
    for page in pages:
        has_exit = page.get("previous_page") is not None or page.get("next_page") is not None or len(pages) == 1
        rows.append(
            {
                "pagination_endurance_id": stable_row_id("PGE", page.get("history_pagination_id"), has_exit),
                "page_number": page.get("page_number"),
                "entry_count": page.get("entry_count"),
                "previous_page": page.get("previous_page"),
                "next_page": page.get("next_page"),
                "dead_end_detected": not has_exit,
                "endurance_status": "survives" if has_exit else "dead_end",
                "human_review_required": True,
            }
        )
    artifact = phase46_artifact("deterministic_pagination_endurance_v1")
    artifact.update({"pagination_endurance_registry_id": stable_row_id("PGEREG", [row["pagination_endurance_id"] for row in rows]), "pagination_endurance_checks": rows, "summary": {"pagination_endurance_check_count": len(rows), "pagination_dead_end_count": sum(1 for row in rows if row["dead_end_detected"])}})
    return artifact


def render_pagination_endurance_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("pagination_endurance_registry") or {}).get("pagination_endurance_checks") or []
    return render_resilience_page("Pagination Endurance Dashboard", "pagination_endurance_dashboard.html", rows, ["page_number", "entry_count", "previous_page", "next_page", "endurance_status"], "pagination_endurance_id", [("Pagination checks", len(rows))])
