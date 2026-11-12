# Corpus Intelligence System

Corpus analysis runs the existing per-video analyzer across a local folder of source videos, then writes corpus-level review artifacts to a sibling `Corpus_analysis/` folder.

Put source videos in:

```text
tools/video-insight-bundler/Videos/Brian/Corpus/
```

Supported extensions: `.mp4`, `.mov`, `.mkv`, `.m4v`, `.avi`, `.webm`.

Run:

```powershell
py -3.13 .\tools\video-insight-bundler\analyze_corpus.py --corpus "C:\Users\brian\Documents\Book-Agents\tools\video-insight-bundler\Videos\Brian\Corpus" --include "C:\Users\brian\Documents\Book-Agents\tools\video-insight-bundler\Videos\Brian\Why Should Anyone Listen to you Anyway - Brian Theory.mp4" --force --verbose
```

The runner writes one managed per-video analysis folder beside each source video and writes corpus-level outputs under:

```text
tools/video-insight-bundler/Videos/Brian/Corpus_analysis/
```

Corpus outputs include index, intelligence, fingerprint, archetypes, comparative stabilization, corpus recommendations, corpus readiness, and summary artifacts.

Corpus, workbench, audit, governance, and release-candidate outputs are deterministic editorial-review artifacts. They do not perform autonomous editing, semantic inference, identity recognition, cloud analysis, or media/timeline mutation.
## Phase 27 RC Hardening

Corpus intelligence now feeds deterministic RC hardening artifacts. Recurring pressure patterns, recommendation families, readiness blockers, and editorial archetypes are used to compress review queues, explain governance threshold gaps, rank blockers, and plan human review actions.

The corpus intelligence pass remains local and conservative. It does not add semantic runtime, embeddings, vector search, cloud APIs, LLM calls, autonomous editing, Resolve integration, or media/timeline mutation.

RC hardening and remediation outputs are deterministic review-planning artifacts. They do not apply edits, mutate media, change timelines, perform semantic inference, or make autonomous release decisions.
