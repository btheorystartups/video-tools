# Video Insight Bundler technical walkthrough scenes and narration

Optional companion to the consulting showcase in `video_walkthrough_script.md`.
An approximately five-minute screen recording showing how to follow one saved
video finding through its segment evidence, assess a recommendation, and save
review notes. Use one narrator with a calm, practical delivery. The audience is
a first-time reviewer; no technical setup or editing knowledge is assumed.

The timings below are editing targets, including cursor movement and short
reading pauses. Rehearse once before locking the final duration. This is an
internal beta walkthrough, not a claim of production readiness.

## Recording setup

- Begin at `http://127.0.0.1:8010/portable_review_package/index.html`.
- Use a clean browser view, readable text, and a visible but unhurried cursor.
  Hide notifications, unrelated tabs, and personal filesystem paths where possible.
- Show the actual interface, not a mockup. Do not include a fake video player,
  automatic edits, audience predictions, or automatic note persistence.
- Record the narration separately if that makes the screen demonstration easier.
  Keep narration continuous while using cuts between page changes.
- The demonstration video is `Why Should Anyone Listen to you Anyway - Brian Theory.mp4`.
  Focus on the opening segment, 0.00 to 14.64 seconds.
- Use the notes example in Scene 7 as demonstration text, not a final editorial decision.

## Scene 1 Introduce the review workflow

**Target time:** 0:00 to 0:25

**Screen action:** Start with the package landing page. Keep the application
title visible, then gently highlight the five-minute walkthrough link.

**On-screen caption:** Video Insight Bundler — from a finding to a review decision

**Spoken narration:**

> A recommendation is only useful if we can see what supports it. Video Insight
> Bundler brings saved analysis, timelines, evidence, and review guidance into
> one portable package. In this walkthrough, we'll follow one video segment,
> inspect its recorded signals, assess a recommendation, and save a review note
> for the next person.

## Scene 2 Open the focused walkthrough

**Target time:** 0:25 to 0:55

**Screen action:** Click “Finding → evidence → recommendation → saved notes.”
Show the named video, the segment range, and the four-step review route. Hold
the snapshot and excluded-media notice long enough to read.

**On-screen caption:** Saved analysis snapshot — original media is not bundled

**Spoken narration:**

> I'll open the short walkthrough for “Why Should Anyone Listen to You Anyway.”
> This is a saved analysis snapshot, not a new analysis happening as I click.
> The original video is intentionally excluded from this package. What we're
> reviewing here is the derived information and the guidance attached to it.
> The route keeps us focused on one segment instead of the entire corpus.

## Scene 3 Orient on the video timeline

**Target time:** 0:55 to 1:35

**Screen action:** Click “Orient: video timeline.” Frame the video title and
the segment lane. Move the cursor across two or three segment boxes, then
pause over the 0.00–14.64 sec opening segment. Do not imply that hovering plays
the video or reveals features the interface does not expose.

**On-screen caption:** Locate the segment by its time range

**Spoken narration:**

> The timeline gives us a way to locate the part of the video we want to review.
> These boxes are labeled with time ranges, so we don't have to work from
> internal segment identifiers alone. For this example, I'll use the opening
> fourteen point six four seconds. The high label is a signal to inspect this
> region. It isn't proof that the opening is wrong, or a prediction of how an
> audience will respond.

## Scene 4 Inspect the segment context

**Target time:** 1:35 to 2:05

**Screen action:** Click the opening segment. Show its readable heading and
metadata, then scroll to “What To Preserve,” “What To Review,” and “What Not
To Infer.” Avoid lingering on long provenance paths or recommendation IDs.
Return to the walkthrough using browser Back twice, or a clean edit cut.

**On-screen caption:** Read the context before changing the video

**Spoken narration:**

> Opening the segment shows its context, evidence references, and linked
> recommendation identifiers. It also explains what to preserve and what not
> to infer. Some references point back to the originating machine; a recorded
> source reference doesn't mean that file is included here. Before making an
> edit, I still need to check the original media and decide whether the pattern
> is intentional.

## Scene 5 Read the recorded segment signals

**Target time:** 2:05 to 2:55

**Screen action:** Click “Check this segment’s recorded evidence.” Show the
four recorded signals. Highlight topic_drift at 0.75 and the sentence explaining
that scores are heuristic indicators, not probabilities. Briefly point to
“Source temporal evidence registry” without opening a large JSON document
during the main narration.

