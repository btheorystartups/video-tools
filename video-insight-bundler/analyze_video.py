#!/usr/bin/env python3
"""Command-line entry point for the standalone Video Insight Bundler."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from audio_extract import extract_audio
from audio_features import analyze_audio_features
from acoustic_features import analyze_acoustic_features
from bundle_writer import AnalysisBundle, write_bundle
from dependency_diagnostics import build_dependency_report, write_dependency_report
from emotional_arc import build_emotional_arc
from media_probe import probe_media
from multi_video_analysis import write_comparative_outputs
from persona_classifier import classify_persona_style, classify_teaching_style, load_taxonomy
from portable_export_package import build_portable_package
from recommendation_engine import build_recommendation_outputs
from revision_graph import load_revision_profile
from rhetorical_analysis import analyze_rhetoric
from rhetorical_coherence import analyze_rhetorical_coherence
from segmenter import build_segments
from stability import STATUS_COMPLETE, STATUS_SKIPPED, hash_profile, utc_now_iso, warning, write_json
from transcript_import import import_transcript
from transcription import transcribe_audio, write_srt
from topic_analysis import analyze_topics
from topic_continuity import analyze_topic_continuity
from visual_sampler import sample_frames

MANAGED_ARTIFACT_FILES = {
    "manifest.json",
    "dependency_report.json",
    "validation_report.json",
    "transcript.json",
    "transcript.srt",
    "audio_features.json",
    "acoustic_features.json",
    "topic_analysis.json",
    "rhetorical_analysis.json",
    "visual_sample_index.json",
    "scene_segments.json",
    "emotional_arc.json",
    "persona_style_profile.json",
    "teaching_style_profile.json",
    "recommendations.md",
    "recommendations.json",
    "llm_context_bundle.md",
    "llm_context_bundle.json",
    "analysis_index.json",
    "analysis_index.md",
    "analysis_audio.wav",
}
MANAGED_ARTIFACT_DIRS = {"charts", "frames", "verification_evidence", "visualizations", "graphs", "reports", "static_assets", "interactive", "revision_graph", "consensus", "continuity", "discourse", "visual_structure", "integrity", "longitudinal", "sequence", "comparative"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze a local video and produce a human/LLM-ready insight bundle."
    )
    parser.add_argument("--video", help="Path to the source video file.")
    parser.add_argument(
        "--output",
        default=str(Path("output") / "video_analysis"),
        help="Root output directory. A <safe-video-stem>_analysis folder is created inside it.",
    )
    parser.add_argument(
        "--profile",
        default=str(SCRIPT_DIR / "config" / "analysis_profile.default.json"),
        help="Analysis profile JSON file.",
    )
    parser.add_argument(
        "--sample-interval",
        type=float,
        default=None,
        help="Seconds between sampled frames. Overrides the profile default.",
    )
    parser.add_argument(
        "--transcribe",
        dest="transcribe",
        action="store_true",
        default=True,
        help="Extract audio and attempt local transcription. Default: enabled.",
    )
    parser.add_argument(
        "--no-transcribe",
        dest="transcribe",
        action="store_false",
        help="Skip audio extraction and transcription.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow writing into an existing per-video output directory.",
    )
    parser.add_argument(
        "--no-revision-graph",
        action="store_true",
        help="Skip deterministic editorial revision graph generation.",
    )
    parser.add_argument(
        "--revision-profile",
        default=str(SCRIPT_DIR / "config" / "revision_profile.default.json"),
        help="Revision graph profile JSON file.",
    )
    parser.add_argument(
        "--transcript-import",
        help="Use an existing transcript JSON and skip local transcription. Supports OpenAI Whisper JSON and native transcript.json.",
    )
    parser.add_argument(
        "--compare-analysis-folders",
        nargs="+",
        help="Run deterministic multi-video comparative intelligence over existing analysis folders.",
    )
    parser.add_argument(
        "--creator-evolution",
        action="store_true",
        help="Alias flag documenting that comparative outputs should include creator-evolution analysis.",
    )
    parser.add_argument(
        "--portable-export",
        action="store_true",
        help="Build a self-contained portable_review_package after generation.",
    )
    parser.add_argument(
        "--zip-export",
        action="store_true",
        help="Build portable_review_package.zip after generation. Implies --portable-export.",
    )
    parser.add_argument("--verbose", action="store_true", help="Print progress details.")
    return parser.parse_args()


def load_profile(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def video_output_dir(output_root: Path, video_path: Path) -> Path:
    invalid = '<>:"/\\|?*'
    safe_name = "".join(
        ch if (ch not in invalid and ord(ch) >= 32) else "_"
        for ch in video_path.stem
    ).strip(" .")
    safe_name = safe_name or "video"
    return output_root / f"{safe_name}_analysis"


def prepare_output_dir(output_root: Path, output_dir: Path, force: bool) -> None:
    if output_dir.exists() and not force:
        raise FileExistsError(f"Output directory already exists; use --force to reuse it: {output_dir}")
    if output_dir.resolve() == output_root.resolve():
        raise ValueError("Output directory resolved to the output root; refusing to write managed artifacts there.")

    output_dir.mkdir(parents=True, exist_ok=True)
    if force:
        for name in MANAGED_ARTIFACT_FILES:
            path = output_dir / name
            if path.exists() or path.is_symlink():
                path.unlink()
        for name in MANAGED_ARTIFACT_DIRS:
            path = output_dir / name
            if path.is_symlink() or path.is_file():
                path.unlink()
            elif path.is_dir():
                try:
                    shutil.rmtree(path)
                except PermissionError:
                    if name != "interactive":
                        raise

    (output_dir / "frames").mkdir(exist_ok=True)
    (output_dir / "charts").mkdir(exist_ok=True)
    (output_dir / "verification_evidence").mkdir(exist_ok=True)
    (output_dir / "visualizations").mkdir(exist_ok=True)
    (output_dir / "graphs").mkdir(exist_ok=True)
    (output_dir / "reports").mkdir(exist_ok=True)
    (output_dir / "consensus").mkdir(exist_ok=True)
    (output_dir / "continuity").mkdir(exist_ok=True)
    (output_dir / "discourse").mkdir(exist_ok=True)
    (output_dir / "visual_structure").mkdir(exist_ok=True)
    (output_dir / "integrity").mkdir(exist_ok=True)
    (output_dir / "history").mkdir(exist_ok=True)
    (output_dir / "longitudinal").mkdir(exist_ok=True)
    (output_dir / "sequence").mkdir(exist_ok=True)
    (output_dir / "comparative").mkdir(exist_ok=True)


def log(enabled: bool, message: str) -> None:
    if enabled:
        print(message, flush=True)


def emit_dependency_diagnostics(report: dict, transcribe_requested: bool, transcript_import: str | None) -> None:
    dependencies = report.get("dependencies", {})
    for name in ("ffprobe", "ffmpeg"):
        details = dependencies.get(name, {})
        if not details.get("available"):
            print(f"Dependency unavailable: {name}. {details.get('reason')}", file=sys.stderr)
    whisper = dependencies.get("faster_whisper", {})
    if transcribe_requested and not transcript_import and not whisper.get("available"):
        print(
            f"Dependency unavailable: faster_whisper. {whisper.get('reason')} "
            "Use --transcript-import or --no-transcribe to avoid local transcription.",
            file=sys.stderr,
        )


def collect_warnings(
    dependency_report: dict,
    audio_result: dict,
    transcript: dict,
    audio_features: dict,
    scene_segments: dict,
    visual_index: dict,
    acoustic_features: dict | None = None,
    topic_analysis: dict | None = None,
    rhetorical_analysis: dict | None = None,
    topic_continuity: dict | None = None,
    rhetorical_coherence: dict | None = None,
) -> list[dict]:
    warnings: list[dict] = []
    deps = dependency_report.get("dependencies", {})
    for name, details in deps.items():
        if not details.get("available"):
            subsystem = {"ffprobe": "media_probe", "ffmpeg": "audio_extract", "faster_whisper": "transcription"}.get(name)
            warnings.append(warning("DEPENDENCY_UNAVAILABLE", details.get("reason", f"{name} is unavailable."), "warning", subsystem))

    if audio_result.get("status") in {"unavailable", "error"}:
        warnings.append(
            warning(
                "AUDIO_EXTRACTION_UNAVAILABLE",
                audio_result.get("reason", "Audio extraction was unavailable."),
                "warning",
                "audio_extract",
            )
        )

    if transcript.get("transcription_status") != STATUS_COMPLETE:
        warnings.append(
            warning(
                "TRANSCRIPT_UNAVAILABLE",
                transcript.get("reason", "Transcript is unavailable or incomplete."),
                "warning",
                "transcription",
            )
        )

    duration = float(audio_features.get("duration_sec") or 0.0)
    word_count = int(audio_features.get("word_count") or 0)
    if duration >= 30 and word_count > 0 and word_count / max(duration / 60.0, 1e-9) < 35:
        warnings.append(
            warning(
                "LOW_TRANSCRIPT_DENSITY",
                "Transcript word density is low for the media duration.",
                "warning",
                "transcription",
            )
        )
    if duration >= 60 and word_count < 20:
        warnings.append(
            warning(
                "UNUSUALLY_SPARSE_SPEECH",
                "Very little speech was detected relative to media duration.",
                "warning",
                "transcription",
            )
        )

    if scene_segments.get("method") == "fixed_time_window_fallback":
        warnings.append(
            warning(
                "COARSE_SEGMENTATION_FALLBACK_USED",
                "Segmentation used fixed time windows because transcript timing was unavailable.",
                "warning",
                "segmentation",
            )
        )

    if visual_index.get("sampling_status") in {"unavailable", "error", "limited"}:
        warnings.append(
            warning(
                "VISUAL_SAMPLING_LIMITED",
                visual_index.get("reason", "Visual sampling did not complete cleanly."),
                "warning",
                "visual_sampling",
            )
        )

    for subsystem, data in [
        ("acoustic_analysis", acoustic_features or {}),
        ("topic_analysis", topic_analysis or {}),
        ("rhetorical_analysis", rhetorical_analysis or {}),
        ("topic_continuity", topic_continuity or {}),
        ("rhetorical_coherence", rhetorical_coherence or {}),
    ]:
        status = data.get("analysis_status")
        if status in {"unavailable", "error", "limited"}:
            warnings.append(
                warning(
                    f"{subsystem.upper()}_{str(status).upper()}",
                    data.get("reason") or "; ".join(data.get("limitations", [])[:1]) or f"{subsystem} produced limited output.",
                    "warning" if status != "error" else "error",
                    subsystem,
                )
            )

    questionable = [item for item in scene_segments.get("segments", []) if (item.get("boundary") or {}).get("questionable")]
    if questionable:
        warnings.append(
            warning(
                "QUESTIONABLE_SEGMENT_BOUNDARIES",
                f"{len(questionable)} segment boundary/boundaries were flagged for human review.",
                "info",
                "segmentation",
            )
        )

    return warnings


def main() -> int:
    start_monotonic = time.monotonic()
    start_timestamp = utc_now_iso()
    args = parse_args()
    if args.compare_analysis_folders and not args.video:
        output_root = Path(args.output).expanduser().resolve()
        output_root.mkdir(parents=True, exist_ok=True)
        analysis_dirs = [Path(item).expanduser().resolve() for item in args.compare_analysis_folders]
        missing = [str(path) for path in analysis_dirs if not path.exists()]
        if missing:
            print(f"Analysis folder(s) not found: {', '.join(missing)}", file=sys.stderr)
            return 2
        write_comparative_outputs(output_root, SCRIPT_DIR / "schemas", analysis_dirs)
        if args.portable_export or args.zip_export:
            export = build_portable_package(output_root, zip_export=args.zip_export)
            print(f"Portable package written to: {export['package_root']}")
            if export.get("zip_path"):
                print(f"Portable zip written to: {export['zip_path']}")
        print(f"Comparative intelligence bundle written to: {output_root}")
        return 0
    if not args.video:
        print("--video is required unless --compare-analysis-folders is used.", file=sys.stderr)
        return 2
    video_path = Path(args.video).expanduser().resolve()
    if not video_path.exists() or not video_path.is_file():
        print(f"Video file not found: {video_path}", file=sys.stderr)
        return 2

    profile_path = Path(args.profile).expanduser().resolve()
    if not profile_path.exists():
        print(f"Analysis profile not found: {profile_path}", file=sys.stderr)
        return 2
    profile = load_profile(profile_path)
    profile_hash = hash_profile(profile)
    revision_profile = None
    revision_profile_path = Path(args.revision_profile).expanduser().resolve()
    if not args.no_revision_graph:
        if not revision_profile_path.exists():
            print(f"Revision profile not found: {revision_profile_path}", file=sys.stderr)
            return 2
        revision_profile = load_revision_profile(revision_profile_path)
    sample_interval = args.sample_interval or float(profile.get("sample_interval_sec", 30.0))
    transcript_import_path = Path(args.transcript_import).expanduser().resolve() if args.transcript_import else None
    if transcript_import_path and not transcript_import_path.exists():
        print(f"Transcript import file not found: {transcript_import_path}", file=sys.stderr)
        return 2

    output_root = Path(args.output).expanduser().resolve()
    output_dir = video_output_dir(output_root, video_path)
    try:
        prepare_output_dir(output_root, output_dir, args.force)
    except (FileExistsError, ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    evidence_dir = output_dir / "verification_evidence"

    dependency_report = build_dependency_report()
    write_dependency_report(dependency_report, output_dir, evidence_dir)
    emit_dependency_diagnostics(dependency_report, args.transcribe, args.transcript_import)

    log(args.verbose, "Probing media with FFprobe...")
    media_metadata = probe_media(video_path, evidence_dir)

    audio_result = {
        "status": STATUS_SKIPPED,
        "reason": "--no-transcribe was supplied",
        "audio_path": None,
    }
    transcript = {
        "transcription_status": STATUS_SKIPPED,
        "reason": "--no-transcribe was supplied",
        "text": "",
        "segments": [],
    }
    if transcript_import_path:
        log(args.verbose, "Importing supplied transcript and skipping local transcription...")
        try:
            transcript = import_transcript(transcript_import_path)
            audio_result = {
                "status": STATUS_SKIPPED,
                "reason": "--transcript-import was supplied; audio extraction and local transcription were skipped.",
                "audio_path": None,
            }
        except Exception as exc:
            transcript = {
                "transcription_status": "error",
                "reason": f"Transcript import failed: {exc}",
                "text": "",
                "segments": [],
            }
    elif args.transcribe:
        log(args.verbose, "Extracting local analysis audio with FFmpeg...")
        audio_result = extract_audio(video_path, evidence_dir / "analysis_audio.wav", evidence_dir)
        if audio_result.get("status") == STATUS_COMPLETE:
            log(args.verbose, "Attempting local transcription with faster-whisper...")
            transcript = transcribe_audio(Path(audio_result["audio_path"]), profile)
        else:
            transcript = {
                "transcription_status": "unavailable",
                "reason": audio_result.get("reason", "Audio extraction failed."),
                "text": "",
                "segments": [],
            }

    log(args.verbose, "Writing transcript artifacts...")
    with (output_dir / "transcript.json").open("w", encoding="utf-8") as handle:
        json.dump(transcript, handle, indent=2, ensure_ascii=False)
    write_srt(transcript, output_dir / "transcript.srt")
    write_json(
        evidence_dir / "transcription_metadata.json",
        {
            "transcription_status": transcript.get("transcription_status"),
            "engine": transcript.get("engine"),
            "model": transcript.get("model"),
            "language": transcript.get("language"),
            "segment_count": len(transcript.get("segments") or []),
            "provenance": transcript.get("provenance"),
            "reason": transcript.get("reason"),
        },
    )

    log(args.verbose, "Analyzing audio-derived pacing features...")
    audio_features = analyze_audio_features(transcript, media_metadata, audio_result)
    with (output_dir / "audio_features.json").open("w", encoding="utf-8") as handle:
        json.dump(audio_features, handle, indent=2, ensure_ascii=False)

    log(args.verbose, "Sampling visual frames...")
    visual_index = sample_frames(video_path, output_dir / "frames", media_metadata, sample_interval, profile_hash, evidence_dir)
    with (output_dir / "visual_sample_index.json").open("w", encoding="utf-8") as handle:
        json.dump(visual_index, handle, indent=2, ensure_ascii=False)

    log(args.verbose, "Building scene/segment structure...")
    segments = build_segments(transcript, media_metadata, audio_features, profile, profile_hash)
    with (output_dir / "scene_segments.json").open("w", encoding="utf-8") as handle:
        json.dump(segments, handle, indent=2, ensure_ascii=False)

    log(args.verbose, "Analyzing local acoustic energy and rhythm evidence...")
    acoustic_features = analyze_acoustic_features(audio_result, segments, media_metadata)
    with (output_dir / "acoustic_features.json").open("w", encoding="utf-8") as handle:
        json.dump(acoustic_features, handle, indent=2, ensure_ascii=False)

    log(args.verbose, "Analyzing deterministic transcript topics...")
    topic_analysis = analyze_topics(transcript, segments)
    with (output_dir / "topic_analysis.json").open("w", encoding="utf-8") as handle:
        json.dump(topic_analysis, handle, indent=2, ensure_ascii=False)

    log(args.verbose, "Analyzing rhetorical markers and modes...")
    rhetorical_analysis = analyze_rhetoric(transcript, segments)
    with (output_dir / "rhetorical_analysis.json").open("w", encoding="utf-8") as handle:
        json.dump(rhetorical_analysis, handle, indent=2, ensure_ascii=False)

    log(args.verbose, "Analyzing deterministic topic continuity and rhetorical coherence...")
    topic_continuity = analyze_topic_continuity(transcript, segments, topic_analysis)
    rhetorical_coherence = analyze_rhetorical_coherence(transcript, segments, rhetorical_analysis)
    continuity_dir = output_dir / "continuity"
    with (continuity_dir / "topic_continuity.json").open("w", encoding="utf-8") as handle:
        json.dump(topic_continuity, handle, indent=2, ensure_ascii=False)
    with (continuity_dir / "rhetorical_coherence.json").open("w", encoding="utf-8") as handle:
        json.dump(rhetorical_coherence, handle, indent=2, ensure_ascii=False)

    topic_analysis["topic_continuity_score"] = topic_continuity.get("topic_continuity_score")
    topic_analysis["unsupported_topic_shifts"] = topic_continuity.get("unsupported_topic_shifts", [])
    topic_analysis["topic_drift_explanation"] = topic_continuity.get("topic_drift_explanation")
    rhetorical_analysis["rhetorical_coherence_score"] = rhetorical_coherence.get("rhetorical_coherence_score")
    rhetorical_analysis["unresolved_questions"] = rhetorical_coherence.get("unresolved_questions", [])
    rhetorical_analysis["claims_without_examples"] = rhetorical_coherence.get("claims_without_examples", [])
    with (output_dir / "topic_analysis.json").open("w", encoding="utf-8") as handle:
        json.dump(topic_analysis, handle, indent=2, ensure_ascii=False)
    with (output_dir / "rhetorical_analysis.json").open("w", encoding="utf-8") as handle:
        json.dump(rhetorical_analysis, handle, indent=2, ensure_ascii=False)

    log(args.verbose, "Building transparent heuristic emotional arc...")
    emotional_arc = build_emotional_arc(segments, transcript, audio_features, media_metadata.get("sha256"), profile_hash)
    with (output_dir / "emotional_arc.json").open("w", encoding="utf-8") as handle:
        json.dump(emotional_arc, handle, indent=2, ensure_ascii=False)

    log(args.verbose, "Classifying communication persona and teaching style...")
    persona_taxonomy = load_taxonomy(SCRIPT_DIR / "config" / "persona_taxonomy.json")
    style_taxonomy = load_taxonomy(SCRIPT_DIR / "config" / "style_taxonomy.json")
    persona_profile = classify_persona_style(segments, transcript, audio_features, emotional_arc, persona_taxonomy)
    teaching_profile = classify_teaching_style(segments, transcript, audio_features, style_taxonomy)
    with (output_dir / "persona_style_profile.json").open("w", encoding="utf-8") as handle:
        json.dump(persona_profile, handle, indent=2, ensure_ascii=False)
    with (output_dir / "teaching_style_profile.json").open("w", encoding="utf-8") as handle:
        json.dump(teaching_profile, handle, indent=2, ensure_ascii=False)

    warnings = collect_warnings(dependency_report, audio_result, transcript, audio_features, segments, visual_index, acoustic_features, topic_analysis, rhetorical_analysis, topic_continuity, rhetorical_coherence)

    log(args.verbose, "Writing recommendations and LLM bundle...")
    recommendation_outputs = build_recommendation_outputs(
        media_metadata,
        transcript,
        audio_features,
        segments,
        emotional_arc,
        persona_profile,
        teaching_profile,
        acoustic_features,
        topic_analysis,
        rhetorical_analysis,
        topic_continuity,
        rhetorical_coherence,
    )
    recommendations_md = recommendation_outputs["markdown"]
    (output_dir / "recommendations.md").write_text(recommendations_md, encoding="utf-8")
    with (output_dir / "recommendations.json").open("w", encoding="utf-8") as handle:
        json.dump({k: v for k, v in recommendation_outputs.items() if k != "markdown"}, handle, indent=2, ensure_ascii=False)

    bundle = AnalysisBundle(
        source_video=str(video_path),
        output_dir=output_dir,
        media_metadata=media_metadata,
        audio_result=audio_result,
        transcript=transcript,
        audio_features=audio_features,
        visual_index=visual_index,
        scene_segments=segments,
        emotional_arc=emotional_arc,
        persona_profile=persona_profile,
        teaching_profile=teaching_profile,
        recommendations_md=recommendations_md,
        profile=profile,
        profile_path=str(profile_path),
        profile_hash=profile_hash,
        dependency_report=dependency_report,
        warnings=warnings,
        start_timestamp_utc=start_timestamp,
        execution_duration_sec=time.monotonic() - start_monotonic,
        schema_path=SCRIPT_DIR / "schemas" / "video_analysis_bundle.schema.json",
        evidence_dir=evidence_dir,
        acoustic_features=acoustic_features,
        topic_analysis=topic_analysis,
        rhetorical_analysis=rhetorical_analysis,
        topic_continuity=topic_continuity,
        rhetorical_coherence=rhetorical_coherence,
        recommendations_json={k: v for k, v in recommendation_outputs.items() if k != "markdown"},
        enable_revision_graph=not args.no_revision_graph,
        revision_profile=revision_profile,
        revision_profile_path=str(revision_profile_path),
    )
    write_bundle(bundle)
    if args.portable_export or args.zip_export:
        log(args.verbose, "Building portable review package...")
        export = build_portable_package(output_dir, zip_export=args.zip_export)
        print(f"Portable package written to: {export['package_root']}")
        if export.get("zip_path"):
            print(f"Portable zip written to: {export['zip_path']}")

    print(f"Video analysis bundle written to: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
