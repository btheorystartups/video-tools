# Video Insight Bundler consulting showcase scenes and narration

A roughly three-minute case study for potential clients visiting
CorrespondenceMatrices.com. Show how Brian turns a review problem into an
inspectable workflow, using one working video-analysis example, then connect
that approach to possible client needs. The invitation is to discuss a technical
question, not to buy a finished video-analytics product.

Use one narrator with a calm, conversational delivery. Timings are editing
targets, not a requirement to pad the video. The five-minute demonstration is
preserved in [the technical walkthrough script](video_walkthrough_technical_script.md).

## Recording setup

- Start with the actual package at
  `http://127.0.0.1:8010/portable_review_package/demo_walkthrough.html`.
- Use the named Brian video and its opening segment, 0.00–14.64 seconds.
  Say “opening fifteen seconds”; keep the exact range visible onscreen.
- Frame the relevant content closely. Avoid dense sidebars, internal IDs,
  personal filesystem paths, and large JSON documents as primary visuals.
- Cut loading, back-navigation, and most typing; keep narration flowing over
  the screen actions. Show the real interface, not a fictional client dashboard.
- Show “Working prototype · saved analysis” once near the beginning.
- Use the sample note below as a demonstration, not a final editorial decision.
- Confirm an external notes file was saved before depicting a completed handoff;
  otherwise show the export step without claiming a successful save.

## Scene 1 Establish the client problem

**Target time:** 0:00 to 0:25

**Screen action:** Open on a close view of the actual recommendation and review
note areas. Introduce three short editorial labels in sequence: “Recommendation,”
“Supporting evidence,” and “Next action.” These describe the problem, not a
simulated client dashboard. Let the application title appear after the opening
sentence rather than starting with a long title card.

**On-screen caption:** What supports this recommendation and what happens next?

**Spoken narration:**

> When analysis, source material, and review decisions live in different places,
> teams can lose track of why a recommendation was made. The challenge isn't
> just generating more information. It's making that information usable: what
> should someone inspect, what supports the recommendation, and what needs a
> human decision?

## Scene 2 Explain the design choice

**Target time:** 0:25 to 0:50

**Screen action:** Show the walkthrough title and four-step route. Briefly
highlight the separation between recorded signals, the recommendation, and
the human review note. Keep “Working prototype · saved analysis” readable.

**On-screen caption:** Brian's design choice — connect evidence without automating judgment

**Spoken narration:**

> I built Video Insight Bundler to explore that workflow using video analysis.
> My central design choice was to keep recorded signals, source references,
> and human decisions separate, but connected. Video is the example here;
> the broader design problem is connecting evidence to decisions people can
> inspect. This demonstration uses saved analysis, with original media excluded.

## Scene 3 Follow one example from evidence to recommendation

**Target time:** 0:50 to 1:35

**Screen action:** Click “Orient: video timeline” and frame the opening-segment
box. Open its context page, showing the time range and review guidance rather
than long identifiers. Cut back to the scoped recorded signals, then the
segment-matched recommendation. Hold its next-action sentence long enough to
read. Connect the explanation to the relevant text with the cursor; do not read
numeric scores aloud or imply the source video plays in the package.

**On-screen caption:** Locate the segment → inspect the record → frame a review question

**Spoken narration:**

> Here, we're reviewing the opening fifteen seconds of one example video.
> The timeline locates the segment, and its context shows what the analysis
> recorded. I'll compare those signals with the linked recommendation:
> inspect whether the opening needs a clearer transition or a pacing review.
> These signals guide inspection, not conclusions. Before editing, I'd check
> the original media and decide whether the opening's structure is intentional.
> The workflow lets me document that question and its next step.

## Scene 4 Show the useful review record

**Target time:** 1:35 to 2:10

**Screen action:** Show the completed example note below. Cut past most typing.
Check the two review items after documenting the open decision, then request
the notes export. Keep “Evidence checked,” “Uncertainty,” and “Next action” as
the visual payoff; show the payload only briefly to confirm the note and checklist
state. Don't linger on JSON syntax. If an external save has been verified, end
on the saved file beside the package. Otherwise, remain on the export request
message and visible manual-save fallback.

**On-screen caption:** Evidence checked · uncertainty recorded · next action identified

**Sample note:**

```text
Decision: Leave open pending original-media review.
Evidence checked: Opening segment 0.00–14.64 sec, recorded signals, and the linked recommendation.
Uncertainty: The recorded signals do not establish whether the opening is intentionally structured this way.
Next action: Watch the original opening and decide whether to preserve it or test a clearer transition.
```

