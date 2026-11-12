"""Corpus discovery and index generation for local analysis folders."""

from __future__ import annotations

from pathlib import Path

from intelligence_common import avg, base_artifact, deterministic_id, load_analysis_folder, read_json
from stability import STATUS_COMPLETE, write_json

SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".m4v", ".avi", ".webm"}


def is_analysis_dir(path: Path) -> bool:
    return path.is_dir() and path.name.endswith("_analysis")


def safe_video_output_dir(video_path: Path) -> Path:
    invalid = '<>:"/\\|?*'
    safe_name = "".join(ch if (ch not in invalid and ord(ch) >= 32) else "_" for ch in video_path.stem).strip(" .") or "video"
    return video_path.parent / f"{safe_name}_analysis"


def discover_videos(corpus_dir: Path, includes: list[Path] | None = None) -> list[Path]:
    videos = []
    if corpus_dir.exists():
        for path in sorted(corpus_dir.rglob("*"), key=lambda item: str(item).lower()):
            if any(part.endswith("_analysis") for part in path.parts):
                continue
            if path.is_file() and path.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS:
                videos.append(path.resolve())
    for include in includes or []:
        if include.exists() and include.is_file() and include.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS:
            videos.append(include.resolve())
    return sorted(dict.fromkeys(videos), key=lambda item: str(item).lower())


def build_corpus_index(corpus_output_dir: Path, analysis_dirs: list[Path], run_manifest: dict | None = None) -> dict:
    analyses = [load_analysis_folder(path) for path in analysis_dirs if Path(path).exists()]
    items = []
    for analysis in analyses:
        manifest = analysis.get("manifest") or {}
        readiness = analysis.get("release_readiness") or {}
        sequence = analysis.get("sequence_structure") or {}
        pressure = analysis.get("editorial_pressure") or {}
        comparative = read_json(Path(analysis.get("analysis_dir")) / "comparative" / "comparative_summary.json")
        items.append(
            {
                "corpus_item_id": deterministic_id("CITEM", analysis.get("analysis_dir"), manifest.get("source_video_sha256")),
                "source_video": manifest.get("source_video"),
                "source_video_sha256": manifest.get("source_video_sha256"),
                "analysis_dir": analysis.get("analysis_dir"),
                "readiness_score": readiness.get("release_readiness_score"),
                "readiness_class": readiness.get("release_readiness_class"),
                "structural_coherence_score": (sequence.get("summary") or {}).get("structural_coherence_score"),
                "peak_pressure_score": (pressure.get("summary") or {}).get("peak_cumulative_pressure_score"),
                "warning_count": len(manifest.get("warnings") or []),
                "artifact_status": manifest.get("subsystem_statuses", {}),
                "comparative_eligible": bool(manifest.get("source_video_sha256") and Path(analysis.get("analysis_dir", "")).exists()),
                "comparative_classification": comparative.get("creator_evolution_classification"),
            }
        )
    output = base_artifact(method="deterministic_corpus_index_v1")
    output.update(
        {
            "corpus_index_id": deterministic_id("CORPUS", [row.get("source_video_sha256") for row in items]),
            "video_count": len(items),
            "analysis_folder_count": len(analysis_dirs),
            "source_video_hashes": sorted(row.get("source_video_sha256") for row in items if row.get("source_video_sha256")),
            "output_dirs": [row.get("analysis_dir") for row in items],
            "videos": items,
            "run_manifest_ref": "corpus/corpus_run_manifest.json" if run_manifest else None,
            "summary": {
                "video_count": len(items),
                "comparative_eligible_count": sum(1 for row in items if row.get("comparative_eligible")),
                "mean_readiness_score": avg([row.get("readiness_score") for row in items]),
                "mean_structural_coherence_score": avg([row.get("structural_coherence_score") for row in items]),
                "mean_peak_pressure_score": avg([row.get("peak_pressure_score") for row in items]),
            },
        }
    )
    write_json(corpus_output_dir / "corpus" / "corpus_index.json", output)
    return output
