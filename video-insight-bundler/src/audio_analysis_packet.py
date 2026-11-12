"""Build standalone audio-analysis packets and zip exports."""

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

from audio_extraction import extract_audio_artifact
from audio_review_dashboard import build_audio_review_dashboards
from audio_transcript_packet import build_transcript_packet
from deep_pacing_analysis import build_deep_pacing_analysis
from gpt_audio_packet_builder import build_gpt_audio_packet
from pause_silence_analysis import build_pause_silence_and_acoustic_outputs
from stability import utc_now_iso


def _copy(src: Path, dst: Path) -> bool:
    if not src.exists() or not src.is_file():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def _copy_json_sanitized(src: Path, dst: Path) -> bool:
    if not src.exists() or not src.is_file():
        return False
    data = json.loads(src.read_text(encoding="utf-8"))
    def scrub(value):
        if isinstance(value, dict):
            cleaned = {}
            for key, item in value.items():
                if key in {"ffmpeg_command", "command"}:
                    cleaned[key] = "ffmpeg command redacted for portable packet; see extraction status and metadata fields."
                else:
                    cleaned[key] = scrub(item)
            return cleaned
        if isinstance(value, list):
            return ["redacted_command_component" if ("\\" in str(item) or ":/" in str(item)) else scrub(item) for item in value]
        if isinstance(value, str) and ("C:\\" in value or "file:///" in value):
            return Path(value).name
        return value
    data = scrub(data)
    if isinstance(data, dict):
        if data.get("ffmpeg_command"):
            data["ffmpeg_command"] = "ffmpeg command redacted for portable packet; see extraction status and metadata fields."
        for key in ("source_video_path", "extracted_audio_path"):
            if data.get(key):
                data[key] = Path(str(data[key])).name if key == "source_video_path" else f"audio/{Path(str(data[key])).name}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return True


