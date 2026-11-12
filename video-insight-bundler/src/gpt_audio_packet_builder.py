"""GPT-ready audio review packet generation."""

from __future__ import annotations

import json
from pathlib import Path

from stability import utc_now_iso


def build_gpt_audio_packet(output_root: Path, source_video: Path, extraction: dict, transcript_packet: dict, pacing: dict, acoustic_outputs: dict) -> dict:
    audio_analysis = output_root / "audio_analysis"
    gpt_dir = audio_analysis / "gpt_ready"
    gpt_dir.mkdir(parents=True, exist_ok=True)
    transcript_report = transcript_packet.get("report") or {}
    extracted_metadata = dict(extraction.get("metadata") or {})
    if extracted_metadata.get("ffmpeg_command"):
        extracted_metadata["ffmpeg_command"] = "ffmpeg command redacted for portable GPT packet; see extraction status and metadata fields."
    brief = {
        "generated_at_utc": utc_now_iso(),
        "source_video_name": source_video.name,
        "extracted_audio_metadata": extracted_metadata,
        "transcript_summary": {
            "available": transcript_report.get("transcript_available"),
            "word_count": transcript_report.get("word_count"),
            "segment_count": transcript_report.get("segment_count"),
        },
        "pacing_summary": {
            "overall_words_per_minute": pacing.get("overall_words_per_minute"),
            "pacing_volatility": pacing.get("pacing_volatility"),
            "candidate_optimal_pacing_range_wpm": pacing.get("candidate_optimal_pacing_range_wpm"),
        },
        "pause_silence_summary": acoustic_outputs.get("pause_silence_metrics") or {},
        "acoustic_energy_summary": acoustic_outputs.get("acoustic_energy_metrics") or {},
        "top_pacing_issues": pacing.get("pacing_spike_locations", [])[:10],
        "top_pause_opportunities": pacing.get("recommended_pause_insertion_points", [])[:10],
        "top_dense_sections": pacing.get("dense_explanation_sections", [])[:10],
        "top_re_record_candidates": pacing.get("recommended_re_record_candidates", [])[:10],
        "top_preserve_as_intentional_candidates": pacing.get("preserve_as_intentional_candidates", [])[:10],
        "recommended_review_questions": [
            "Where may pacing be too dense for the intended audience?",
            "Which pauses would improve clarity without reducing useful energy?",
            "Which high-WPM sections should be preserved as intentional cadence?",
            "Which sections are candidate re-records after human review?",
        ],
        "artifact_references": {
            "transcript": "../transcript_full.md",
            "timed_transcript": "../timed_transcript.csv",
            "pacing_metrics": "../deep_pacing_metrics.json",
            "pause_silence_metrics": "../pause_silence_metrics.json",
            "acoustic_energy_metrics": "../acoustic_energy_metrics.json",
            "recommendations": "../optimal_pacing_recommendations.md",
        },
        "limitations": [
            "Acoustic energy is not emotion.",
            "Loudness is not confidence.",
            "Silence is not uncertainty.",
            "Human review is required before script, edit, or re-record decisions.",
        ],
    }
    lines = [
        "# GPT Audio Review Brief",
        "",
        f"- Source video: `{source_video.name}`",
        f"- Transcript available: `{transcript_report.get('transcript_available')}`",
        f"- Word count: `{transcript_report.get('word_count')}`",
        f"- Overall WPM: `{pacing.get('overall_words_per_minute')}`",
        f"- Pacing volatility: `{pacing.get('pacing_volatility')}`",
        "",
        "## Top Review Points",
        "",
    ]
    for row in brief["top_pacing_issues"][:8]:
        lines.append(f"- Segment `{row.get('segment_id')}` at {row.get('start_sec')}-{row.get('end_sec')}s may suggest high pacing (`{row.get('wpm')}` WPM).")
    lines.extend(["", "## Artifact References", ""])
    for label, rel in brief["artifact_references"].items():
        lines.append(f"- {label}: `{rel}`")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in brief["limitations"])
    prompt_base = "\n".join(
        [
            "Use the attached audio-analysis packet. Treat metrics as candidate review signals, not proof of emotion, intent, or audience response.",
            "Reference segment IDs and artifact filenames. Do not assume the raw source video is included.",
            f"Source video: {source_video.name}",
            f"Overall WPM: {pacing.get('overall_words_per_minute')}",
            "Use transcript files for exact wording instead of asking this prompt to contain the full transcript.",
        ]
    )
    prompts = {
        "gpt_prompt_for_audio_pacing_review.md": prompt_base + "\n\nFocus on candidate optimal pacing range, high-WPM sections, pauses, and dense explanations.\n",
        "gpt_prompt_for_delivery_coaching.md": prompt_base + "\n\nFocus on delivery patterns, cadence, emphasis candidates, and human-review coaching language.\n",
        "gpt_prompt_for_rewrite_or_rerecord_plan.md": prompt_base + "\n\nCreate a conservative rewrite or re-record plan with segment IDs and rationale.\n",
        "gpt_prompt_for_editorial_timing_review.md": prompt_base + "\n\nReview edit timing, visual reset opportunities, and pause placement candidates.\n",
    }
    (gpt_dir / "gpt_audio_review_brief.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (gpt_dir / "gpt_audio_review_brief.json").write_text(json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")
    for filename, text in prompts.items():
        (gpt_dir / filename).write_text("# GPT Prompt\n\n" + text, encoding="utf-8")
    manifest = {"generated_at_utc": utc_now_iso(), "files": sorted(path.name for path in gpt_dir.iterdir() if path.is_file()), "brief": "gpt_audio_review_brief.md"}
    (gpt_dir / "gpt_data_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"brief": brief, "manifest": manifest}
