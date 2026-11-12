"""Static reports, HTML pages, and PNG graphs for revision intelligence."""

from __future__ import annotations

import html
import json
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover - optional dependency
    plt = None


THEME = {"bg": "#f7f7f4", "ink": "#242424", "blue": "#386b8f", "green": "#5d7f62", "red": "#9c4f45", "gold": "#a7783a", "violet": "#6d668c"}


def _e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _page(title: str, body: str) -> str:
    nav = "\n".join(
        f'<a href="{name}">{label}</a>'
        for name, label in [
            ("dashboard.html", "Dashboard"),
            ("revision_graph.html", "Revision Graph"),
            ("revision_comparison.html", "Branch Comparison"),
            ("release_readiness.html", "Release Readiness"),
            ("mutation_safety.html", "Mutation Safety"),
            ("editorial_evolution.html", "Editorial Evolution"),
        ]
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_e(title)}</title>
  <link rel="stylesheet" href="../static_assets/report.css">
</head>
<body>
  <aside class="sidebar"><div class="brand">Video Insight Bundler</div><nav>{nav}</nav></aside>
  <main class="main">{body}</main>
</body>
</html>
"""


def _metric(label: str, value) -> str:
    return f'<div class="metric"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'


def _link_grid(items: list[tuple[str, str]]) -> str:
    return "<div class='link-grid'>" + "".join(f"<a href='{_e(href)}'>{_e(label)}</a>" for label, href in items) + "</div>"


def _table(rows: list[dict], columns: list[str]) -> str:
    head = "".join(f"<th>{_e(column.replace('_', ' ').title())}</th>" for column in columns)
    body = ""
    for row in rows:
        body += "<tr>" + "".join(f"<td>{_e(row.get(column))}</td>" for column in columns) + "</tr>"
    empty_row = f'<tr><td colspan="{len(columns)}">No rows available.</td></tr>'
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body or empty_row}</tbody></table>"


def _setup(title: str, xlabel: str = "", ylabel: str = ""):
    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=140)
    fig.patch.set_facecolor(THEME["bg"])
    ax.set_facecolor(THEME["bg"])
    ax.set_title(title, loc="left", color=THEME["ink"])
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, color="#d8d8d2", alpha=0.7)
    return fig, ax


def _placeholder(path: Path, title: str, message: str) -> None:
    if plt:
        fig, ax = _setup(title)
        ax.text(0.5, 0.5, message, ha="center", va="center", wrap=True)
        ax.set_xticks([])
        ax.set_yticks([])
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
    else:
        path.write_text(f"{title}\n{message}\n", encoding="utf-8")


def write_revision_visualizations(output_dir: Path, revision_data: dict) -> dict:
    vis_dir = output_dir / "visualizations"
    graphs_dir = output_dir / "graphs"
    reports_dir = output_dir / "reports"
    vis_dir.mkdir(exist_ok=True)
    graphs_dir.mkdir(exist_ok=True)
    reports_dir.mkdir(exist_ok=True)

    root = revision_data["root_revision"]
    candidates = revision_data["candidates"]
    readiness = revision_data["release_readiness"]
    constraints = revision_data["constraints"]
    branch_comparison = revision_data["branch_comparison"]
    mutation_contract = revision_data["mutation_safety_contract"]

    _write_graphs(graphs_dir, root, candidates, readiness, constraints, branch_comparison, mutation_contract)
    _write_reports(reports_dir, root, candidates, readiness, constraints, branch_comparison, mutation_contract, revision_data["recommendations"])
    _write_html(vis_dir, root, candidates, readiness, constraints, branch_comparison, mutation_contract, revision_data["recommendations"])
    return {
        "status": "complete",
        "html_files": [
            "revision_graph.html",
            "revision_comparison.html",
            "release_readiness.html",
            "mutation_safety.html",
            "editorial_evolution.html",
        ],
        "graph_files": [
            "revision_score_evolution.png",
            "branch_comparison.png",
            "release_readiness_radar.png",
            "constraint_pressure.png",
            "mutation_safety_matrix.png",
            "editorial_evolution.png",
        ],
        "report_files": [
            "revision_graph_summary.md",
            "revision_graph_summary.json",
            "release_readiness_summary.md",
            "branch_comparison_summary.md",
            "mutation_safety_summary.md",
        ],
    }


def _write_graphs(graphs_dir: Path, root: dict, candidates: list[dict], readiness: dict, constraints: dict, branch_comparison: dict, mutation_contract: dict) -> None:
    names = ["Baseline"] + [row["candidate_label"].replace("Candidate_", "") for row in candidates]
    scores = [root["release_readiness"]["release_readiness_score"]] + [row["predicted_release_readiness"]["release_readiness_score"] for row in candidates]
    if not plt:
        for name in ["revision_score_evolution.png", "branch_comparison.png", "release_readiness_radar.png", "constraint_pressure.png", "mutation_safety_matrix.png", "editorial_evolution.png"]:
            _placeholder(graphs_dir / name, name, "matplotlib unavailable; placeholder written.")
        return

    fig, ax = _setup("Revision Score Evolution", "Branch", "Readiness")
    ax.plot(names, scores, marker="o", color=THEME["blue"])
    ax.set_ylim(0, 1)
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(graphs_dir / "revision_score_evolution.png")
    plt.close(fig)

    rows = branch_comparison.get("branches", [])
    fig, ax = _setup("Branch Comparison", "Score", "Branch")
    ax.barh([row["branch_label"].replace("Candidate_", "") for row in rows], [row.get("recommendation_score", 0) for row in rows], color=THEME["green"])
    ax.set_xlim(0, 1)
    fig.tight_layout()
    fig.savefig(graphs_dir / "branch_comparison.png")
    plt.close(fig)

    components = readiness.get("score_components", {})
    fig, ax = _setup("Release Readiness Components", "Metric", "Score")
    ax.bar([key.replace("_", "\n") for key in components], list(components.values()), color=THEME["violet"])
    ax.set_ylim(0, 1)
    ax.tick_params(axis="x", labelsize=7)
    fig.tight_layout()
    fig.savefig(graphs_dir / "release_readiness_radar.png")
    plt.close(fig)

    pressure_rows = sorted(constraints.get("constraints", []), key=lambda row: row.get("pressure_score", 0), reverse=True)[:12]
    fig, ax = _setup("Constraint Pressure", "Pressure", "Constraint")
    ax.barh([row["constraint_id"] for row in reversed(pressure_rows)], [row["pressure_score"] for row in reversed(pressure_rows)], color=THEME["red"])
    ax.set_xlim(0, 1)
    fig.tight_layout()
    fig.savefig(graphs_dir / "constraint_pressure.png")
    plt.close(fig)

    contract_rows = mutation_contract.get("candidate_contracts", [])
    fig, ax = _setup("Mutation Safety Matrix", "Safety", "Candidate")
    safety_values = [row.get("mutation_safety_score", 0) for row in contract_rows]
    ax.barh([row.get("candidate_label") for row in contract_rows], safety_values, color=THEME["gold"])
    ax.set_xlim(0, 1)
    fig.tight_layout()
    fig.savefig(graphs_dir / "mutation_safety_matrix.png")
    plt.close(fig)

    fig, ax = _setup("Editorial Evolution", "Branch", "Score")
    ax.plot(names, scores, marker="o", label="readiness", color=THEME["blue"])
    ax.plot(names, [1.0] + [row.get("identity_preservation_score", 1.0) for row in candidates], marker="s", label="identity", color=THEME["green"])
    ax.set_ylim(0, 1)
    ax.legend(frameon=False)
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(graphs_dir / "editorial_evolution.png")
    plt.close(fig)


def _write_reports(reports_dir: Path, root: dict, candidates: list[dict], readiness: dict, constraints: dict, branch_comparison: dict, mutation_contract: dict, recommendations: dict) -> None:
    summary = {
        "root_revision_id": root["revision_id"],
        "candidate_count": len(candidates),
        "recommended_branch": recommendations.get("recommended_branch"),
        "release_readiness_class": readiness.get("release_readiness_class"),
        "mutation_status": mutation_contract.get("overall_status"),
        "warning": "Revision graph outputs are planning and simulation artifacts. They do not apply edits, mutate media, change Resolve timelines, or guarantee publication readiness.",
    }
    _write_json(reports_dir / "revision_graph_summary.json", summary)
    (reports_dir / "revision_graph_summary.md").write_text(
        "\n".join(
            [
                "# Revision Graph Summary",
                "",
                summary["warning"],
                "",
                f"- Root revision: `{summary['root_revision_id']}`",
                f"- Candidates: `{summary['candidate_count']}`",
                f"- Recommended branch: `{summary['recommended_branch']}`",
                f"- Release readiness class: `{summary['release_readiness_class']}`",
                f"- Mutation status: `{summary['mutation_status']}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (reports_dir / "release_readiness_summary.md").write_text(
        "# Release Readiness Summary\n\n"
        f"- Score: `{readiness.get('release_readiness_score')}`\n"
        f"- Class: `{readiness.get('release_readiness_class')}`\n"
        f"- Next best action: {readiness.get('next_best_action')}\n\n"
        "This is a deterministic planning score, not publication approval.\n",
        encoding="utf-8",
    )
    (reports_dir / "branch_comparison_summary.md").write_text(
        "# Branch Comparison Summary\n\n"
        f"- Recommended branch: `{branch_comparison.get('recommended_branch', {}).get('branch_label')}`\n"
        f"- Basis: {branch_comparison.get('comparison_basis')}\n",
        encoding="utf-8",
    )
    (reports_dir / "mutation_safety_summary.md").write_text(
        "# Mutation Safety Summary\n\n"
        f"- Overall status: `{mutation_contract.get('overall_status')}`\n"
        "- All Phase 9 candidates remain proposal/simulation artifacts only.\n",
        encoding="utf-8",
    )


def _write_html(vis_dir: Path, root: dict, candidates: list[dict], readiness: dict, constraints: dict, branch_comparison: dict, mutation_contract: dict, recommendations: dict) -> None:
    graph_links = _link_grid(
        [
            ("Revision score evolution", "../graphs/revision_score_evolution.png"),
            ("Branch comparison", "../graphs/branch_comparison.png"),
            ("Readiness components", "../graphs/release_readiness_radar.png"),
            ("Constraint pressure", "../graphs/constraint_pressure.png"),
            ("Mutation safety matrix", "../graphs/mutation_safety_matrix.png"),
            ("Editorial evolution", "../graphs/editorial_evolution.png"),
        ]
    )
    candidate_rows = [
        {
            "candidate_label": row.get("candidate_label"),
            "score": row.get("predicted_release_readiness", {}).get("release_readiness_score"),
            "safety": row.get("mutation_safety_class"),
            "render_required": row.get("render_required"),
            "identity": row.get("identity_preservation_score"),
        }
        for row in candidates
    ]
    warning = "<p><strong>Planning artifact:</strong> These pages do not apply edits, mutate media, or change timelines.</p>"
    (vis_dir / "revision_graph.html").write_text(
        _page(
            "Revision Graph",
            f"<header class='page-header'><p>Revision Intelligence</p><h1>Revision Graph</h1></header>{warning}"
            f"<section class='metrics'>{_metric('Root Revision', root.get('revision_id'))}{_metric('Candidates', len(candidates))}{_metric('Recommended', recommendations.get('recommended_branch'))}</section>"
            f"<section class='panel'><h2>Candidate Branches</h2>{_table(candidate_rows, ['candidate_label', 'score', 'safety', 'render_required', 'identity'])}</section>"
            f"<section class='panel'><h2>Graphs</h2>{graph_links}</section>",
        ),
        encoding="utf-8",
    )
    (vis_dir / "revision_comparison.html").write_text(
        _page("Revision Comparison", f"<header class='page-header'><p>Branch Review</p><h1>Revision Comparison</h1></header>{warning}<section class='panel'>{_table(branch_comparison.get('branches', []), ['branch_label', 'release_readiness', 'identity_preservation', 'mutation_safety', 'human_review_burden', 'rollback_complexity', 'recommendation_score'])}</section>"),
        encoding="utf-8",
    )
    (vis_dir / "release_readiness.html").write_text(
        _page("Release Readiness", f"<header class='page-header'><p>Conservative Heuristic</p><h1>Release Readiness</h1></header>{warning}<section class='metrics'>{_metric('Score', readiness.get('release_readiness_score'))}{_metric('Class', readiness.get('release_readiness_class'))}</section><section class='panel'><h2>Components</h2>{_table([readiness.get('score_components', {})], list(readiness.get('score_components', {}).keys()))}</section><section class='panel'><h2>Next Action</h2><p>{_e(readiness.get('next_best_action'))}</p></section>"),
        encoding="utf-8",
    )
    (vis_dir / "mutation_safety.html").write_text(
        _page("Mutation Safety", f"<header class='page-header'><p>Safety Contract</p><h1>Mutation Safety</h1></header>{warning}<section class='metrics'>{_metric('Overall Status', mutation_contract.get('overall_status'))}</section><section class='panel'>{_table(mutation_contract.get('candidate_contracts', []), ['candidate_label', 'mutation_safety_class', 'mutation_safety_score', 'render_required', 'reinsertion_required'])}</section>"),
        encoding="utf-8",
    )
    (vis_dir / "editorial_evolution.html").write_text(
        _page("Editorial Evolution", f"<header class='page-header'><p>Lineage View</p><h1>Editorial Evolution</h1></header>{warning}<section class='panel'><h2>Evolution Graphs</h2>{graph_links}</section><section class='panel'><h2>Constraint Pressure</h2>{_table(constraints.get('summary', {}).get('highest_pressure_constraints', []), ['constraint_id', 'pressure_score', 'status'])}</section>"),
        encoding="utf-8",
    )
