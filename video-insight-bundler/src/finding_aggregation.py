"""Finding aggregation for portable analytical review packages."""

from __future__ import annotations

from pathlib import Path

from stability import deterministic_id, utc_now_iso
from review_navigation_policy import is_analytical_review_target


SEVERITY_SCORE = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def _severity(score: int) -> str:
    if score >= 90:
        return "critical"
    if score >= 72:
        return "high"
    if score >= 45:
        return "medium"
    return "low"


def _title_from_path(path: str) -> str:
    return Path(path).stem.replace("_", " ").replace("-", " ").title()


def aggregate_findings(
    package_root: Path,
    manifest: dict,
    validation: dict,
    governance: dict | None,
    change_intelligence: dict | None = None,
) -> dict:
    dashboards = [row for row in (((governance or {}).get("dashboard_governance_registry") or {}).get("dashboards") or []) if is_analytical_review_target(row.get("package_path"))]
    findings: list[dict] = []

    validation_issues = [
        ("Broken package links", validation.get("broken_link_count", 0), "broken links block offline review flow"),
        ("Missing package assets", validation.get("missing_asset_count", 0), "missing assets reduce trust in dashboards"),
        ("Absolute live paths", validation.get("absolute_live_path_count", 0), "absolute live paths weaken portability"),
    ]
    for title, count, matter in validation_issues:
        if count:
            score = 95 if count > 3 else 82
            findings.append(
                _finding(
                    title=title,
                    score=score,
                    summary=f"{count} issue(s) were detected during portable validation.",
                    artifacts=["portable_package_validation_report.json"],
                    dashboards=["index.html"],
                    evidence=[matter],
                    recommendations=["Resolve package validation issues before broader reviewer handoff."],
                    concern="package_integrity",
                )
            )

    for row in sorted(dashboards, key=lambda item: (item.get("review_importance_score", 0), item.get("navigation_priority_score", 0)), reverse=True)[:8]:
        score = int(row.get("review_importance_score") or row.get("human_importance_score") or 0)
        if score < 55:
            continue
        category = row.get("category") or "review"
        label = "Primary review" if category == "review" else f"{category.title()} review"
        title = f"{label} focus: {row.get('title') or _title_from_path(row.get('package_path', 'dashboard'))}"
        findings.append(
            _finding(
                title=title,
                score=score,
                summary=f"This artifact ranks highly for {label.lower()} and should be inspected early.",
                artifacts=[row.get("package_path")],
                dashboards=[row.get("package_path")],
                evidence=[f"review_importance_score={row.get('review_importance_score')}", f"visibility={row.get('visibility')}"],
                recommendations=[f"Start the {label.lower()} pathway here, then follow linked evidence."],
                concern=category,
            )
        )

    for change in (change_intelligence or {}).get("meaningful_changes", [])[:5]:
        path = change.get("artifact") or change.get("path") or "package_diff_report.json"
        score = int(change.get("change_priority_score") or 70)
        findings.append(
            _finding(
                title=f"Change focus: {_title_from_path(str(path))}",
                score=score,
                summary=change.get("summary") or "A meaningful change was detected since the comparison export.",
                artifacts=[str(path), "package_diff_report.json"],
                dashboards=["index.html"],
                evidence=[change.get("change_type") or "change_intelligence"],
                recommendations=["Review this change before signing off on continuity or regression status."],
                concern="delta",
            )
        )

    if not findings:
        primary = [path for path in (manifest.get("dashboards") or manifest.get("html_pages") or []) if is_analytical_review_target(path)]
        findings.append(
            _finding(
                title="No critical package blockers detected",
                score=48,
                summary="The export has no critical validation blockers; review should focus on the ranked dashboards and recommendation evidence.",
                artifacts=["portable_package_validation_report.json"],
                dashboards=primary[:3],
                evidence=["portable_validation_clean_or_low_signal"],
                recommendations=["Proceed through the recommended review pathway and capture unresolved questions."],
                concern="orientation",
            )
        )

    findings = sorted(findings, key=lambda row: (SEVERITY_SCORE[row["severity"]], row["review_priority"], row["confidence"]), reverse=True)
    for index, finding in enumerate(findings, start=1):
        finding["rank"] = index
        finding["finding_id"] = deterministic_id("FIND", index, finding["title"], finding["supporting_artifacts"])
    return {
        "analysis_status": "complete",
        "method": "finding_aggregation_v73",
        "generated_at_utc": utc_now_iso(),
        "findings": findings,
        "summary": {
            "finding_count": len(findings),
            "critical_count": sum(1 for row in findings if row["severity"] == "critical"),
            "high_count": sum(1 for row in findings if row["severity"] == "high"),
        },
    }


def _finding(title: str, score: int, summary: str, artifacts: list[str | None], dashboards: list[str | None], evidence: list[str | None], recommendations: list[str], concern: str) -> dict:
    sev = _severity(score)
    return {
        "finding_id": "",
        "title": title,
        "severity": sev,
        "confidence": round(min(0.95, max(0.55, score / 100)), 2),
        "review_priority": min(100, max(1, score)),
        "summary": summary,
        "supporting_artifacts": [item for item in artifacts if item],
        "related_dashboards": [item for item in dashboards if item],
        "related_evidence": [item for item in evidence if item],
        "related_recommendations": recommendations,
        "human_review_questions": [
            "Is the supporting evidence sufficient for a reviewer decision?",
            "Does this finding change the recommended next action?",
            "What uncertainty should be preserved in the handoff?",
        ],
        "why_it_matters": f"This affects {concern} review quality and reviewer confidence.",
        "what_to_review_next": recommendations[0] if recommendations else "Review supporting artifacts.",
        "concern_group": concern,
    }
