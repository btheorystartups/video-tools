# Methodology

## Local-First Design

The project uses local tools first:

- FFprobe for media metadata
- FFmpeg for audio extraction and frame sampling
- faster-whisper when installed for local transcription
- Python standard library for bundle assembly and heuristics

No cloud API is required.

## Transcript And Pacing

When transcription is available, the tool uses segment timestamps to estimate:

- word count
- words per minute
- pauses between transcript segments
- segment-level pacing

This is not acoustic prosody analysis. It does not measure pitch, loudness, stress, or phoneme timing.

## Segmentation

With transcript timestamps, segments are grouped by:

- target duration windows
- pauses
- rhetorical markers such as contrast, sequence, examples, and instructions

Without a transcript, the tool falls back to fixed time windows.

## Emotional Arc

The first-pass emotional arc is a transparent lexical and pacing heuristic. It estimates:

- energy
- valence
- certainty
- intensity
- dominant tone

The model is intentionally modest. It is not psychological analysis and should not be treated as clinical, identity, or intent evidence.

## Persona And Style Classification

Persona and teaching style profiles use taxonomy marker hits, pacing bands, and tone signals. Categories are weighted observations of communication style.

They are not claims about the speaker's identity, character, or stable personality.

## Visual Sampling

The tool samples frames at regular intervals and, when OpenCV is available, performs deterministic local visual structure analysis:

- histogram difference
- mean absolute pixel difference
- edge difference
- brightness and contrast change
- brightness, contrast, saturation proxy, edge density, visual complexity, motion proxy, negative-space proxy, and similarity summaries
- visual-boundary alignment against transcript, rhetorical, discourse, acoustic, and topic boundary evidence

If OpenCV is unavailable, the tool writes placeholder visual structure artifacts with explicit status and limitations so downstream reports remain stable.

The visual pass does not perform:

- face detection
- pose analysis
- object recognition
- visual emotion recognition
- identity detection
- cinematic intent detection

Visual structure outputs are deterministic pixel/color/edge-level evidence summaries for editorial review. They are not object recognition, identity detection, emotion recognition, or cinematic intent claims.

## Privacy

The tool writes analysis outputs locally. Video, audio, transcripts, sampled frames, and recommendations may contain sensitive content. Review generated bundles before sharing them with any LLM or external service.

## Sending To An LLM

Use `llm_context_bundle.md` for a pasteable context package. Use `llm_context_bundle.json` when the receiving tool can ingest structured data.

Recommended follow-up prompt:

```text
Review this video analysis bundle. Identify the strongest segments, weakest segments, pacing issues, tonal inconsistencies, unclear claims, and the top edits that would improve retention and clarity.
```
