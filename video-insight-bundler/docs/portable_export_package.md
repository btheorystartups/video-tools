# Portable Export Package

The package includes a five-minute evidence walkthrough when a named video and
its segment-context pages are available. See [video_walkthrough.md](video_walkthrough.md).
Missing-asset fallback links are disclosed in
`validation/portable_fallback_link_audit.json`; they are not equivalent to
available evidence even when broken-link validation is clean. Review workspaces
offer an explicit notes/checklist JSON export with a manual-save fallback, not
automatic persistence or synchronization.

Phase V55 adds `portable_review_package/`, a standalone offline deliverable generated from `Corpus_analysis/`.

Use `--portable-export` to generate the package and `--zip-export` to create `portable_review_package.zip`. Existing analysis trees can be exported with:

```powershell
Book-Agents\.venv\Scripts\python.exe video-insight-bundler\src\portable_export_package.py --source "C:\path\to\Corpus_analysis" --dest "C:\path\to\portable_review_package" --zip --validate-extracted
```

The package preserves dashboards, graphs, boards, contact sheets, JSON, Markdown, manifests, schemas, validation evidence, interpretation artifacts, recommendations, evidence, governance, timelines, snapshots, diffs, replay outputs, review sheets, CSS, and JavaScript. Raw media, caches, temporary files, dependency folders, development scratch files, and risky credential-like files are excluded by default.

Recipients unzip the package and open `index.html` directly. Classification remains operational beta+ / internal beta_plus.

## Phase V56 Profiles And Reports

V56 supports `--export-profile minimal|review|audit|full`, `--portable-dedupe none|report|safe`, `--validate-extracted`, `--clean-dry-run`, and `--clean-old-exports`.

`review` is the default. Raw media and previous portable packages are excluded unless explicitly requested.

## Phase V57 Dashboard Governance

V57 adds governance-first navigation over the exported corpus. `index.html` is now hierarchical and uses start-here links, review pathways, ranked category sections, search/filter, and collapsed advanced/audit inventories instead of a flat list of every generated page.

New package reports include:

- `dashboard_governance_registry.json`
- `artifact_importance_registry.json`
- `artifact_orphan_registry.json`
- `review_pathways.json`
- `dashboard_consolidation_report.json`
- `dashboard_tag_registry.json`
- `canonical_asset_registry.json`
- `review_coherence_report.json`

`--dashboard-consolidation none|grouped|aggressive` controls drilldown grouping metadata. The default is `grouped`. Additional profile names are scaffolded: `executive`, `presentation`, `investigation`, and `diff_only`.

## V67-V72 Operating Layer

Portable packages now include cache identity/invalidation evidence, zip assembly reports, optional delta manifests, topology simplification reports, guided review workbench files, CI smoke evidence, benchmark evidence, and release-readiness evidence. Normal full zip behavior remains compatible, and raw video remains excluded by default.

## Metadata Compaction

The exporter stores cache artifact records once in `artifact_change_graph.json`. `export_cache_registry.json` points to these shared records; `load_previous_cache()` reconstructs the source, package-path, and identity indexes and still reads older cache files. Keep both files together when reusing an export cache. Missing or invalid shared records trigger a cache miss.

After all dashboards and reports are generated, byte-identical JSON mirrors of at least 64 KiB under `governance/`, `validation/`, or `manifests/` are consolidated into their same-name package-root file. Navigation links and relative metadata references are updated to that canonical file. Unique evidence, display assets, and original absolute provenance are retained. `portable_metadata_compaction_report.json` records every consolidation and the saved bytes.

Final folder validation and requested ZIP extraction validation run after compaction. The final ZIP contains the reconciled manifest, size report, and extraction evidence. Backup folders named `portable_review_package_*` are excluded from future source exports.

To compact an already-generated package, work on a backup or staging copy and run from the `Tools` directory:

```powershell
Book-Agents\.venv\Scripts\python.exe video-insight-bundler\src\portable_metadata_compaction.py --package "C:\path\to\portable_review_package" --zip --validate-extracted
```
