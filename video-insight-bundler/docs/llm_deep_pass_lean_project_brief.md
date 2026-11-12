# LLM Deep-Pass Brief for Leaning the Project

This document defines the information packet, investigation order, and execution commands to give an LLM or human reviewer when asking for a deep pass on `video-insight-bundler` with the goal of making the project leaner without breaking the portable offline deliverable.

The current conservative classification remains:

`operational beta+ / internal beta_plus`

Do not ask the reviewer to promote the project to release-candidate status unless existing governance evidence independently supports that conclusion.

## Goal

The deep pass should answer:

- Which documents are canonical, current, and required?
- Which documents are stale, duplicative, superseded, or better merged?
- Which source files are essential to the current pipeline?
- Which generated artifacts are required outputs versus historical evidence?
- Which tests protect core behavior?
- Which fixtures, docs, generated outputs, or old phase files can be archived, consolidated, or excluded from normal review?
- Which files must not be removed because they are part of the output contract, portable package contract, validation contract, or governance evidence?
- What exact, staged plan would make the project leaner while preserving behavior?

The reviewer should produce a plan first. Code deletion or large file moves should happen only after the plan identifies risk, owner files, tests, and rollback points.

## What To Feed The LLM First

Provide these files before asking for recommendations:

- `README.md`
- `tools/video-insight-bundler/README.md`
- `docs/implementation_report.md`
- `tools/video-insight-bundler/docs/implementation_report.md`
- `docs/output_contract.md`
- `tools/video-insight-bundler/docs/output_contract.md`
- `docs/portable_export_package.md`
- `docs/offline_dashboard_package.md`
- `docs/portable_link_rewriting.md`
- `docs/portable_package_validation.md`
- `docs/llm_deep_pass_lean_project_brief.md`

Also provide the current generated validation artifacts:

- `tools/video-insight-bundler/Videos/Brian/Corpus_analysis/portable_review_package/portable_package_manifest.json`
- `tools/video-insight-bundler/Videos/Brian/Corpus_analysis/portable_review_package/portable_package_validation_report.json`
- `tools/video-insight-bundler/Videos/Brian/Corpus_analysis/portable_review_package/package_diff_report.json`
- `tools/video-insight-bundler/Videos/Brian/Corpus_analysis/portable_review_package/package_size_report.json`
- `tools/video-insight-bundler/Videos/Brian/Corpus_analysis/portable_review_package/exclusion_manifest.json`
- `tools/video-insight-bundler/Videos/Brian/Corpus_analysis/portable_review_package/manifests/asset_dependency_report.json`
- `tools/video-insight-bundler/Videos/Brian/Corpus_analysis/portable_review_package/manifests/external_display_assets_copied.json`
- `tools/video-insight-bundler/Videos/Brian/Corpus_analysis/portable_review_package/validation/offline_dashboard_hardening_report.json`
- `tools/video-insight-bundler/Videos/Brian/Corpus_analysis/portable_review_package/validation/portable_integrity_report.json`
- `tools/video-insight-bundler/Videos/Brian/Corpus_analysis/portable_review_package/validation/portable_privacy_scan_report.json`

If context is limited, start with the README files, output contracts, portable docs, implementation reports, and validation summary JSON. Add source files only after the reviewer has identified the subsystem boundaries.

## Source Files To Investigate

Start with orchestration and CLI entrypoints:

- `tools/video-insight-bundler/analyze_corpus.py`
- `tools/video-insight-bundler/src/corpus_runner.py`
- `tools/video_insight_bundler/portable_export_package.py`

Then inspect portable-package infrastructure:

- `tools/video-insight-bundler/src/portable_export_package.py`
- `tools/video-insight-bundler/src/asset_dependency_scanner.py`
- `tools/video-insight-bundler/src/portable_exclusion_policy.py`
- `tools/video-insight-bundler/src/portable_link_rewriter.py`
- `tools/video-insight-bundler/src/offline_dashboard_hardening.py`
- `tools/video-insight-bundler/src/portable_package_validator.py`
- `tools/video-insight-bundler/src/portable_integrity_checker.py`
- `tools/video-insight-bundler/src/portable_package_diff.py`
- `tools/video-insight-bundler/src/portable_package_size_report.py`

Then inspect shared support modules used by many phases:

- `tools/video-insight-bundler/src/stability.py`
- `tools/video-insight-bundler/src/reporting.py`
- `tools/video-insight-bundler/src/schema_validation.py`
- `tools/video-insight-bundler/src/dashboard*.py` where present
- `tools/video-insight-bundler/src/*registry*.py`
- `tools/video-insight-bundler/src/*validation*.py`
- `tools/video-insight-bundler/src/*governance*.py`
- `tools/video-insight-bundler/src/*recommendation*.py`
- `tools/video-insight-bundler/src/*interpretation*.py`

Then inspect tests:

- `tests/test_video_insight_bundler*.py`
- `tests/test_video_insight_bundler_portable_export_package.py`
- `tests/test_video_insight_bundler_portable_link_rewriter.py`
- `tests/test_video_insight_bundler_asset_dependency_scanner.py`
- `tests/test_video_insight_bundler_portable_package_validator.py`
- `tests/test_video_insight_bundler_offline_dashboard_hardening.py`

