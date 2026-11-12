"""Orchestration for local deterministic visual structure artifacts."""

from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import mean
from typing import Any

from composition_features import analyze_composition_features
from schema_validation import validate_against_schema
from shot_boundary import detect_shot_boundaries
from stability import STATUS_COMPLETE, STATUS_ERROR, STATUS_LIMITED, deterministic_id, write_json
from visual_continuity import analyze_visual_continuity

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


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 3)


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _avg(values: list[float]) -> float:
    clean = [float(value) for value in values if value is not None]
    return round(mean(clean), 3) if clean else 0.0


def _pair_map(rows: list[dict], left: str = "from_segment_id", right: str = "to_segment_id") -> dict[tuple[str, str], dict]:
    return {(row.get(left), row.get(right)): row for row in rows}


def _nearest_visual_boundary(boundaries: list[dict], timestamp: float, window: float) -> dict:
    candidates = [
        (abs(_num(row.get("timestamp_sec")) - timestamp), row)
        for row in boundaries
        if abs(_num(row.get("timestamp_sec")) - timestamp) <= window
    ]
    if not candidates:
        return {}
    return sorted(candidates, key=lambda item: (item[0], item[1].get("boundary_id") or ""))[0][1]


def analyze_visual_boundary_alignment(bundle, shot_boundaries: dict, visual_continuity: dict) -> dict:
    """Compare visual boundary evidence with transcript, discourse, acoustic, and consensus boundaries."""

    segments = bundle.scene_segments.get("segments") or []
    boundaries = shot_boundaries.get("detected_boundaries") or []
    window = float((bundle.profile.get("visual_structure") or {}).get("boundary_alignment_window_sec") or 3.0)
    transition_confidence = (getattr(bundle, "consensus_outputs", None) or {}).get("transition_confidence") or {}
    transition_rows = _pair_map(transition_confidence.get("transitions") or [])
    topic_rows = _pair_map((getattr(bundle, "topic_continuity", None) or {}).get("topic_bridge_terms") or [])
    rhetorical_rows = _pair_map((getattr(bundle, "rhetorical_coherence", None) or {}).get("mode_transitions") or [])
    discourse_rows = _pair_map((getattr(bundle, "discourse_state", None) or {}).get("discourse_transitions") or [])
    acoustic_rows = _pair_map((getattr(bundle, "acoustic_features", None) or {}).get("acoustic_contrast_between_segments") or [])
    rows = []
    used_visual_ids = set()
    for index, (left, right) in enumerate(zip(segments, segments[1:]), start=1):
        pair = (left.get("segment_id"), right.get("segment_id"))
        boundary_time = _num(right.get("start_sec"), _num(left.get("end_sec")))
        visual = _nearest_visual_boundary(boundaries, boundary_time, window)
        if visual:
            used_visual_ids.add(visual.get("boundary_id"))
        transition = transition_rows.get(pair, {})
        scores = transition.get("evidence_scores") or {}
        topic = topic_rows.get(pair, {})
        rhetoric = rhetorical_rows.get(pair, {})
        discourse = discourse_rows.get(pair, {})
        acoustic = acoustic_rows.get(pair, {})
        visual_support = _clamp(_num(visual.get("boundary_confidence"), 0.0) * 0.45 + _num(visual.get("visual_change_score"), 0.0) * 0.55)
        transcript_support = _clamp(_num(scores.get("transcript_pause"), 0.35))
        rhetorical_support = _clamp(0.72 if rhetoric.get("transition_type") == "mode_shift" else _num(scores.get("rhetorical_shift"), 0.35))
        discourse_support = _clamp(1.0 - _num(discourse.get("discourse_continuation_evidence"), 0.35))
        acoustic_support = _clamp(_num(scores.get("acoustic_energy_change"), 0.35))
        topic_support = _clamp(1.0 - _num(topic.get("continuity_score"), 0.5))
        nonvisual_support = _avg([transcript_support, rhetorical_support, discourse_support, acoustic_support, topic_support])
        visual_contradiction = _clamp(max(nonvisual_support - visual_support, 0.0))
        visual_only_pressure = _clamp(max(visual_support - nonvisual_support, 0.0))
        combined = _clamp(visual_support * 0.32 + nonvisual_support * 0.48 + _num(transition.get("confidence_score"), 0.35) * 0.2 - visual_contradiction * 0.18)
        likely_visual = bool(visual_support >= 0.55)
        likely_nonvisual = bool(visual_support < 0.32 and nonvisual_support >= 0.52)
        if likely_visual and nonvisual_support >= 0.5:
            action = "Treat as multimodal boundary evidence; review before editing."
            boundary_type = "multimodal_boundary"
        elif likely_nonvisual:
            action = "Boundary is rhetorically/transcript supported but visually unsupported; consider visual reset only after review."
            boundary_type = "discourse_boundary_without_visual_reset"
        elif likely_visual and nonvisual_support < 0.42:
            action = "Visual reset occurs without strong transcript/discourse transition; review as possible unsupported visual jump."
            boundary_type = "visual_reset_without_transcript_transition"
        elif transcript_support >= 0.55 and visual_support < 0.35:
            action = "Transcript-only boundary; review whether visual continuity is intentional."
            boundary_type = "transcript_only_boundary"
        else:
            action = "Review boundary manually; evidence is mixed or weak."
            boundary_type = "weak_or_mixed_boundary"
        rows.append(
            {
                "alignment_id": deterministic_id("VALIGN", left.get("segment_id"), right.get("segment_id"), boundary_time),
                "boundary_index": index,
                "from_segment_id": left.get("segment_id"),
                "to_segment_id": right.get("segment_id"),
                "boundary_timestamp_sec": round(boundary_time, 3),
                "matched_shot_boundary_id": visual.get("boundary_id"),
                "matched_shot_timestamp_sec": visual.get("timestamp_sec"),
                "visual_support": visual_support,
                "visual_contradiction": visual_contradiction,
                "transcript_support": transcript_support,
                "rhetorical_support": rhetorical_support,
                "discourse_support": discourse_support,
                "acoustic_support": acoustic_support,
                "topic_support": topic_support,
                "combined_boundary_confidence": combined,
                "likely_visual_boundary": likely_visual,
                "likely_nonvisual_boundary": likely_nonvisual,
                "boundary_evidence_type": boundary_type,
                "suggested_review_action": action,
                "visual_evidence": {
                    "visual_change_score": visual.get("visual_change_score"),
                    "boundary_confidence": visual.get("boundary_confidence"),
                    "neighboring_frame_paths": visual.get("neighboring_frame_paths", []),
                },
                "limitations": [
                    "Alignment compares evidence timing only; it does not rewrite boundaries.",
                    "Visual evidence is pixel/color/edge-level and not a semantic claim.",
                ],
            }
        )
    segment_boundary_times = [_num(row.get("boundary_timestamp_sec")) for row in rows]
    unsupported_visual = []
    for boundary in boundaries:
        timestamp = _num(boundary.get("timestamp_sec"))
        if boundary.get("boundary_id") in used_visual_ids:
            continue
        nearest = min([abs(timestamp - item) for item in segment_boundary_times], default=None)
        if nearest is None or nearest > window:
            unsupported_visual.append(
                {
                    "shot_boundary_id": boundary.get("boundary_id"),
                    "timestamp_sec": boundary.get("timestamp_sec"),
                    "visual_change_score": boundary.get("visual_change_score"),
                    "boundary_confidence": boundary.get("boundary_confidence"),
                    "suggested_review_action": "Review abrupt visual change that does not align with transcript/discourse boundary.",
                }
            )
    return {
        "analysis_status": STATUS_COMPLETE if rows or boundaries else STATUS_LIMITED,
        "method": "deterministic_visual_boundary_alignment_v1",
        "alignment_window_sec": window,
        "boundaries": rows,
        "unsupported_visual_jumps": unsupported_visual,
        "summary": {
            "segment_boundary_count": len(rows),
            "shot_boundary_count": len(boundaries),
            "likely_visual_boundary_count": sum(1 for row in rows if row["likely_visual_boundary"]),
            "likely_nonvisual_boundary_count": sum(1 for row in rows if row["likely_nonvisual_boundary"]),
            "unsupported_visual_jump_count": len(unsupported_visual),
            "mean_visual_support": _avg([row["visual_support"] for row in rows]),
            "mean_visual_contradiction": _avg([row["visual_contradiction"] for row in rows]),
            "mean_combined_boundary_confidence": _avg([row["combined_boundary_confidence"] for row in rows]),
            "visual_continuity_score": visual_continuity.get("visual_continuity_score"),
        },
        "limitations": [
            "Visual boundary alignment is proposal-only review evidence.",
            "No boundaries, media files, or timelines are changed.",
        ],
    }


