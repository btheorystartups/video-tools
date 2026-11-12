"""Offline static dashboards for audio-analysis packets."""

from __future__ import annotations

import html
from pathlib import Path


def _page(title: str, body: str) -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title><style>
body{{font-family:Arial,sans-serif;margin:0;background:#f6f7f8;color:#202124;line-height:1.45}}header,main{{padding:24px 32px}}header{{background:#fff;border-bottom:1px solid #d6d9dd}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}.card{{background:#fff;border:1px solid #d6d9dd;border-radius:6px;padding:14px}}
a{{color:#245f86}}table{{border-collapse:collapse;width:100%;background:#fff}}td,th{{border:1px solid #d6d9dd;padding:8px;text-align:left}}.note{{border-left:4px solid #8a6d3b;background:#fff;padding:12px}}
</style></head><body><header><h1>{html.escape(title)}</h1><p>Offline audio review dashboard. Candidate review signals only.</p></header><main>{body}</main></body></html>"""


def build_audio_review_dashboards(output_root: Path, source_video: Path, transcript_packet: dict, pacing: dict, acoustic_outputs: dict, gpt: dict) -> dict:
    vis_dir = output_root / "visualizations" / "audio"
    vis_dir.mkdir(parents=True, exist_ok=True)
    transcript_report = transcript_packet.get("report") or {}
    cards = f"""
<section class="grid">
<div class="card"><strong>Source</strong><br>{html.escape(source_video.name)}</div>
<div class="card"><strong>Transcript</strong><br>{transcript_report.get('transcript_available')}</div>
<div class="card"><strong>Overall WPM</strong><br>{pacing.get('overall_words_per_minute')}</div>
<div class="card"><strong>Pacing Volatility</strong><br>{pacing.get('pacing_volatility')}</div>
<div class="card"><strong>Pause Count</strong><br>{(acoustic_outputs.get('pause_silence_metrics') or {}).get('pause_count')}</div>
<div class="card"><strong>Silence Ratio</strong><br>{(acoustic_outputs.get('pause_silence_metrics') or {}).get('silence_ratio')}</div>
</section>"""
    links = """
<section><h2>GPT-Ready Files</h2><ul>
<li><a href="../../audio_analysis/gpt_ready/gpt_audio_review_brief.md">GPT audio review brief</a></li>
<li><a href="../../audio_analysis/gpt_ready/gpt_prompt_for_audio_pacing_review.md">Audio pacing prompt</a></li>
<li><a href="../../audio_analysis/gpt_ready/gpt_prompt_for_delivery_coaching.md">Delivery coaching prompt</a></li>
</ul></section>"""
    limitations = "<section class='note'><h2>Limitations</h2><p>Acoustic energy is not emotion, loudness is not confidence, and silence is not uncertainty. Human review is required.</p></section>"
    body = cards + """
<section><h2>Audio Extraction Summary</h2><p>See <a href="../../audio/extracted_audio_metadata.json">extracted audio metadata</a>.</p></section>
<section><h2>Transcript Availability</h2><p>See <a href="../../audio_analysis/transcript_availability_report.json">transcript report</a>.</p></section>
<section><h2>Pacing Overview</h2><p>See <a href="../../audio_analysis/deep_pacing_metrics.json">deep pacing metrics</a> and <a href="../../audio_analysis/optimal_pacing_recommendations.md">recommendations</a>.</p></section>
<section><h2>Pause and Silence</h2><p>See <a href="../../audio_analysis/pause_silence_metrics.json">pause and silence metrics</a>.</p></section>
<section><h2>Acoustic Energy</h2><p>See <a href="../../audio_analysis/acoustic_energy_metrics.json">acoustic energy metrics</a>.</p></section>
<section><h2>Dense Sections and Re-record Candidates</h2><p>Use segment IDs in the pacing registry. Preserve-as-intentional candidates require human judgment.</p></section>
""" + links + limitations
    pages = {
        "audio_review_dashboard.html": body,
        "pacing_review_dashboard.html": cards + "<section><h2>Pacing Spikes</h2><p>Review <a href='../../audio_analysis/pacing_spike_registry.json'>pacing spikes</a>.</p></section>" + limitations,
        "pause_silence_dashboard.html": cards + "<section><h2>Pause Opportunities</h2><p>Review <a href='../../audio_analysis/pause_opportunity_registry.json'>pause opportunities</a>.</p></section>" + limitations,
        "acoustic_energy_dashboard.html": cards + "<section><h2>Acoustic Energy Curve</h2><p>Review <a href='../../audio_analysis/acoustic_energy_curve.csv'>energy curve CSV</a>.</p></section>" + limitations,
        "transcript_timing_dashboard.html": cards + "<section><h2>Timed Transcript</h2><p>Review <a href='../../audio_analysis/timed_transcript.csv'>timed transcript CSV</a>.</p></section>" + limitations,
        "gpt_audio_packet_dashboard.html": cards + links + limitations,
    }
    for filename, page_body in pages.items():
        (vis_dir / filename).write_text(_page(filename.replace("_", " ").replace(".html", "").title(), page_body), encoding="utf-8")
    return {"dashboard_dir": str(vis_dir), "dashboards": sorted(pages)}