**On-screen caption:** Heuristic scores are review cues, not probabilities

**Spoken narration:**

> Back in the walkthrough, the evidence section keeps the recorded signals
> tied to this same segment. Here we can see recommendation activity, topic
> drift, speech pacing, and visual reset. For example, topic drift is recorded
> at zero point seven five. That number is a heuristic indicator, not a
> seventy-five percent probability of a problem. These signals help frame a
> review question; they don't settle it. The source registry is available if
> we want to inspect the underlying record in more detail.

## Scene 6 Assess the segment matched recommendation

**Target time:** 2:55 to 3:40

**Screen action:** Click “Assess the segment-matched recommendation.” Frame
“Chronic editorial pressure region,” the recommended next action, and the
lowest-risk path. Keep the recommended action readable rather than zooming
into its internal identifier.

**On-screen caption:** Assess the recommendation — preserve intentional choices

**Spoken narration:**

> The segment-matched recommendation asks us to inspect the pressure
> components and consider whether a bridge, callback resolution, or pacing
> review is needed. That's a prompt for a human decision, not an instruction
> to automatically change the video. The lowest-risk path is to start with
> analysis-only notes and preserve intentional patterns unless the evidence
> remains strong after review. I can accept the recommendation, reject it,
> or leave it open with a clear reason. Nothing on this page applies an edit
> to the media.

## Scene 7 Record and export a review note

**Target time:** 3:40 to 4:35

**Screen action:** Scroll to the checklist and notes. Type the example below,
check both items after recording the open decision, and click “Download review
notes.” Show the visible exported JSON, including its note and checklist state.
Only show a downloaded file if the browser actually saved one; otherwise show
the manual-save fallback. Do not claim that a download request confirms a save.

**On-screen caption:** Example review note — explicit external save required

**Example text to enter:**

```text
Decision: Leave open pending original-media review.
Evidence checked: Opening segment 0.00–14.64 sec, recorded signals, and the segment-matched recommendation.
Open risk: The heuristic labels do not establish whether the opening is intentionally structured this way.
Next action: Review the original opening and decide whether to preserve it or test a clearer bridge.
```

**Spoken narration:**

> I'll leave this example open until I've checked the original opening. My
> note records the evidence I inspected, the uncertainty, and the next action.
> The checklist makes that review state explicit. One important limitation:
> this is a static package. Notes and checkboxes do not save automatically.
> I'll request the notes download and check that the file was actually saved.
> If the browser doesn't save it, the exported JSON is visible here so I can
> copy it into an external file. Either way, I keep that notes file with the
> handoff before closing or refreshing the page.

## Scene 8 Explain the handoff and close

**Target time:** 4:35 to 5:00

**Screen action:** Return to the landing page with a clean cut. Show the package
validation status, then the separate fallback-link audit notice. Finish on the
walkthrough title or a simple end card.

**On-screen caption:** Handoff = review package + saved notes + original-media review when needed

**Spoken narration:**

> The handoff is the review package plus the notes we saved separately. Package
> validation checks whether links resolve, while the fallback audit separately
> identifies references that aren't available in the package. A clean link
> check doesn't mean every source is present. The workflow is straightforward:
> find the segment, inspect the evidence, assess the recommendation, and
> preserve the human decision and uncertainty.

## Recording acceptance checklist

- The named video and 0.00–14.64 sec range match throughout the recording.
- Narration calls this a saved snapshot and explains original-media exclusion.
- Severity and scores are not presented as probabilities, viewer predictions,
  verified defects, or validated creative outcomes.
- The recommendation is assessed, not presented as an automatic edit.
- The example note is clearly a demonstration and preserves an open decision.
- Note text and checklist state appear in the exported JSON. A successful file
  save is shown only if verified; the manual-save fallback is shown otherwise.
- The finished video includes the no-autosave limitation and separate fallback audit.
- Personal paths and unrelated tabs or notifications are not prominent.
- Captions use the spoken words and leave the important interface text readable.
- Rehearsal confirms that the narration and screen actions fit the final timing.

## Producer source references

The narration follows the generated `demo_walkthrough.html` and
`demo_walkthrough.json`, the named video's timeline and opening-segment context,
`timeline/temporal_evidence_index.json`, and
`recommendations/recommendation_traceability.json` inside the current
`Videos/Brian/Corpus_analysis/portable_review_package` export. The matching
recommendation is `RECTRC_2ae092334497a2fc`. Keep those sources aligned if the
package is regenerated before recording.
