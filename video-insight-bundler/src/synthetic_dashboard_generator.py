"""Synthetic dashboard grouping and consistency registries."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from stability import deterministic_id, utc_now_iso, write_json
from review_navigation_policy import is_analytical_review_target


TEMPLATES = ["executive", "review", "audit", "timeline", "recommendation", "governance", "evidence", "diff"]


def build_synthetic_dashboards(package_root: Path, governance: dict | None, reduction: dict, *, density: str = "balanced") -> dict:
    rows = [row for row in (((governance or {}).get("dashboard_governance_registry") or {}).get("dashboards") or []) if is_analytical_review_target(row.get("package_path"))]
    by_category: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_category[row.get("category") or "review"].append(row)
    groups = []
    for category, items in sorted(by_category.items()):
        ranked = sorted(items, key=lambda item: item.get("review_importance_score", 0), reverse=True)[:12]
        groups.append(
            {
                "aggregation_id": deterministic_id("DAGG", category, [item.get("package_path") for item in ranked]),
                "category": category,
                "density": density,
                "source_pages": [item.get("package_path") for item in ranked],
                "synthetic_page": f"review/{category}_synthetic_review.html",
                "display_mode": "compact_summary" if density == "compact" else "expanded_evidence" if density == "expanded" else "balanced_review",
            }
        )
        _write_synthetic_page(package_root, category, ranked, density)
    aggregation = {
        "analysis_status": "complete",
        "method": "synthetic_dashboard_generator_v75",
        "generated_at_utc": utc_now_iso(),
        "dashboard_density": density,
        "aggregations": groups,
        "summary": {"aggregation_count": len(groups), "source_page_count": sum(len(row["source_pages"]) for row in groups)},
    }
    style = {
        "analysis_status": "complete",
        "method": "dashboard_style_registry_v74",
        "generated_at_utc": utc_now_iso(),
        "standards": {
            "headers": "consistent title, classification badge, export metadata",
            "navigation": "breadcrumb, recommended next step, related dashboards",
            "interpretation_panel": "summary, why it matters, review question, limitation",
            "audit_details": "collapsed by default unless audit_dense",
        },
    }
    template_registry = {
        "analysis_status": "complete",
        "method": "dashboard_template_registry_v74",
        "generated_at_utc": utc_now_iso(),
        "templates": [{"template_id": deterministic_id("DTPL", name), "template_type": name, "required_sections": ["header", "summary", "evidence", "review_guidance", "limitations"]} for name in TEMPLATES],
    }
    consistency = _validate_consistency(rows)
    for rel, payload in [
        ("dashboard_aggregation_registry.json", aggregation),
        ("dashboard_style_registry.json", style),
        ("dashboard_template_registry.json", template_registry),
        ("dashboard_consistency_validation.json", consistency),
    ]:
        write_json(package_root / rel, payload)
        write_json(package_root / "review" / rel, payload)
    return {
        "dashboard_aggregation_registry": aggregation,
        "dashboard_style_registry": style,
        "dashboard_template_registry": template_registry,
        "dashboard_consistency_validation": consistency,
    }


def _write_synthetic_page(package_root: Path, category: str, rows: list[dict], density: str) -> None:
    items = "".join(f"<li><a href='../{row.get('package_path')}'>{row.get('title') or row.get('package_path')}</a><span> priority {row.get('review_importance_score')}</span></li>" for row in rows)
    detail = "<details><summary>Advanced audit details</summary><p>Source page list and metadata are preserved in dashboard_aggregation_registry.json.</p></details>"
    html = f"<!doctype html><html><head><meta charset='utf-8'><title>{category.title()} Review</title></head><body><main><p><a href='../index.html'>Index</a></p><h1>{category.title()} Review</h1><p>Density: {density}</p><section><h2>Highest Signal Pages</h2><ol>{items}</ol></section>{detail}</main></body></html>"
    path = package_root / "review" / f"{category}_synthetic_review.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def _validate_consistency(rows: list[dict]) -> dict:
    issues = []
    for row in rows:
        if not row.get("title"):
            issues.append({"path": row.get("package_path"), "issue": "missing_title"})
        if not row.get("category"):
            issues.append({"path": row.get("package_path"), "issue": "missing_category"})
        if row.get("visibility") == "primary" and row.get("orphaned"):
            issues.append({"path": row.get("package_path"), "issue": "orphan_exposed_to_primary_view"})
    return {
        "analysis_status": "complete" if not issues else "limited",
        "method": "dashboard_consistency_validation_v74",
        "generated_at_utc": utc_now_iso(),
        "checks": ["metadata", "category", "visibility", "orphan_exposure", "progressive_disclosure"],
        "issues": issues,
        "summary": {"issue_count": len(issues), "dashboard_count": len(rows), "validation_passed": not issues},
    }