**Spoken narration:**

> For this example, I leave the editorial decision open and record what I
> checked, the uncertainty, and what to inspect next. Now the next reviewer
> has an explicit starting point. This static version requires an external
> save; notes don't autosave. I can export the note and checklist together,
> keeping the review record alongside the package. That makes the handoff
> inspectable, even while the editorial decision remains open.

## Scene 5 Connect the approach to client needs

**Target time:** 2:10 to 2:40

**Screen action:** Show a simple editorial graphic with the sequence
“Inputs → evidence → human review → decision record.” Below it, reveal three
possible domains: “Research documents,” “Engineering evidence,” and “Internal
review.” Label these “Possible custom applications.” Do not present them as
existing integrations or substitute a fictional working interface.

**On-screen caption:** A workflow designed around your decision and constraints

**Spoken narration:**

> Video is the example, not the limit of the approach. A similar workflow
> could be designed around research documents, engineering evidence, or
> internal review processes. For a client, I'd start with the decision,
> the available inputs, and the constraints—then determine what to build,
> how it should connect to existing tools, and how we'd evaluate whether
> it is useful.

## Scene 6 Invite a focused consulting conversation

**Target time:** 2:40 to 3:00

**Screen action:** Finish with Brian's name, “Applied AI and R&D consulting,”
`CorrespondenceMatrices.com`, and “Request a 20-minute fit call.” Hold the
address during the final sentence. Avoid a second product summary or an
extended silent end card. Do not submit a contact form during the recording.

**On-screen caption:** What decision does your team need to make?

**Spoken narration:**

> If your team has scattered analysis, or an idea that needs to become a
> testable system, visit CorrespondenceMatrices.com to request a twenty-minute
> fit call. We'll discuss your goals, constraints, and the decision you need
> to make—and identify a practical next step.

## Pacing and sound

- Let the delivery determine the final length; aim for roughly three minutes
  rather than forcing an exact runtime.
- Pause at meaningful transitions or where text needs reading, not after every
  click. Keep the cursor still while explaining, then move it deliberately.
- Record narration separately if live interaction disrupts delivery. Cuts must
  preserve the real workflow and must not manufacture results.
- Keep narration prominent. Music is optional and must not obscure words.
  Provide accurate captions without covering important interface text.
- Assess silence, vocal energy, and readability from a rough cut. Cut dead air
  rather than filling it with extra claims.

## Claim boundaries and accompanying page copy

This is a working prototype and saved analysis example. It does not demonstrate
live analysis, original-video playback, automatic edits, audience prediction,
collaborative synchronization, or automatic note persistence. Scores are review
cues, not validated diagnoses of a creative problem. No measured client return,
time saving, or deployment outcome is claimed.

Some source references are provenance rather than bundled files. Do not portray
those as available evidence or functioning source links. Preserve the separate
fallback-link audit in the technical companion; a clean link check does not
establish analytical usefulness or complete source coverage.

Suggested copy beside the video:

> A working video-review prototype illustrating how I connect recorded analysis,
> source references, and human decisions into an inspectable workflow. The demo
> uses saved analysis, excludes original media, and requires notes to be saved
> separately. Similar workflows would be scoped and evaluated around a client's
> inputs, constraints, and decisions.

Offer the technical walkthrough as an optional companion, not a prerequisite
for understanding this case study.

## Viewer check before final production

Show the rough cut to a few representative viewers without explaining its
intended message first. Ask:

- What problem does this system address?
- What do you think Brian designed or contributed?
- What similar need in your organization could this approach address?
- What works in the demonstration, and what would need further development?
- Where did your attention drop, and what was confusing?
- What would you want to know before requesting a conversation?

The video is ready when viewers can describe the problem, your contribution,
and a plausible reason to contact you without mistaking the prototype for a
finished product. A positive reaction alone is not sufficient.

## Producer source references

The demonstration follows `demo_walkthrough.html` and `demo_walkthrough.json`
inside `Videos/Brian/Corpus_analysis/portable_review_package`, the named video's
opening-segment timeline and context, `timeline/temporal_evidence_index.json`,
and `recommendations/recommendation_traceability.json`. The scoped range is
0.00–14.64 seconds and the matching recommendation is `RECTRC_2ae092334497a2fc`.
Keep those records aligned if the export changes before recording.

The consulting invitation follows the current
[Correspondence Matrices consulting page](https://www.correspondencematrices.com/),
which offers a 20-minute fit call focused on goals, constraints, and a useful
next step. Confirm the visible contact route before publishing the finished video.
