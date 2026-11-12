# Portable Link Rewriting

The rewriter handles HTML `href`/`src`/`srcset`, CSS `url(...)`, Markdown links/images, and JSON fields that are likely to be live asset paths.

No live link may use an absolute filesystem path, `file:///`, remote HTTP(S), or a relative path that escapes the package root. Historical paths may remain only in provenance metadata fields such as `original_source_path`, `original_video_path`, `source_analysis_root`, and `package_root`.

Raw video and audio links are rewritten to `raw_media_excluded.html` unless `--portable-include-raw-media` is explicitly used.
