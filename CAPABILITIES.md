# Video Insight Bundler: capabilities and demonstrated output

Video Insight Bundler turns a recording into a navigable evidence package. It connects transcript text, timestamps, sound measurements, visual samples, graphs, and review recommendations so that an editor or researcher can find a passage, compare signals, and return to the original recording.

## Six complementary views

### Emotional Arc

Shows segment-level **energy, valence, certainty, intensity, and dominant tone**. The implementation counts transparent lexical markers and combines some of them with speaking rate. Example tone categories include analytical, instructional, motivational, critical, and reflective.

Use it to locate changes in language or delivery, compare the opening with later passages, or find moments worth preserving or reviewing. The evidence records the marker words and pacing cues behind the score.

**Interpretation:** these are editorial communication-style proxies. They do not measure the speaker's feelings, identify personality, or establish how viewers respond. The emotional-arc energy score is distinct from measured acoustic RMS energy.

Outputs: `emotional_arc.json`, `graphs/emotional_arc.png`, `visualizations/emotional_arc.html`.

### Pacing Curve

Plots speaking rate from transcript word counts and timestamped intervals. Related outputs summarize rate distributions, transcript density, and gaps between transcript segments.

Use it to find abrupt accelerations, slower reflective passages, unusually short intervals, and possible pauses. Pair the curve with the transcript and playback before deciding whether to tighten or preserve a passage.

**Interpretation:** transcript boundaries strongly affect words-per-minute estimates. A short final interval can produce a sharp spike. Gaps between transcription segments are not phoneme-level silence measurements.

Outputs: `audio_features.json`, `graphs/pacing_curve.png`, `graphs/speaking_rate_distribution.png`, `graphs/pause_distribution.png`, `visualizations/pacing_analysis.html`.

### Acoustic Energy

Measures the sound waveform locally using librosa and NumPy. The analysis includes RMS energy over time, per-segment averages and variability, approximate quiet regions, contrasts between adjacent segments, and spectral summaries.

Use it to locate peaks, quieter passages, changes in recording level, and moments where delivery or sound deserves a closer listen. Comparing waveform energy with transcript pacing helps distinguish a change in sound level from a change in word density.

**Interpretation:** RMS measures signal amplitude/energy rather than calibrated perceived loudness. Microphone placement, recording gain, music, and noise can affect it. Threshold-based quiet regions and rhythm proxies are approximate; a peak does not establish excitement or intent.

Outputs: `acoustic_features.json`, `graphs/acoustic_energy_curve.png`, `graphs/segment_energy_bars.png`, `graphs/silence_ratio.png`, `visualizations/acoustic_analysis.html`.

### Topic Timeline

Shows the prominent terms associated with successive segments. With scikit-learn available, the tool uses local TF-IDF term weighting, cosine similarity between adjacent segments, and deterministic K-means clustering when enough segments exist. A frequency-keyword fallback is available.

Use it to follow discussion structure, locate a subject, inspect a topic transition, and compare repeated concepts across passages.

**Interpretation:** labels summarize surface vocabulary. Similar words do not guarantee similar meaning, and a vocabulary change does not prove incoherence. The method and fallback status are recorded in the output.

Outputs: `topic_analysis.json`, `graphs/topic_timeline.png`, `graphs/topic_shift_heatmap.png`, `visualizations/topic_analysis.html`.

### Keyword Clusters

Provides a compact view of salient transcript vocabulary alongside related topic, keyword-importance, repetition, and word-cloud views. The current graph groups the 24 most frequent keywords by their first letter and sums their counts; the topic-analysis JSON separately records TF-IDF segment clusters when available.

Use it to see recurring language, identify terms to search in the transcript, and check whether the recording spends attention on its intended subject. Inspect the topic cluster records to see which segments are grouped together.

**Interpretation:** a frequent term is not automatically an important idea. Stopwords, transcription quality, excerpt length, and repeated phrasing affect the result. The displayed first-letter groups are alphabetical buckets, not semantic clusters; the separate TF-IDF/K-means segment grouping is a different output.

Outputs: `graphs/keyword_clusters.png`, `graphs/keyword_importance.png`, `graphs/concept_repetition.png`, `graphs/wordcloud.png`, and keyword/cluster records in `topic_analysis.json`.

### Rhetorical Modes

Maps marker-based communication patterns across segments: instruction, examples, explanation, contrast, audience address, abstract reflection, concrete action, and other detected categories. Related views summarize question density, claim/example balance, and abstract/concrete language.

