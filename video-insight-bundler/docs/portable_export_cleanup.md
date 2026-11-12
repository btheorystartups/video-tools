# Portable Export Cleanup

Dry run:

```powershell
py -3 .\tools\video-insight-bundler\src\portable_export_package.py --source "C:\path\to\Corpus_analysis" --clean-dry-run
```

Actual cleanup:

```powershell
py -3 .\tools\video-insight-bundler\src\portable_export_package.py --source "C:\path\to\Corpus_analysis" --clean-old-exports
```

Cleanup removes old portable packages, zips, and extract folders, not source analysis artifacts.