def _relative_files(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


def _has_absolute_live_path(root: Path) -> bool:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".json", ".md", ".txt", ".csv", ".html"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "C:\\" in text or "file:///" in text:
                return True
    return False


def build_audio_analysis_artifacts(
    analysis_root: Path,
    source_video: Path,
    output_root: Path,
    *,
    extract_audio: bool = True,
    audio_format: str = "wav",
    sample_rate: int = 16000,
    mono: bool = True,
) -> dict:
    output_root.mkdir(parents=True, exist_ok=True)
    extraction = extract_audio_artifact(source_video, output_root, audio_format=audio_format, sample_rate=sample_rate, mono=mono) if extract_audio else {"status": "skipped", "metadata": {}, "audio_path": None}
    transcript_packet = build_transcript_packet(analysis_root, output_root, source_video)
    pacing = build_deep_pacing_analysis(transcript_packet, output_root)
    acoustic = build_pause_silence_and_acoustic_outputs(analysis_root, output_root, transcript_packet)
    gpt = build_gpt_audio_packet(output_root, source_video, extraction, transcript_packet, pacing, acoustic)
    dashboards = build_audio_review_dashboards(output_root, source_video, transcript_packet, pacing, acoustic, gpt)
    return {"extraction": extraction, "transcript_packet": transcript_packet, "pacing": pacing, "acoustic": acoustic, "gpt": gpt, "dashboards": dashboards}


def build_audio_analysis_packet(
    analysis_root: Path,
    source_video: Path,
    output_root: Path,
    *,
    profile: str = "review",
    zip_packet: bool = False,
    include_extracted_audio: bool = True,
    include_transcript: bool = True,
    include_gpt_prompts: bool = True,
    include_audio_dashboards: bool = True,
    extract_audio: bool = True,
    audio_format: str = "wav",
    sample_rate: int = 16000,
    mono: bool = True,
) -> dict:
    if profile not in {"compact", "review", "full", "gpt_ready"}:
        raise ValueError(f"Unknown audio packet profile: {profile}")
    artifacts = build_audio_analysis_artifacts(
        analysis_root,
        source_video,
        output_root,
        extract_audio=extract_audio,
        audio_format=audio_format,
        sample_rate=sample_rate,
        mono=mono,
    )
    packet = output_root / "audio_analysis_packet"
    if packet.exists():
        shutil.rmtree(packet)
    for dirname in ("audio", "transcript", "metrics", "recommendations", "gpt_ready", "visualizations", "validation", "manifests"):
        (packet / dirname).mkdir(parents=True, exist_ok=True)
    if include_extracted_audio:
        for name in (f"extracted_audio.{audio_format}",):
            _copy(output_root / "audio" / name, packet / "audio" / name)
        _copy_json_sanitized(output_root / "audio" / "extracted_audio_metadata.json", packet / "audio" / "extracted_audio_metadata.json")
        _copy_json_sanitized(output_root / "audio" / "audio_extraction_log.json", packet / "audio" / "audio_extraction_log.json")
    if include_transcript:
        for name in ("transcript_full.md", "transcript_full.txt", "transcript_segments.json", "transcript_segments.csv", "timed_transcript.csv", "timed_transcript.json", "transcript_availability_report.json", "transcript_missing_report.md"):
            _copy(output_root / "audio_analysis" / name, packet / "transcript" / name)
    for name in ("deep_pacing_metrics.json", "pause_silence_metrics.json", "acoustic_energy_metrics.json", "loudness_proxy_metrics.json", "dynamic_range_metrics.json", "audio_quality_flags.json"):
        _copy(output_root / "audio_analysis" / name, packet / "metrics" / name)
    _copy(output_root / "audio_analysis" / "optimal_pacing_recommendations.md", packet / "recommendations" / "optimal_pacing_recommendations.md")
    _copy(output_root / "audio_analysis" / "pause_opportunity_registry.json", packet / "recommendations" / "pause_opportunities.json")
    _copy(output_root / "audio_analysis" / "pacing_spike_registry.json", packet / "recommendations" / "rerecord_candidates.json")
    if include_gpt_prompts:
        for path in (output_root / "audio_analysis" / "gpt_ready").glob("*"):
            _copy(path, packet / "gpt_ready" / path.name)
    if include_audio_dashboards:
        for path in (output_root / "visualizations" / "audio").glob("*.html"):
            _copy(path, packet / "visualizations" / path.name)
    summary = [
        "# Audio Packet Summary",
        "",
        f"- Generated at UTC: `{utc_now_iso()}`",
        f"- Source video: `{source_video.name}`",
        f"- Profile: `{profile}`",
        f"- Extracted audio included: `{include_extracted_audio}`",
        f"- Raw source video included: `False`",
        f"- Transcript included: `{include_transcript}`",
        f"- GPT prompts included: `{include_gpt_prompts}`",
        f"- Classification: `operational beta+ / internal beta_plus`",
    ]
    (packet / "AUDIO_PACKET_SUMMARY.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    (packet / "index.html").write_text("<!doctype html><meta charset='utf-8'><title>Audio Analysis Packet</title><h1>Audio Analysis Packet</h1><ul><li><a href='visualizations/audio_review_dashboard.html'>Audio Review Dashboard</a></li><li><a href='gpt_ready/gpt_audio_review_brief.md'>GPT Audio Review Brief</a></li><li><a href='recommendations/optimal_pacing_recommendations.md'>Pacing Recommendations</a></li></ul>", encoding="utf-8")
    validation = {
        "generated_at_utc": utc_now_iso(),
        "extracted_audio_exists_when_requested": (not include_extracted_audio) or any((packet / "audio").glob("extracted_audio.*")),
        "transcript_exists_or_missing_warning_exists": (packet / "transcript" / "transcript_full.md").exists() or (packet / "transcript" / "transcript_missing_report.md").exists(),
        "metrics_json_exists": (packet / "metrics" / "deep_pacing_metrics.json").exists(),
        "gpt_ready_brief_exists": (packet / "gpt_ready" / "gpt_audio_review_brief.md").exists(),
        "dashboards_exist": bool(list((packet / "visualizations").glob("*.html"))),
        "source_video_excluded": not any(path.suffix.lower() in {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"} for path in packet.rglob("*")),
        "no_absolute_live_paths": not _has_absolute_live_path(packet),
    }
    validation["validation_passed"] = all(bool(value) for key, value in validation.items() if key not in {"generated_at_utc"})
    for name in ("audio_packet_validation.json", "audio_extraction_validation.json", "transcript_packet_validation.json"):
        (packet / "validation" / name).write_text(json.dumps(validation, indent=2), encoding="utf-8")
    manifest = {"generated_at_utc": utc_now_iso(), "profile": profile, "files": _relative_files(packet), "raw_source_video_included": False, "validation_passed": validation["validation_passed"]}
    (packet / "manifests" / "audio_packet_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    zip_path = None
    if zip_packet:
        zip_path = packet.with_suffix(".zip")
        if zip_path.exists():
            zip_path.unlink()
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=8) as archive:
            for path in packet.rglob("*"):
                if path.is_file():
                    archive.write(path, Path("audio_analysis_packet") / path.relative_to(packet))
        validation["zip_validates_after_extraction"] = zipfile.is_zipfile(zip_path)
        (packet / "validation" / "audio_packet_validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    return {"packet_root": packet, "zip_path": zip_path, "validation": validation, "artifacts": artifacts}