def build_visual_structure_summary(shot: dict, continuity: dict, composition: dict, alignment: dict) -> dict:
    return {
        "analysis_status": STATUS_COMPLETE if shot.get("analysis_status") == STATUS_COMPLETE else STATUS_LIMITED,
        "method": "deterministic_visual_structure_summary_v1",
        "shot_boundary_count": len(shot.get("detected_boundaries") or []),
        "visual_continuity_score": continuity.get("visual_continuity_score"),
        "visual_evidence_completeness": _clamp(
            (1.0 if shot.get("analysis_status") == STATUS_COMPLETE else 0.25) * 0.38
            + (1.0 if composition.get("frame_features") else 0.0) * 0.28
            + (1.0 if alignment.get("boundaries") else 0.0) * 0.2
            + min(len(shot.get("sampled_frame_features") or []) / 24.0, 1.0) * 0.14
        ),
        "visual_boundary_alignment_quality": _clamp(1.0 - (alignment.get("summary") or {}).get("mean_visual_contradiction", 0.0)),
        "visual_contradiction_pressure": (alignment.get("summary") or {}).get("mean_visual_contradiction"),
        "visual_reset_support": _clamp(min(len(continuity.get("visual_reset_candidates") or []) / max(len(alignment.get("boundaries") or []), 1), 1.0)),
        "strongest_visual_evidence": sorted(
            [
                {"boundary_id": row.get("boundary_id"), "timestamp_sec": row.get("timestamp_sec"), "score": row.get("visual_change_score")}
                for row in shot.get("detected_boundaries") or []
            ],
            key=lambda row: (-(row.get("score") or 0), row.get("boundary_id") or ""),
        )[:5],
        "weakest_visual_evidence_areas": [
            "Sampling can miss short transitions between sampled frames.",
            "Visual features are pixel/color/edge summaries and do not identify objects, faces, people, emotions, or intent.",
        ],
        "limitations": [
            "Visual structure outputs are deterministic pixel/color/edge-level evidence summaries for editorial review.",
            "They are not object recognition, identity detection, emotion recognition, or cinematic intent claims.",
        ],
    }