Use it to investigate where an explanation needs an example, where a question is introduced, how direct audience address is distributed, and whether long stretches use a similar mode.

**Interpretation:** modes come from phrase counts and simple rules. Question cues can include interrogative words as well as question marks. These are review leads, not validated argument understanding or intent detection.

Outputs: `rhetorical_analysis.json`, `graphs/rhetorical_mode_timeline.png`, `graphs/question_density.png`, `graphs/claim_example_balance.png`, `visualizations/rhetorical_deep_dive.html`.

## A concrete example from the portfolio walkthrough

The saved demonstration record describes an excerpt from **01:15 to 03:40** in the original recording:

| Saved field | Value |
| --- | --- |
| Excerpt duration | 145 seconds (2:25) |
| Transcript words | 260 |
| Topic segments | 7 |
| Topic method | `local_tfidf_deterministic` |
| Example pacing interval, relative to excerpt | 112.32–127.08 seconds |
| Words in that interval | 14 |
| Interval speaking rate | 56.91 words per minute |
| Same interval in original recording | 187.32–202.08 seconds |

That slower interval gives a reviewer a specific passage to check for emphasis or a pause. It does not by itself mean the passage needs to be cut.

The walkthrough follows a discussion from information-stitching tools, through connection with AI and comparisons with pets, to the speaker's value as a human communicator. It demonstrates reading topic labels beside the actual transcript. Its narration describes fairly steady acoustic energy with brief peaks and quieter passages; that description is qualitative, rather than a new acoustic measurement made for this release.

Evidence:
- [Saved example record](https://github.com/btheorystartups/Consulting-Website/blob/main/public/work/video-insight-bundler/example-record.json)
- [Published walkthrough captions](https://github.com/btheorystartups/Consulting-Website/blob/main/public/media/project-captions/video-insight-bundler.vtt)
- [Portfolio page and video](https://www.correspondencematrices.com/work/video-insight-bundler)

These numbers describe one demonstrated excerpt, not a benchmark of accuracy or editing effectiveness. The original full local analysis directory was not available during this extraction, and its results were not recomputed.

## Beyond the six graphs

The source also includes:

- **Local transcription and transcript import:** optional faster-whisper transcription; JSON and SRT; import of compatible existing transcript JSON.
- **Frame sampling and visual structure:** contact sheets and deterministic pixel/color/edge change evidence for shot-boundary and continuity review, when optional dependencies are available.
- **Continuity and discourse review:** topic bridges, rhetorical coherence, argument-chain and callback heuristics, with source-linked review leads.
- **Recommendations and evidence tracing:** ranked recommendations, segment drilldowns, and links between findings and supporting artifacts.
- **Corpus comparison:** multi-video summaries, pacing/style fingerprints, review queues, and historical comparisons based on configured corpus context.
- **Review and handoff:** annotations, checkpoints, worksheets, reconciliation, provenance, and review packets.
- **Offline sharing:** static HTML dashboards, PNG charts, JSON/Markdown reports, optional self-contained interactive HTML, and portable ZIP exports.
- **LLM context bundles:** structured JSON and pasteable Markdown for a separate assisted review. Optional LLM explanatory enrichment remains advisory.

Many advanced layers are deterministic heuristics or workflow scaffolding. Their presence in the source does not establish validated semantic understanding, production readiness, or automatic editing capability.

## A practical review workflow

1. Analyze a recording with a transcript and the relevant optional dependencies.
2. Open `visualizations/dashboard.html`.
3. Find an interesting passage in the pacing, topic, sound, or rhetorical views.
4. Read the timestamped transcript and evidence together.
5. Listen to or watch the original passage.
6. Record a decision, uncertainty, or follow-up; then export a reviewed package if useful.

Check `dependency_report.json`, analysis statuses, and `validation_report.json` before interpreting results. Missing dependencies may lead to unavailable analyses or placeholder graphs. An output file existing does not guarantee that its analysis ran.

## Boundaries and sharing

The core workflow runs locally and does not require DaVinci Resolve, a database, or a cloud API. Optional model downloads or deliberately configured LLM services are separate. The tool does not autonomously apply edits, infer identity, diagnose emotion, or predict audience retention.

Portable exports omit raw media by default, but transcripts, sampled frames, annotations, and provenance paths can still be sensitive. Inspect the exact package before sharing it.

For technical details, see [methodology](video-insight-bundler/docs/methodology.md), [visualization reporting](video-insight-bundler/docs/visualization_reporting.md), and the [output contract](video-insight-bundler/docs/output_contract.md).
