# New Video Portable Export Workflow

Run:

```powershell
py -3.13 .\tools\video-insight-bundler\export_new_video.py `
  --video "C:\path\to\new_video.mp4" `
  --corpus "C:\path\to\Corpus" `
  --output-root "C:\path\to\Exports" `
  --package-name "my_new_video_analysis" `
  --export-profile review `
  --zip `
  --validate-extracted
```

The command prints the `index.html` to open and the zip to send.

## V71 Dry-Run And Real-Video Controls

New flags: `--real-video-required`, `--simulate-if-missing`, `--dry-run-plan`, and `--write-run-plan`.

```powershell
python tools/video-insight-bundler/export_new_video.py --video path/to/video.mp4 --output-root output/new_video --dry-run-plan --simulate-if-missing
```

This writes `new_video_run_plan.json` with exact commands and expected outputs when no real video is available.
