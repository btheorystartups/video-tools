# Video Tools

Local-first video analysis and editorial review tools by Brian.

## Video Insight Bundler

[Video Insight Bundler](video-insight-bundler/) turns a local recording into an inspectable analysis bundle: transcripts, graphs, timestamped evidence, recommendations, and offline HTML dashboards.

| View | What it helps you investigate |
| --- | --- |
| **Emotional Arc** | Changes in lexical tone, certainty, intensity, and pacing-derived energy. |
| **Pacing Curve** | Speaking-rate changes and transcript gaps worth reviewing. |
| **Acoustic Energy** | Waveform energy, quieter regions, and contrasts between segments. |
| **Topic Timeline** | How prominent terms and topic labels change through a recording. |
| **Keyword Clusters** | Recurring vocabulary and related groups of transcript segments. |
| **Rhetorical Modes** | Patterns of explanation, examples, contrast, questions, and audience address. |

See all six original example graphs in the [illustrated capability writeup](CAPABILITIES.md), with methods, practical uses, output filenames, and limitations.

Watch the [portfolio walkthrough](https://www.correspondencematrices.com/work/video-insight-bundler).

## Quick start

Install Python 3.13 (or a compatible Python 3.x), FFmpeg, and FFprobe; ensure the latter two are on PATH. From the repository root:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\video-insight-bundler\requirements-visualization.txt
.\.venv\Scripts\python.exe -m pip install faster-whisper opencv-python
.\.venv\Scripts\python.exe .\video-insight-bundler\analyze_video.py --video "C:\path\to\video.mp4" --output .\output --verbose
```

Open `output/<video-stem>_analysis/visualizations/dashboard.html` in a browser. If transcription is unavailable, supply an existing transcript with `--transcript-import "C:\path\to\transcript.json"`; language-based analysis needs transcript evidence.

The first faster-whisper model download may require internet access. Normal analysis runs locally; cloud transcription or an LLM is not required. The optional LLM interpretation layer is separate from the measured results.

For a portable shareable package:

```powershell
.\.venv\Scripts\python.exe .\video-insight-bundler\export_new_video.py --video "C:\path\to\video.mp4" --output-root .\exports --package-name my_video_review --export-profile review --zip --validate-extracted
```

See the [upstream technical README](video-insight-bundler/README.md) for the full feature history. Older examples there use the original `tools/video-insight-bundler` layout; in this repository use `video-insight-bundler` from the root.

## Scope and maturity

This is an extracted development snapshot, classified upstream as **operational beta+ / internal beta_plus**. It provides evidence and review support; a person interprets the signals and makes editorial decisions. It does not automatically edit video, detect a speaker's true emotions, or predict audience retention.

The source snapshot comes from [btheorystartups/Tools](https://github.com/btheorystartups/Tools/tree/4207202c325557eb6888a4b009b287a5927b292d/video-insight-bundler). See [PUBLICATION.md](PUBLICATION.md) for provenance and verification boundaries.

Raw recordings, extracted audio, full analysis outputs, and local credentials are not included. Review transcripts, frames, paths, and annotations before sharing a generated bundle.