## Document Inventory Strategy

The repo has many phase documents. The reviewer should classify documents into these buckets:

- Canonical: current docs required to understand, run, validate, or maintain the system.
- Contract: docs that define expected outputs, validation gates, safety limits, or CLI behavior.
- Subsystem reference: docs that explain a specific active subsystem.
- Historical phase evidence: useful for audit/history, but not required in daily context.
- Superseded duplicate: older versions replaced by a newer doc.
- Draft or speculative: planning material not implemented or not part of current behavior.
- Generated output documentation: files created by a run and not intended as source-of-truth docs.
- Archive candidate: safe to move under an archive folder if links are updated or left intentionally historical.
- Removal candidate: safe to delete only if no tests, docs, manifests, or dashboards reference it.

The reviewer should not assume that a document is removable because it is old. Some old phase docs may encode safety constraints, governance decisions, or output contracts that later code still follows.

## File Inventory Strategy

The reviewer should classify source and artifact files into:

- Runtime source required by CLI.
- Runtime source imported indirectly.
- Portable export source.
- Static assets required by dashboards.
- Schema files required by validation.
- Tests and fixtures required for regression coverage.
- Generated outputs required as sample evidence.
- Generated outputs that should not be committed or used as source.
- Large artifacts that should remain excluded from portable packages.
- Raw media that must stay excluded by default.
- Cache/temp/dependency files that should not be copied or reviewed.

Use import graphs, `rg`, test execution, manifests, and package validation rather than filename intuition alone.

## Questions The LLM Should Answer

Ask the LLM to produce:

1. A canonical-document set.
2. A duplicate/superseded-document map.
3. A source-file dependency map.
4. A generated-output versus source-file boundary.
5. A portable-package critical-path map.
6. A test coverage map for each critical subsystem.
7. A list of files that are clearly safe to ignore in future LLM context.
8. A list of files that are archive candidates.
9. A list of files that are deletion candidates, if any.
10. A staged lean-down plan with verification commands after each stage.
11. A rollback plan.
12. Risks and unknowns that require manual confirmation.

The plan should prefer consolidation and archival before deletion.

## Suggested LLM Prompt

Use a prompt like this:

```text
You are reviewing the local-first video-insight-bundler project. The current classification is operational beta+ / internal beta_plus; do not promote readiness.

Goal: propose a deep-pass plan to make the project leaner without breaking the analysis pipeline, static dashboards, portable review package, validation evidence, or offline zip deliverable.

First read the supplied README files, implementation reports, output contracts, portable export docs, and validation JSON. Then identify which additional source files and tests must be inspected. Do not propose deletions until you have classified documents and files by role, dependency, and risk.

Produce:
- canonical docs
- docs to merge
- docs to archive
- docs that are likely stale or superseded
- source files required by runtime
- files required by portable export
- generated artifacts that are required evidence
- generated artifacts that should be excluded from future context
- tests needed for confidence
- staged lean-down plan
- commands to validate each stage
- risks, unknowns, and manual review points

Preserve current behavior and classification.
```

## Commands For Discovery

Run these from the repository root:

```powershell
rg --files tools/video-insight-bundler
rg --files docs
rg --files tests | rg "video_insight_bundler"
rg -n "portable_export|portable_review_package|zip-export|portable-export|output_contract|implementation_report" README.md docs tools/video-insight-bundler tests
rg -n "import .*portable|from .*portable|portable_package|asset_dependency|link_rewriter|offline_dashboard" tools/video-insight-bundler tests
```

Useful size and duplicate discovery:

```powershell
Get-ChildItem -Recurse -File tools/video-insight-bundler | Sort-Object Length -Descending | Select-Object -First 50 FullName,Length
Get-ChildItem -Recurse -File docs | Group-Object Name | Where-Object { $_.Count -gt 1 } | Select-Object Name,Count
```

Useful generated-output checks:

```powershell
Get-ChildItem -Recurse -File tools/video-insight-bundler/Videos/Brian/Corpus_analysis/portable_review_package | Measure-Object
Get-ChildItem -Recurse -File tools/video-insight-bundler/Videos/Brian/Corpus_analysis/portable_review_package | Sort-Object Length -Descending | Select-Object -First 25 FullName,Length
```

## Compilation And Validation Commands

Use these before and after any lean-down stage.

Compile Python files:

```powershell
py -3 -m compileall tools\video-insight-bundler tests
```

Run focused portable tests:

```powershell
py -3 -m unittest discover tests -p "test_video_insight_bundler_portable*.py"
```

Run all video-insight-bundler tests:

```powershell
py -3 -m unittest discover tests -p "test_video_insight_bundler*.py"
```

Run all tests if feasible:

```powershell
py -3 -m unittest discover tests
```

If full tests fail because of unrelated optional dependencies outside `video-insight-bundler`, report them separately and do not treat them as a portable export failure if the video-insight-bundler tests pass.