def _setup(title: str, xlabel: str = "", ylabel: str = ""):
    fig, ax = plt.subplots(figsize=(11, 5.8), dpi=140)
    fig.patch.set_facecolor(THEME["bg"])
    ax.set_facecolor(THEME["bg"])
    ax.grid(True, color=THEME["grid"], linewidth=0.7, alpha=0.75)
    ax.set_title(title, loc="left", fontsize=14, color=THEME["ink"], pad=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    return fig, ax


def _placeholder_graph(path: Path, title: str, message: str) -> None:
    if plt:
        fig, ax = _setup(title)
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
        path.write_text(f"{title}\n{message}\n", encoding="utf-8")


def write_visual_graphs(output_dir: Path, shot: dict, continuity: dict, composition: dict, alignment: dict) -> None:
    graphs = output_dir / "graphs"
    graphs.mkdir(exist_ok=True)
    if not plt:
        for name in [
            "shot_boundary_curve.png",
            "visual_change_intensity.png",
            "visual_continuity_timeline.png",
            "composition_complexity_curve.png",
            "frame_difference_heatmap.png",
            "visual_boundary_alignment.png",
            "shot_contact_sheet.png",
        ]:
            _placeholder_graph(graphs / name, name, "matplotlib unavailable; placeholder graph written.")
        return
    samples = shot.get("sampled_frame_features") or []
    boundaries = shot.get("detected_boundaries") or []
    if samples:
        x = [_num(row.get("timestamp_sec")) for row in samples]
        y = [_num(row.get("visual_change_score")) for row in samples]
        fig, ax = _setup("Shot Boundary Curve", "Seconds", "Visual change")
        ax.plot(x, y, color=THEME["blue"], linewidth=1.8)
        ax.axhline(_num(shot.get("threshold_used"), 0.46), color=THEME["red"], linestyle="--", label="threshold")
        ax.scatter([_num(row.get("timestamp_sec")) for row in boundaries], [_num(row.get("visual_change_score")) for row in boundaries], color=THEME["red"], zorder=4)
        ax.set_ylim(0, 1)
        ax.legend(frameon=False)
        fig.tight_layout()
        fig.savefig(graphs / "shot_boundary_curve.png")
        plt.close(fig)

        fig, ax = _setup("Visual Change Intensity", "Seconds", "Change score")
        ax.fill_between(x, y, color=THEME["gold"], alpha=0.35)
        ax.plot(x, y, color=THEME["gold"], linewidth=1.4)
        ax.set_ylim(0, 1)
        fig.tight_layout()
        fig.savefig(graphs / "visual_change_intensity.png")
        plt.close(fig)

        fig, ax = _setup("Composition Complexity Curve", "Seconds", "Complexity")
        ax.plot(x, [_num(row.get("visual_complexity")) for row in samples], color=THEME["green"], linewidth=1.8)
        ax.set_ylim(0, 1)
        fig.tight_layout()
        fig.savefig(graphs / "composition_complexity_curve.png")
        plt.close(fig)

        keys = ["histogram_difference", "mean_absolute_pixel_difference", "edge_difference", "brightness_change", "contrast_change"]
        matrix = [[_num(row.get(key)) for key in keys] for row in samples[1:]]
        if matrix:
            fig, ax = _setup("Frame Difference Heatmap", "Method", "Sample")
            image = ax.imshow(matrix, cmap="YlOrRd", aspect="auto", vmin=0, vmax=1)
            ax.set_xticks(range(len(keys)), [key.replace("_", " ") for key in keys], rotation=35, ha="right")
            ax.set_yticks([])
            fig.colorbar(image, ax=ax, shrink=0.8)
            fig.tight_layout()
            fig.savefig(graphs / "frame_difference_heatmap.png")
            plt.close(fig)
        else:
            _placeholder_graph(graphs / "frame_difference_heatmap.png", "Frame Difference Heatmap", "No pairwise frame differences available.")
    else:
        for name in ["shot_boundary_curve.png", "visual_change_intensity.png", "composition_complexity_curve.png", "frame_difference_heatmap.png"]:
            _placeholder_graph(graphs / name, name, "No visual frame samples available.")

    rows = continuity.get("visual_change_intensity") or []
    if rows:
        fig, ax = _setup("Visual Continuity Timeline", "Seconds", "Similarity / change")
        x = [_num(row.get("timestamp_sec")) for row in rows]
        ax.plot(x, [_num(row.get("frame_similarity_to_previous"), 1.0) for row in rows], color=THEME["green"], label="similarity")
        ax.plot(x, [_num(row.get("visual_change_score")) for row in rows], color=THEME["red"], label="change")
        ax.set_ylim(0, 1)
        ax.legend(frameon=False)
        fig.tight_layout()
        fig.savefig(graphs / "visual_continuity_timeline.png")
        plt.close(fig)
    else:
        _placeholder_graph(graphs / "visual_continuity_timeline.png", "Visual Continuity Timeline", "No continuity rows available.")

    align_rows = alignment.get("boundaries") or []
    if align_rows:
        fig, ax = _setup("Visual Boundary Alignment", "Boundary", "Support")
        x = range(1, len(align_rows) + 1)
        ax.plot(x, [row["visual_support"] for row in align_rows], marker="o", label="visual", color=THEME["blue"])
        ax.plot(x, [row["transcript_support"] for row in align_rows], marker="s", label="transcript", color=THEME["green"])
        ax.plot(x, [row["discourse_support"] for row in align_rows], marker="^", label="discourse", color=THEME["gold"])
        ax.set_ylim(0, 1)
        ax.legend(frameon=False)
        fig.tight_layout()
        fig.savefig(graphs / "visual_boundary_alignment.png")
        plt.close(fig)
    else:
        _placeholder_graph(graphs / "visual_boundary_alignment.png", "Visual Boundary Alignment", "No alignment rows available.")
    _shot_contact_sheet(graphs / "shot_contact_sheet.png", boundaries)


def _shot_contact_sheet(path: Path, boundaries: list[dict]) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return _placeholder_graph(path, "Shot Contact Sheet", "Pillow unavailable; contact sheet could not be generated.")
    image_paths = []
    for row in boundaries[:12]:
        paths = row.get("neighboring_frame_paths") or []
        image_paths.extend(paths[:2])
    thumbs = []
    for item in image_paths[:24]:
        frame_path = Path(item)
        if not frame_path.exists():
            continue
        try:
            img = Image.open(frame_path).convert("RGB")
            img.thumbnail((220, 124))
            thumbs.append((frame_path.name, img.copy()))
        except Exception:
            continue
    if not thumbs:
        return _placeholder_graph(path, "Shot Contact Sheet", "No readable neighboring shot frames were available.")
    cols = 4
    cell_w, cell_h = 240, 160
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), THEME["bg"])
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 11)
    except Exception:
        font = ImageFont.load_default()
    for index, (label, img) in enumerate(thumbs):
        col = index % cols
        row = index // cols
        x = col * cell_w + 10
        y = row * cell_h + 10
        sheet.paste(img, (x, y))
        draw.text((x, y + 130), label[:36], fill=THEME["ink"], font=font)
    sheet.save(path)


