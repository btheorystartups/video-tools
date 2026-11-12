# Sample Command

```powershell
py -3.13 .\tools\video-insight-bundler\analyze_video.py --video "C:\path\to\video.mp4" --output .\output\video_analysis --force --verbose
```

Transcription is enabled by default. To run metadata, frame sampling, fixed-window segmentation, and heuristic bundle writing without transcription:

```powershell
py -3.13 .\tools\video-insight-bundler\analyze_video.py --video "C:\path\to\video.mp4" --output .\output\video_analysis --no-transcribe --force
```

To use an existing OpenAI Whisper JSON or native transcript JSON:

```powershell
py -3.13 .\tools\video-insight-bundler\analyze_video.py --video "C:\path\to\video.mp4" --transcript-import "C:\path\to\transcript.json" --output .\output\video_analysis --force --verbose
```

The tool does not require a sample video in this repository.