## Standalone Portable Package Generation

To regenerate analysis and the portable zip from the normal corpus command:

```powershell
py -3.13 .\tools\video-insight-bundler\analyze_corpus.py --corpus "C:\Users\brian\Documents\Book-Agents\tools\video-insight-bundler\Videos\Brian\Corpus" --include "C:\Users\brian\Documents\Book-Agents\tools\video-insight-bundler\Videos\Brian\Why Should Anyone Listen to you Anyway - Brian Theory.mp4" --force --verbose --portable-export --zip-export
```

To compile/export the standalone portable files from an existing `Corpus_analysis` tree without rerunning the full corpus analysis:

```powershell
py -3 -m tools.video_insight_bundler.portable_export_package --source "C:\Users\brian\Documents\Book-Agents\tools\video-insight-bundler\Videos\Brian\Corpus_analysis" --zip
```

Optional explicit destination:

```powershell
py -3 -m tools.video_insight_bundler.portable_export_package --source "C:\path\to\Corpus_analysis" --dest "C:\path\to\portable_review_package" --zip
```

The generated standalone deliverables are:

- `Corpus_analysis/portable_review_package/index.html`
- `Corpus_analysis/portable_review_package/PACKAGE_SUMMARY.md`
- `Corpus_analysis/portable_review_package/portable_package_manifest.json`
- `Corpus_analysis/portable_review_package/portable_package_validation_report.json`
- `Corpus_analysis/portable_review_package/package_diff_report.json`
- `Corpus_analysis/portable_review_package/package_size_report.json`
- `Corpus_analysis/portable_review_package/exclusion_manifest.json`
- `Corpus_analysis/portable_review_package.zip`

The recipient should unzip `portable_review_package.zip` and open `portable_review_package/index.html` directly in a browser.

## Standalone Package Extraction Simulation

After creating the zip, simulate a recipient workflow:

```powershell
$zip = "C:\Users\brian\Documents\Book-Agents\tools\video-insight-bundler\Videos\Brian\Corpus_analysis\portable_review_package.zip"
$dest = Join-Path $env:TEMP ("portable_extract_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $dest | Out-Null
Expand-Archive -Path $zip -DestinationPath $dest
py -3 - <<'PY'
from pathlib import Path
import sys, os
sys.path.insert(0, str(Path("tools/video-insight-bundler/src").resolve()))
from portable_package_validator import validate_portable_package
package = next(Path(os.environ["TEMP"]).glob("portable_extract_*/portable_review_package"))
report = validate_portable_package(package)
print(report["validation_passed"])
print(report.get("summary", {}))
PY
```

If PowerShell heredoc behavior is inconvenient, run validation with a short temporary Python file or invoke the validator through the existing export workflow.

## Path-Length Check For Windows

Because Windows Explorer can fail around long paths, check the generated portable package:

```powershell
$root = (Resolve-Path tools/video-insight-bundler/Videos/Brian/Corpus_analysis/portable_review_package).Path
Get-ChildItem -Recurse -File $root |
  ForEach-Object {
    [PSCustomObject]@{
      FullLength = $_.FullName.Length
      RelLength = $_.FullName.Substring($root.Length + 1).Length
      Rel = $_.FullName.Substring($root.Length + 1)
    }
  } |
  Sort-Object FullLength -Descending |
  Select-Object -First 20 |
  Format-Table -AutoSize
```

The portable exporter should keep generated package paths short enough for normal Windows copying. If paths regress, inspect `portable_export_package.py` path-shortening behavior before changing generated files manually.

## Do Not Remove Without Strong Evidence

Treat these as protected until the reviewer proves otherwise:

- CLI entrypoints.
- Corpus runner orchestration.
- Portable export modules.
- Link rewriting, dependency scanning, validation, exclusion policy, size/diff reporting.
- Static assets used by dashboards.
- Schemas and validation reports.
- Tests for portable export and video-insight-bundler behavior.
- Governance/readiness docs that define current conservative classification.
- Output contract docs.
- Generated portable package validation artifacts used as evidence.

## Safe Leaning Patterns

Prefer these operations:

- Create a canonical-doc index instead of feeding every historical phase doc to every future LLM.
- Move superseded docs to an archive folder after updating references.
- Merge mirrored docs only if the project no longer needs root-level and tool-level copies.
- Exclude generated packages, zips, cache folders, raw media, and validation-heavy outputs from routine LLM context unless the task is about export correctness.
- Keep generated-output samples small and representative.
- Add `.gitignore` or context-exclusion guidance for generated artifacts if they are not meant to be source-controlled.
- Preserve validation reports as evidence but avoid loading full reports into every LLM prompt.

## Required Final Output From The Deep Pass

The reviewer should end with:

- Proposed canonical document set.
- Proposed archive/merge/delete document set.
- Proposed source-file critical path.
- Proposed generated-artifact policy.
- Proposed test matrix.
- Staged change plan.
- Validation commands for each stage.
- Explicit non-goals.
- Explicit files not to touch.
- Current classification: `operational beta+ / internal beta_plus`.

