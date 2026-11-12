"""Shared deterministic helpers for sequence and comparative intelligence."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from stability import STATUS_COMPLETE, STATUS_LIMITED, deterministic_id, utc_now_iso, write_json

try:  # pragma: no cover - optional plotting dependency
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover
    plt = None


THEME = {
    "bg": "#f7f7f4",
    "ink": "#242424",
    "grid": "#d8d8d2",
    "blue": "#386b8f",
    "green": "#5d7f62",
    "red": "#9c4f45",
    "gold": "#a7783a",
    "violet": "#6d668c",
}


LIMITATION_TEXT = (
    "Temporal, propagation, comparative, fingerprint, and semantic-equivalence-scaffolding outputs are "
    "deterministic editorial-analysis heuristics intended for explainability and human review. They are not "
    "semantic truth systems, identity-recognition systems, predictive systems, or autonomous editorial agents."
)


def clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 3)


def num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        value = float(value)
        if not math.isfinite(value):
            return default
        return value
    except (TypeError, ValueError):
        return default


def avg(values: list[float]) -> float:
    clean = [num(value) for value in values if value is not None]
    return round(mean(clean), 3) if clean else 0.0


def distribution(values: list[float]) -> dict:
    clean = [num(value) for value in values if value is not None]
    if not clean:
        return {"count": 0, "min": None, "max": None, "mean": None, "stddev": None}
    return {
        "count": len(clean),
        "min": round(min(clean), 3),
        "max": round(max(clean), 3),
        "mean": round(mean(clean), 3),
        "stddev": round(pstdev(clean), 3) if len(clean) > 1 else 0.0,
    }


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def sorted_segments(scene_segments: dict) -> list[dict]:
    return sorted(scene_segments.get("segments") or [], key=lambda row: (num(row.get("start_sec")), row.get("segment_id") or ""))


def segment_center(segment: dict) -> float:
    return round((num(segment.get("start_sec")) + num(segment.get("end_sec"))) / 2.0, 3)


def segment_rate(segment: dict) -> float:
    return num(segment.get("speech_rate_wpm") or segment.get("words_per_minute"))


def transition_pairs(segments: list[dict]) -> list[tuple[dict, dict]]:
    return list(zip(segments, segments[1:]))


def index_by_pair(rows: list[dict], left: str = "from_segment_id", right: str = "to_segment_id") -> dict[tuple[str, str], dict]:
    return {(row.get(left), row.get(right)): row for row in rows}


def marker_counts(segments: list[dict]) -> Counter:
    counts: Counter = Counter()
    for segment in segments:
        counts.update(segment.get("topic_markers") or [])
    return counts


def recommendation_rows(bundle_or_root) -> list[dict]:
    if isinstance(bundle_or_root, Path):
        data = read_json(bundle_or_root / "recommendations.json")
    else:
        data = getattr(bundle_or_root, "recommendations_json", None) or {}
    return data.get("recommendations") or []


def graph_setup(title: str, xlabel: str = "", ylabel: str = ""):
    fig, ax = plt.subplots(figsize=(11, 5.8), dpi=140)
    fig.patch.set_facecolor(THEME["bg"])
    ax.set_facecolor(THEME["bg"])
    ax.grid(True, color=THEME["grid"], linewidth=0.7, alpha=0.75)
    ax.set_title(title, loc="left", fontsize=14, color=THEME["ink"], pad=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    return fig, ax


def placeholder_png(path: Path, title: str, message: str) -> None:
    path.parent.mkdir(exist_ok=True)
    if plt:
        fig, ax = graph_setup(title)
        ax.text(0.5, 0.5, message, ha="center", va="center", wrap=True)
        ax.set_xticks([])
        ax.set_yticks([])
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
        return
    try:
        from PIL import Image, ImageDraw
        image = Image.new("RGB", (1200, 640), THEME["bg"])
        draw = ImageDraw.Draw(image)
        draw.text((40, 40), title, fill=THEME["ink"])
        draw.text((40, 90), message[:900], fill=THEME["ink"])
        image.save(path)
    except Exception:
        # Valid 1x1 transparent PNG.
        path.write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
            b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )


def line_png(path: Path, title: str, rows: list[dict], value_key: str = "value", label_key: str = "label", ylabel: str = "Score") -> None:
    path.parent.mkdir(exist_ok=True)
    values = [num(row.get(value_key)) for row in rows if row.get(value_key) is not None]
    if not values:
        return placeholder_png(path, title, "No rows available.")
    if not plt:
        return placeholder_png(path, title, "matplotlib unavailable; placeholder graph written.")
    labels = [str(row.get(label_key) or index + 1) for index, row in enumerate(rows) if row.get(value_key) is not None]
    fig, ax = graph_setup(title, "Index", ylabel)
    ax.plot(labels, values, marker="o", linewidth=2, color=THEME["blue"])
    ax.set_ylim(0, max(1.0, max(values) * 1.1))
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def bar_png(path: Path, title: str, rows: list[tuple[str, float]], ylabel: str = "Score") -> None:
    path.parent.mkdir(exist_ok=True)
    if not rows:
        return placeholder_png(path, title, "No rows available.")
    if not plt:
        return placeholder_png(path, title, "matplotlib unavailable; placeholder graph written.")
    labels = [str(row[0])[:28] for row in rows]
    values = [num(row[1]) for row in rows]
    fig, ax = graph_setup(title, "Category", ylabel)
    ax.bar(labels, values, color=THEME["green"])
    ax.set_ylim(0, max(1.0, max(values) * 1.1))
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def matrix_png(path: Path, title: str, matrix: list[list[float]], xlabels: list[str] | None = None, ylabels: list[str] | None = None) -> None:
    path.parent.mkdir(exist_ok=True)
    if not matrix:
        return placeholder_png(path, title, "No matrix rows available.")
    if not plt:
        return placeholder_png(path, title, "matplotlib unavailable; placeholder graph written.")
    fig, ax = graph_setup(title)
    image = ax.imshow(matrix, cmap="YlOrRd", aspect="auto", vmin=0, vmax=max(1.0, max(max(row) for row in matrix if row)))
    if xlabels:
        ax.set_xticks(range(len(xlabels)), [label[:18] for label in xlabels], rotation=35, ha="right")
    if ylabels:
        ax.set_yticks(range(len(ylabels)), [label[:18] for label in ylabels])
    fig.colorbar(image, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def write_simple_html(path: Path, title: str, section: str, graph: str, data: dict, links: list[tuple[str, str]]) -> None:
    safe_json = json.dumps(data, indent=2, ensure_ascii=False).replace("&", "&amp;").replace("<", "&lt;")
    nav = "".join(f"<a href='{href}'>{label}</a>" for label, href in links)
    path.write_text(
        f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><link rel="stylesheet" href="../static_assets/report.css"></head>
<body><aside class="sidebar"><div class="brand">Video Insight Bundler</div><nav><a href="dashboard.html">Dashboard</a>{nav}</nav></aside>
<main class="main"><header class="page-header"><p>{section}</p><h1>{title}</h1></header>
<figure class="graph"><img src="../graphs/{graph}" alt="{title}"></figure><section class="panel"><pre>{safe_json}</pre></section></main></body></html>
""",
        encoding="utf-8",
    )