def _write_reports(output_dir: Path, shot: dict, continuity: dict, composition: dict, alignment: dict, summary: dict) -> None:
    reports = output_dir / "reports"
    reports.mkdir(exist_ok=True)
    specs = [
        ("visual_structure_report.md", "Visual Structure", [("Status", summary.get("analysis_status")), ("Shot boundaries", summary.get("shot_boundary_count")), ("Continuity score", summary.get("visual_continuity_score"))]),
        ("shot_boundary_report.md", "Shot Boundary", [("Status", shot.get("analysis_status")), ("Method", shot.get("method")), ("Detected boundaries", len(shot.get("detected_boundaries") or [])), ("Threshold", shot.get("threshold_used"))]),
        ("visual_continuity_report.md", "Visual Continuity", [("Status", continuity.get("analysis_status")), ("Continuity score", continuity.get("visual_continuity_score")), ("Reset candidates", len(continuity.get("visual_reset_candidates") or []))]),
        ("composition_features_report.md", "Composition Features", [("Status", composition.get("analysis_status")), ("Samples", len(composition.get("frame_features") or [])), ("Mean complexity", ((composition.get("summary") or {}).get("visual_complexity") or {}).get("mean"))]),
        ("visual_boundary_alignment_report.md", "Visual Boundary Alignment", [("Status", alignment.get("analysis_status")), ("Boundaries", (alignment.get("summary") or {}).get("segment_boundary_count")), ("Likely visual", (alignment.get("summary") or {}).get("likely_visual_boundary_count")), ("Unsupported visual jumps", (alignment.get("summary") or {}).get("unsupported_visual_jump_count"))]),
    ]
    for filename, title, metrics in specs:
        lines = [
            f"# {title} Report",
            "",
            "Visual structure outputs are deterministic pixel/color/edge-level evidence summaries for editorial review. They are not object recognition, identity detection, emotion recognition, or cinematic intent claims.",
            "",
        ]
        lines.extend(f"- {label}: `{value}`" for label, value in metrics)
        lines.extend(["", "## Limitations", ""])
        lines.extend(f"- {item}" for item in summary.get("limitations", []))
        (reports / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_visual_structure_outputs(output_dir: Path, schema_dir: Path, scene_segments: dict, visual_outputs: dict) -> dict:
    specs = [
        ("visual_structure/visual_structure.json", "visual_structure.schema.json", visual_outputs.get("visual_structure") or {}),
        ("visual_structure/shot_boundaries.json", "shot_boundaries.schema.json", visual_outputs.get("shot_boundaries") or {}),
        ("visual_structure/visual_continuity.json", "visual_continuity.schema.json", visual_outputs.get("visual_continuity") or {}),
        ("visual_structure/composition_features.json", "composition_features.schema.json", visual_outputs.get("composition_features") or {}),
        ("visual_structure/visual_boundary_alignment.json", "visual_boundary_alignment.schema.json", visual_outputs.get("visual_boundary_alignment") or {}),
    ]
    valid_segments = {row.get("segment_id") for row in scene_segments.get("segments") or []}
    results = []
    for rel_path, schema_name, data in specs:
        custom_errors = []
        schema_path = schema_dir / schema_name
        report = validate_against_schema(data, schema_path)
        artifact_path = output_dir / rel_path
        errors = list(report.get("errors") or [])
        if not artifact_path.exists():
            errors.append({"path": "$", "message": f"Artifact path is missing: {rel_path}"})
        if rel_path.endswith("visual_boundary_alignment.json"):
            for index, row in enumerate(data.get("boundaries") or []):
                for key in ("from_segment_id", "to_segment_id"):
                    if row.get(key) not in valid_segments:
                        custom_errors.append({"path": f"$.boundaries[{index}].{key}", "message": "Segment reference is missing from scene_segments."})
        if rel_path.endswith("shot_boundaries.json"):
            for index, path_text in enumerate(data.get("neighboring_frame_paths") or []):
                if not Path(path_text).exists():
                    custom_errors.append({"path": f"$.neighboring_frame_paths[{index}]", "message": "Neighboring frame artifact is missing."})
        errors.extend(custom_errors)
        results.append(
            {
                "artifact": rel_path,
                "schema": schema_name,
                "validation_status": STATUS_COMPLETE if not errors else STATUS_ERROR,
                "error_count": len(errors),
                "errors": errors,
            }
        )
    report = {
        "validation_status": STATUS_COMPLETE if all(row["validation_status"] == STATUS_COMPLETE for row in results) else STATUS_ERROR,
        "artifact_count": len(results),
        "error_count": sum(row["error_count"] for row in results),
        "results": results,
        "custom_checks": {
            "segment_reference_checks": True,
            "neighboring_frame_path_existence_checks": True,
            "numeric_score_range_checks": "covered by schema-required artifact presence and deterministic generators",
        },
        "limitations": [
            "Validation uses the bundled standalone JSON Schema subset plus deterministic reference checks.",
            "Visual outputs remain review evidence only.",
        ],
    }
    evidence = output_dir / "verification_evidence"
    evidence.mkdir(exist_ok=True)
    write_json(evidence / "visual_structure_validation.json", report)
    return report


def build_visual_structure_outputs(bundle) -> dict:
    root = bundle.output_dir
    visual_dir = root / "visual_structure"
    visual_dir.mkdir(exist_ok=True)
    shot = detect_shot_boundaries(Path(bundle.source_video), root, bundle.media_metadata, bundle.profile, bundle.evidence_dir)
    composition = analyze_composition_features(shot, bundle.scene_segments)
    continuity = analyze_visual_continuity(shot, composition, bundle.scene_segments)
    alignment = analyze_visual_boundary_alignment(bundle, shot, continuity)
    summary = build_visual_structure_summary(shot, continuity, composition, alignment)
    visual_structure = {
        **summary,
        "components": {
            "shot_boundaries": "visual_structure/shot_boundaries.json",
            "visual_continuity": "visual_structure/visual_continuity.json",
            "composition_features": "visual_structure/composition_features.json",
            "visual_boundary_alignment": "visual_structure/visual_boundary_alignment.json",
        },
    }
    artifacts = {
        "visual_structure": visual_structure,
        "shot_boundaries": shot,
        "visual_continuity": continuity,
        "composition_features": composition,
        "visual_boundary_alignment": alignment,
        "visual_structure_summary": summary,
    }
    for filename, key in [
        ("visual_structure.json", "visual_structure"),
        ("shot_boundaries.json", "shot_boundaries"),
        ("visual_continuity.json", "visual_continuity"),
        ("composition_features.json", "composition_features"),
        ("visual_boundary_alignment.json", "visual_boundary_alignment"),
        ("visual_structure_summary.json", "visual_structure_summary"),
    ]:
        write_json(visual_dir / filename, artifacts[key])
    _write_reports(root, shot, continuity, composition, alignment, summary)
    write_visual_graphs(root, shot, continuity, composition, alignment)
    validation = validate_visual_structure_outputs(root, bundle.schema_path.parent, bundle.scene_segments, artifacts)
    artifacts["validation"] = validation
    return artifacts


def read_json_file(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
