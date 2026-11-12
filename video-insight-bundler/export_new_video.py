#!/usr/bin/env python3
"""Analyze one video and build a validated portable review package."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from corpus_runner import run_corpus
from audio_analysis_packet import build_audio_analysis_packet
from fresh_video_export_validation import validate_fresh_video_export
from portable_cleanup import clean_old_exports
from portable_export_package import build_portable_package, zip_package
from stability import utc_now_iso, write_json


def _safe_package_name(video: Path) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", video.stem).strip("._-")
    return stem[:80] or "video_analysis"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze a new video and export a portable non-video review package.")
    parser.add_argument("--video", required=True, help="Path to the source video.")
    parser.add_argument("--corpus", help="Corpus folder to use/create. Defaults to <output-root>/Corpus.")
    parser.add_argument("--output-root", help="Root for exported package folders. Defaults to the corpus parent.")
    parser.add_argument("--package-name", help="Safe package folder name. Defaults to the video filename.")
    parser.add_argument("--export-profile", default="review", choices=["minimal", "review", "audit", "full", "executive", "presentation", "investigation", "diff_only"])
    parser.add_argument("--dashboard-consolidation", default="grouped", choices=["none", "grouped", "aggressive"], help="Dashboard drilldown consolidation mode. Default grouped.")
    parser.add_argument("--fresh-analysis", action="store_true", help="Force fresh managed analysis artifacts.")
    parser.add_argument("--clean-before-export", action="store_true", help="Remove old portable packages before exporting.")
    parser.add_argument("--zip", action="store_true", help="Create a zip file.")
    parser.add_argument("--validate-export", action="store_true", default=True, help="Validate the package.")
    parser.add_argument("--validate-extracted", action="store_true", help="Validate an extracted copy of the zip.")
    parser.add_argument("--validation-tier", default="standard", choices=["quick", "standard", "strict", "extracted_full"], help="Portable validation tier. Default standard.")
    parser.add_argument("--generation-mode", default="hybrid", choices=["eager", "lazy", "hybrid"], help="Portable analytical generation mode. Default hybrid.")
    parser.add_argument("--zip-mode", default="full", choices=["full", "optimized", "delta"], help="Portable zip mode. Default full.")
    parser.add_argument("--cache-mode", default="auto", choices=["auto", "refresh", "off"], help="Portable cache mode. Default auto.")
    parser.add_argument("--topology-simplify", default="safe", choices=["none", "safe", "aggressive"], help="Topology simplification mode. Default safe.")
    parser.add_argument("--review-style", default="balanced", choices=["executive", "balanced", "audit_dense"], help="Review synthesis style. Default balanced.")
    parser.add_argument("--dashboard-density", default="balanced", choices=["compact", "balanced", "expanded"], help="Dashboard information density. Default balanced.")
    parser.add_argument("--artifact-reduction", default="balanced", choices=["conservative", "balanced", "aggressive"], help="Artifact reduction mode. Default balanced.")
    parser.add_argument("--change-summary", default="balanced", choices=["concise", "balanced", "full"], help="Change summary detail. Default balanced.")
    parser.add_argument("--review-workspace", action="store_true", help="Generate static review workspace pages.")
    parser.add_argument("--generate-review-checklists", action="store_true", help="Generate reviewer checklists.")
    parser.add_argument("--generate-handoff-summary", action="store_true", help="Generate handoff summary templates.")
    parser.add_argument("--delta-zip", action="store_true", help="Generate sidecar delta zip.")
    parser.add_argument("--base-export", help="Base package folder for delta comparison.")
    parser.add_argument("--real-video-required", action="store_true", help="Fail instead of simulating when the video is missing.")
    parser.add_argument("--simulate-if-missing", action="store_true", help="Write a dry-run plan when video is missing.")
    parser.add_argument("--dry-run-plan", action="store_true", help="Write a run plan without running analysis/export.")
    parser.add_argument("--write-run-plan", action="store_true", help="Write new_video_run_plan.json before running.")
    parser.add_argument("--open-after-export", action="store_true", help="Open index.html after export.")
    parser.add_argument("--include-raw-media", action="store_true", help="Include raw media. Default is false.")
    parser.add_argument("--simulate", action="store_true", help="Create a lightweight fixture analysis instead of running the full analyzer.")
    parser.add_argument("--extract-audio", action="store_true", help="Extract audio as an audio-analysis artifact.")
    parser.add_argument("--audio-format", default="wav", choices=["wav", "mp3", "m4a"], help="Extracted audio format. Default wav.")
    parser.add_argument("--audio-sample-rate", type=int, default=16000, choices=[16000, 22050, 44100, 48000], help="Extracted audio sample rate. Default 16000.")
    parser.add_argument("--audio-mono", action="store_true", default=True, help="Extract audio as mono. Default true.")
    parser.add_argument("--audio-output-root", help="Root folder for audio-analysis artifacts. Defaults to <output-root>/<package-name>_audio_analysis.")
    parser.add_argument("--include-audio-in-export", action="store_true", help="Include extracted audio in the dedicated audio packet.")
    parser.add_argument("--exclude-audio-from-export", action="store_true", help="Exclude extracted audio from the dedicated audio packet.")
    parser.add_argument("--audio-only-export", action="store_true", help="Build only the audio-analysis packet and skip the portable review package.")
    parser.add_argument("--audio-analysis-packet", action="store_true", help="Build a dedicated audio-analysis packet.")
    parser.add_argument("--audio-packet-zip", action="store_true", help="Zip the dedicated audio-analysis packet.")
    parser.add_argument("--audio-packet-profile", default="review", choices=["compact", "review", "full", "gpt_ready"], help="Audio packet profile. Default review.")
    parser.add_argument("--include-extracted-audio", action="store_true", help="Include extracted audio in the audio packet.")
    parser.add_argument("--exclude-extracted-audio", action="store_true", help="Exclude extracted audio from the audio packet.")
    parser.add_argument("--include-transcript", action="store_true", default=True, help="Include transcript artifacts in the audio packet.")
    parser.add_argument("--include-gpt-prompts", action="store_true", default=True, help="Include GPT-ready prompt files in the audio packet.")
    parser.add_argument("--include-audio-dashboards", action="store_true", default=True, help="Include offline audio dashboards in the audio packet.")
    return parser.parse_args(argv)


def _write_fixture_analysis(analysis_root: Path, video: Path) -> None:
    analysis_root.mkdir(parents=True, exist_ok=True)
    (analysis_root / "visualizations").mkdir(parents=True, exist_ok=True)
    (analysis_root / "graphs").mkdir(parents=True, exist_ok=True)
    (analysis_root / "reports").mkdir(parents=True, exist_ok=True)
    (analysis_root / "recommendations").mkdir(parents=True, exist_ok=True)
    (analysis_root / "verification_evidence").mkdir(parents=True, exist_ok=True)
    (analysis_root / "visualizations" / "dashboard.html").write_text(
        "<h1>Expert Summary</h1><p>Operational Interpretation</p><img src='../graphs/key_graph.png'>",
        encoding="utf-8",
    )
    (analysis_root / "graphs" / "key_graph.png").write_bytes(b"\x89PNG\r\n\x1a\nfixture")
    (analysis_root / "reports" / "executive_summary.md").write_text("# Executive Summary\n\nFixture export proof.\n", encoding="utf-8")
    write_json(analysis_root / "recommendations" / "recommendation_summary.json", {"source_video": video.name, "recommendations": []})
    write_json(
        analysis_root / "corpus_run_manifest.json",
        {"generated_at_utc": utc_now_iso(), "source_video": video.resolve().as_posix(), "requested_video": video.name, "fixture": True},
    )


def _write_console_summary(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_run_plan(args: argparse.Namespace, video: Path, output_root: Path, corpus: Path, package_name: str) -> dict:
    command = [
        "python",
        "video-insight-bundler/export_new_video.py",
        "--video",
        str(video),
        "--output-root",
        str(output_root),
        "--export-profile",
        args.export_profile,
        "--validation-tier",
        args.validation_tier,
        "--generation-mode",
        args.generation_mode,
        "--zip-mode",
        args.zip_mode,
        "--review-style",
        args.review_style,
        "--dashboard-density",
        args.dashboard_density,
        "--artifact-reduction",
        args.artifact_reduction,
        "--change-summary",
        args.change_summary,
    ]
    if args.zip:
        command.append("--zip")
    if args.audio_analysis_packet:
        command.append("--audio-analysis-packet")
    if args.audio_packet_zip:
        command.append("--audio-packet-zip")
    if args.include_extracted_audio:
        command.append("--include-extracted-audio")
    if args.validate_extracted:
        command.append("--validate-extracted")
    if args.review_workspace:
        command.append("--review-workspace")
    if args.generate_review_checklists:
        command.append("--generate-review-checklists")
    if args.generate_handoff_summary:
        command.append("--generate-handoff-summary")
    return {
        "analysis_status": "dry_run" if args.dry_run_plan else "planned",
        "method": "new_video_run_plan_v71",
        "generated_at_utc": utc_now_iso(),
        "video_path": video.as_posix(),
        "video_exists": video.exists(),
        "corpus": corpus.as_posix(),
        "output_root": output_root.as_posix(),
        "package_name": package_name,
        "commands": [" ".join(command)],
        "expected_outputs": [
            f"{package_name}_portable_review_package/index.html",
            f"{package_name}_portable_review_package/portable_package_manifest.json",
            f"{package_name}_portable_review_package/new_video_export_e2e_report.json",
            f"{package_name}_portable_review_package.zip",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    video = Path(args.video).expanduser().resolve()
    if not video.exists() or not video.is_file():
        output_root = Path(args.output_root).expanduser().resolve() if args.output_root else video.parent
        corpus = Path(args.corpus).expanduser().resolve() if args.corpus else output_root / "Corpus"
        package_name = args.package_name or _safe_package_name(video)
        plan = _build_run_plan(args, video, output_root, corpus, package_name)
        output_root.mkdir(parents=True, exist_ok=True)
        write_json(output_root / "new_video_run_plan.json", plan)
        if args.simulate_if_missing and not args.real_video_required:
            print(f"Video not found; dry-run plan written: {output_root / 'new_video_run_plan.json'}")
            return 0
        print(f"Video not found: {video}", file=sys.stderr)
        return 2
    output_root = Path(args.output_root).expanduser().resolve() if args.output_root else video.parent
    corpus = Path(args.corpus).expanduser().resolve() if args.corpus else output_root / "Corpus"
    corpus.mkdir(parents=True, exist_ok=True)
    package_name = args.package_name or _safe_package_name(video)
    run_plan = _build_run_plan(args, video, output_root, corpus, package_name)
    if args.dry_run_plan:
        write_json(output_root / "new_video_run_plan.json", run_plan)
        print(f"Dry-run plan written: {output_root / 'new_video_run_plan.json'}")
        return 0
    if args.write_run_plan:
        write_json(output_root / "new_video_run_plan.json", run_plan)
    if args.audio_only_export:
        audio_output_root = Path(args.audio_output_root).expanduser().resolve() if args.audio_output_root else output_root / f"{package_name}_audio_analysis"
        analysis_root = audio_output_root / "audio_only_analysis"
        analysis_root.mkdir(parents=True, exist_ok=True)
        include_extracted_audio = not args.exclude_extracted_audio and not args.exclude_audio_from_export
        if args.include_extracted_audio or args.include_audio_in_export:
            include_extracted_audio = True
        print("Building audio-only analysis packet.")
        audio_packet = build_audio_analysis_packet(
            analysis_root,
            video,
            audio_output_root,
            profile=args.audio_packet_profile,
            zip_packet=args.audio_packet_zip,
            include_extracted_audio=include_extracted_audio,
            include_transcript=args.include_transcript,
            include_gpt_prompts=args.include_gpt_prompts,
            include_audio_dashboards=args.include_audio_dashboards,
            extract_audio=True,
            audio_format=args.audio_format,
            sample_rate=args.audio_sample_rate,
            mono=args.audio_mono,
        )
        packet_root = Path(audio_packet["packet_root"])
        zip_path = audio_packet.get("zip_path")
        print("Audio analysis packet complete.")
        print(f"\nOpen first:\n{(packet_root / 'index.html').resolve()}")
        if zip_path:
            print(f"\nSend this zip:\n{Path(zip_path).resolve()}")
        print(f"\nValidation:\n{'passed' if audio_packet['validation'].get('validation_passed') else 'failed'}")
        return 0 if audio_packet["validation"].get("validation_passed") else 1
    export_started_at = utc_now_iso()
    print("Starting fresh video analysis.")
    analysis_start = time.perf_counter()
    if args.simulate:
        analysis_root = corpus / f"{package_name}_analysis"
        _write_fixture_analysis(analysis_root, video)
        result = {"output_dir": analysis_root, "simulated": True}
    else:
        result = run_corpus(corpus, [video], force=args.fresh_analysis or True, verbose=True)
    analysis_duration = round(time.perf_counter() - analysis_start, 2)
    analysis_root = Path(result["output_dir"])
    audio_packet = None
    if args.audio_analysis_packet or args.audio_packet_zip or args.extract_audio or args.audio_only_export:
        audio_output_root = Path(args.audio_output_root).expanduser().resolve() if args.audio_output_root else output_root / f"{package_name}_audio_analysis"
        include_extracted_audio = not args.exclude_extracted_audio and not args.exclude_audio_from_export
        if args.include_extracted_audio or args.include_audio_in_export:
            include_extracted_audio = True
        print("Building audio analysis packet.")
        audio_packet = build_audio_analysis_packet(
            analysis_root,
            video,
            audio_output_root,
            profile=args.audio_packet_profile,
            zip_packet=args.audio_packet_zip,
            include_extracted_audio=include_extracted_audio,
            include_transcript=args.include_transcript,
            include_gpt_prompts=args.include_gpt_prompts,
            include_audio_dashboards=args.include_audio_dashboards,
            extract_audio=True,
            audio_format=args.audio_format,
            sample_rate=args.audio_sample_rate,
            mono=args.audio_mono,
        )
        embedded_audio_packet = analysis_root / "audio_analysis_packet"
        if embedded_audio_packet.exists():
            shutil.rmtree(embedded_audio_packet)
        shutil.copytree(Path(audio_packet["packet_root"]), embedded_audio_packet)
    if args.clean_before_export:
        clean_old_exports(analysis_root, dry_run=False)
    dest = output_root / f"{package_name}_portable_review_package"
    print("Building portable review package.")
    export = build_portable_package(
        analysis_root,
        dest,
        zip_export=args.zip,
        include_raw_media=args.include_raw_media,
        strict=True,
        export_profile=args.export_profile,
        dashboard_consolidation=args.dashboard_consolidation,
        validate_extracted=args.validate_extracted,
        validation_tier=args.validation_tier,
        generation_mode=args.generation_mode,
        cache_mode=args.cache_mode,
        zip_mode=args.zip_mode,
        delta_zip=args.delta_zip,
        base_export=Path(args.base_export).expanduser().resolve() if args.base_export else None,
        topology_simplify=args.topology_simplify,
        review_style=args.review_style,
        dashboard_density=args.dashboard_density,
        artifact_reduction=args.artifact_reduction,
        change_summary=args.change_summary,
        review_workspace=args.review_workspace,
        generate_review_checklists=args.generate_review_checklists,
        generate_handoff_summary=args.generate_handoff_summary,
        requested_video=video,
    )
    fresh = validate_fresh_video_export(analysis_root, video, export_started_at=export_started_at, strict=True)
    index_path = Path(export["package_root"]) / "index.html"
    zip_path = export.get("zip_path")
    if args.open_after_export:
        os.startfile(index_path)  # type: ignore[attr-defined]
    validation = export["validation"]
    size_summary = export["size_report"].get("summary", {})
    extracted_validation = export.get("extracted_validation")
    extracted_passed = extracted_validation.get("validation_passed") if isinstance(extracted_validation, dict) else None
    e2e = {
        "analysis_status": "complete" if validation.get("validation_passed") and fresh["pass_fail"] == "pass" and (extracted_passed is not False) else "error",
        "method": "new_video_export_e2e_validation_v1",
        "generated_at_utc": utc_now_iso(),
        "simulated": bool(args.simulate),
        "requested_video_path_recorded": video.resolve().as_posix(),
        "package_name_recorded": package_name,
        "fresh_analysis_timestamp_checked": bool(fresh.get("analysis_generation_timestamp") or args.simulate),
        "stale_artifacts_excluded": not fresh.get("stale_artifact_warnings"),
        "old_portable_packages_excluded": fresh.get("old_package_excluded"),
        "raw_video_excluded_by_default": not args.include_raw_media,
        "package_generated": Path(export["package_root"]).exists(),
        "zip_generated": bool(zip_path and Path(zip_path).exists()),
        "extracted_validation_passed": extracted_passed,
        "index_path_printed": index_path.resolve().as_posix(),
        "zip_path_printed": Path(zip_path).resolve().as_posix() if zip_path else None,
        "validation_passed": bool(validation.get("validation_passed")),
        "fresh_validation_passed": fresh["pass_fail"] == "pass",
        "audio_packet_generated": bool(audio_packet),
        "audio_packet_zip_path": Path(audio_packet["zip_path"]).resolve().as_posix() if audio_packet and audio_packet.get("zip_path") else None,
        "audio_packet_validation_passed": audio_packet["validation"].get("validation_passed") if audio_packet else None,
    }
    (Path(export["package_root"]) / "validation").mkdir(parents=True, exist_ok=True)
    write_json(Path(export["package_root"]) / "new_video_export_e2e_validation.json", e2e)
    write_json(Path(export["package_root"]) / "new_video_export_validation.json", fresh)
    write_json(Path(export["package_root"]) / "new_video_export_e2e_report.json", e2e)
    write_json(Path(export["package_root"]) / "validation" / "new_video_export_e2e_validation.json", e2e)
    write_json(Path(export["package_root"]) / "validation" / "new_video_export_validation.json", fresh)
    write_json(Path(export["package_root"]) / "validation" / "new_video_export_e2e_report.json", e2e)
    write_json(Path(export["package_root"]) / "fresh_video_export_validation.json", fresh)
    console_lines = [
        "Portable export complete.",
        "",
        f"Open first: {index_path.resolve()}",
        f"Send this zip: {Path(zip_path).resolve() if zip_path else 'not generated'}",
        f"Profile: {args.export_profile}",
        f"Raw video included: {'yes' if args.include_raw_media else 'no'}",
        f"Validation: {'passed' if validation.get('validation_passed') else 'failed'}",
        f"Extracted validation: {extracted_passed}",
        f"Fresh video validation: {fresh['pass_fail']}",
        f"Simulated: {bool(args.simulate)}",
        f"Audio packet: {Path(audio_packet['packet_root']).resolve() if audio_packet else 'not generated'}",
        f"Audio packet zip: {Path(audio_packet['zip_path']).resolve() if audio_packet and audio_packet.get('zip_path') else 'not generated'}",
    ]
    if audio_packet:
        audio_link = "audio_analysis_packet/index.html"
        with (Path(export["package_root"]) / "index.html").open("a", encoding="utf-8") as handle:
            handle.write(f"\n<section><h2>Audio Analysis</h2><ul><li><a href=\"{audio_link}\">Audio Analysis Packet</a></li></ul></section>\n")
    _write_console_summary(Path(export["package_root"]) / "new_video_export_console_summary.txt", console_lines)
    _write_console_summary(Path(export["package_root"]) / "new_video_export_user_summary.md", console_lines)
    if zip_path:
        zip_path = zip_package(Path(export["package_root"]))
        e2e["zip_path_printed"] = Path(zip_path).resolve().as_posix()
        write_json(Path(export["package_root"]) / "new_video_export_e2e_validation.json", e2e)
        write_json(Path(export["package_root"]) / "validation" / "new_video_export_e2e_validation.json", e2e)
    print("Portable export complete.")
    print("")
    print(f"Open first:\n{index_path.resolve()}")
    if zip_path:
        print(f"\nSend this zip:\n{Path(zip_path).resolve()}")
    print("")
    print(f"Profile:\n{args.export_profile}")
    print(f"\nRaw video included:\n{'yes' if args.include_raw_media else 'no'}")
    print(f"\nValidation:\n{'passed' if validation.get('validation_passed') else 'failed'}")
    print(f"\nBroken links:\n{validation.get('broken_link_count')}")
    print(f"\nMissing assets:\n{validation.get('missing_asset_count')}")
    print(f"\nPackage size:\n{round((size_summary.get('total_package_size_bytes') or 0) / (1024 * 1024), 2)} MB")
    print(f"\nZip size:\n{round((size_summary.get('zip_size_bytes') or 0) / (1024 * 1024), 2) if size_summary.get('zip_size_bytes') is not None else 'not generated'} MB")
    print(f"\nAnalysis duration:\n{analysis_duration} seconds")
    print(f"\nFresh video validation:\n{fresh['pass_fail']}")
    print(f"\nSimulated:\n{bool(args.simulate)}")
    return 0 if validation.get("validation_passed") and fresh["pass_fail"] == "pass" and (extracted_passed is not False) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
