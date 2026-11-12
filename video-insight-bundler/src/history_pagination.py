"""Deterministic high-density history pagination."""

from __future__ import annotations

from phase44_wayfinding_common import all_wayfinding_events, phase44_artifact, render_wayfinding_page, source_ids, stable_row_id


def build_history_pagination_registry(outputs: dict, page_size: int = 8) -> dict:
    events = all_wayfinding_events(outputs, 64)
    rows = []
    for page_index in range(0, len(events), page_size):
        page_events = events[page_index : page_index + page_size]
        rows.append(
            {
                "history_pagination_id": stable_row_id("HPG", page_index // page_size + 1, source_ids(page_events)),
                "page_number": page_index // page_size + 1,
                "page_size": page_size,
                "source_event_ids": source_ids(page_events),
                "entry_count": len(page_events),
                "previous_page": page_index // page_size if page_index else None,
                "next_page": page_index // page_size + 2 if page_index + page_size < len(events) else None,
                "human_review_required": True,
            }
        )
    artifact = phase44_artifact("deterministic_history_pagination_v1")
    artifact.update({"history_pagination_registry_id": stable_row_id("HPGREG", [row["history_pagination_id"] for row in rows]), "pages": rows, "summary": {"page_count": len(rows), "paginated_event_count": len(events), "page_size": page_size}})
    return artifact


def render_history_pagination_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("history_pagination_registry") or {}).get("pages") or []
    return render_wayfinding_page("History Pagination Dashboard", "history_pagination_dashboard.html", rows, ["page_number", "entry_count", "previous_page", "next_page"], "history_pagination_id", [("Pages", len(rows))])