def write_report(path: Path, title: str, data: dict, summary: dict | None = None) -> None:
    lines = [
        f"# {title}",
        "",
        LIMITATION_TEXT,
        "",
        f"- Status: `{data.get('analysis_status')}`",
        f"- Method: `{data.get('method')}`",
    ]
    for key, value in (summary or data.get("summary") or {}).items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in data.get("limitations", []))
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def base_artifact(status: str = STATUS_COMPLETE, method: str = "deterministic_editorial_heuristic_v1") -> dict:
    return {
        "analysis_status": status,
        "method": method,
        "generated_at_utc": utc_now_iso(),
        "limitations": [LIMITATION_TEXT],
    }


def limited_artifact(method: str, reason: str) -> dict:
    data = base_artifact(STATUS_LIMITED, method)
    data["reason"] = reason
    return data


def load_analysis_folder(path: Path) -> dict:
    return {
        "analysis_dir": str(path),
        "manifest": read_json(path / "manifest.json"),
        "scene_segments": read_json(path / "scene_segments.json"),
        "recommendations": read_json(path / "recommendations.json"),
        "sequence_structure": read_json(path / "sequence" / "sequence_structure.json"),
        "temporal_rhythm": read_json(path / "sequence" / "temporal_rhythm.json"),
        "editorial_pressure": read_json(path / "sequence" / "editorial_pressure.json"),
        "narrative_phase_model": read_json(path / "sequence" / "narrative_phase_model.json"),
        "recommendation_dependencies": read_json(path / "sequence" / "recommendation_dependencies.json"),
        "revision_propagation": read_json(path / "sequence" / "revision_propagation.json"),
        "counterfactual_simulation": read_json(path / "sequence" / "counterfactual_simulation.json"),
        "revision_forecasting": read_json(path / "sequence" / "revision_forecasting.json"),
        "epistemic_stability": read_json(path / "sequence" / "epistemic_stability.json"),
        "discourse_state": read_json(path / "discourse" / "discourse_state.json"),
        "argument_graph": read_json(path / "discourse" / "argument_graph.json"),
        "callback_resolution": read_json(path / "discourse" / "callback_resolution.json"),
        "visual_structure": read_json(path / "visual_structure" / "visual_structure.json"),
        "release_readiness": read_json(path / "revision_graph" / "release_readiness_report.json"),
        "longitudinal_summary": read_json(path / "longitudinal" / "longitudinal_summary.json"),
    }


def analysis_key(analysis: dict) -> str:
    manifest = analysis.get("manifest") or {}
    return manifest.get("source_video_sha256") or manifest.get("source_video") or analysis.get("analysis_dir") or "analysis"
