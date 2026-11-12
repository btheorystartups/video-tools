#!/usr/bin/env python3
"""Corpus-level entry point for the standalone Video Insight Bundler."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from corpus_runner import run_corpus
from portable_export_package import build_portable_package


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic local video analysis over a corpus and write corpus-level intelligence.")
    parser.add_argument("--corpus", required=True, help="Directory containing source videos.")
    parser.add_argument("--include", action="append", default=[], help="Additional source video to include. Can be repeated.")
    parser.add_argument("--force", action="store_true", help="Reuse per-video output folders and clean only managed analysis artifacts.")
    parser.add_argument("--verbose", action="store_true", help="Print per-video analyzer progress.")
    parser.add_argument("--profile", help="Optional per-video analysis profile path.")
    parser.add_argument("--revision-profile", help="Optional per-video revision profile path.")
    parser.add_argument("--portable-export", action="store_true", help="Build a self-contained portable_review_package after corpus generation.")
    parser.add_argument("--zip-export", action="store_true", help="Build portable_review_package.zip after corpus generation. Implies --portable-export.")
    parser.add_argument("--portable-export-root", help="Destination portable package root. Defaults to <Corpus_analysis>/portable_review_package.")
    parser.add_argument("--export-profile", default="review", choices=["minimal", "review", "audit", "full", "executive", "presentation", "investigation", "diff_only"], help="Portable export profile. Default review.")
    parser.add_argument("--validate-export", action="store_true", help="Run portable package validation. Portable exports validate by default; this flag is kept for command clarity.")
    parser.add_argument("--validate-extracted", action="store_true", help="Validate an extracted copy of the generated zip.")
    parser.add_argument("--validation-tier", default="standard", choices=["quick", "standard", "strict", "extracted_full"], help="Portable validation tier. Default standard.")
    parser.add_argument("--generation-mode", default="hybrid", choices=["eager", "lazy", "hybrid"], help="Portable analytical generation mode. Default hybrid.")
    parser.add_argument("--cache-mode", default="auto", choices=["auto", "refresh", "off"], help="Portable incremental cache policy. Default auto.")
    parser.add_argument("--zip-mode", default="full", choices=["full", "optimized", "delta"], help="Portable zip assembly mode. Default full.")
    parser.add_argument("--delta-zip", action="store_true", help="Generate a sidecar delta zip.")
    parser.add_argument("--base-export", help="Base package folder for delta comparison.")
    parser.add_argument("--reuse-zip-manifest", action="store_true", help="Reuse prior zip manifest for planning when available.")
    parser.add_argument("--topology-simplify", default="safe", choices=["none", "safe", "aggressive"], help="Topology simplification mode. Default safe.")
    parser.add_argument("--review-session", choices=["executive", "governance", "recommendation", "evidence", "interpretation", "timeline", "audit", "diff"], help="Preferred guided review pathway.")
    parser.add_argument("--review-style", default="balanced", choices=["executive", "balanced", "audit_dense"], help="Review synthesis style. Default balanced.")
    parser.add_argument("--dashboard-density", default="balanced", choices=["compact", "balanced", "expanded"], help="Dashboard information density. Default balanced.")
    parser.add_argument("--artifact-reduction", default="balanced", choices=["conservative", "balanced", "aggressive"], help="Artifact reduction mode. Default balanced.")
    parser.add_argument("--change-summary", default="balanced", choices=["concise", "balanced", "full"], help="Change summary detail. Default balanced.")
    parser.add_argument("--review-workspace", action="store_true", help="Generate static review workspace pages.")
    parser.add_argument("--generate-review-checklists", action="store_true", help="Generate reviewer checklists.")
    parser.add_argument("--generate-handoff-summary", action="store_true", help="Generate handoff summary templates.")
    parser.add_argument("--ci-smoke", action="store_true", help="Generate CI smoke evidence.")
    parser.add_argument("--benchmark-export", action="store_true", help="Generate benchmark evidence.")
    parser.add_argument("--portable-dedupe", default="report", choices=["none", "report", "safe"], help="Duplicate handling mode. Default report.")
    parser.add_argument("--dashboard-consolidation", default="grouped", choices=["none", "grouped", "aggressive"], help="Dashboard drilldown consolidation mode. Default grouped.")
    parser.add_argument("--portable-clean-dry-run", action="store_true", help="List old portable packages before export without deleting them.")
    parser.add_argument("--portable-clean", action="store_true", help="Remove old portable packages before export.")
    parser.add_argument("--portable-include-raw-media", action="store_true", help="Explicitly include raw source media in the portable package. Default excludes raw media.")
    parser.add_argument("--portable-strict", default="true", choices=["true", "false"], help="Run strict portable validation. Default true.")
    parser.add_argument("--portable-allow-provenance-absolute-paths", default="true", choices=["true", "false"], help="Allow absolute paths only in provenance metadata. Default true.")
    parser.add_argument("--portable-max-file-size-warning-mb", type=float, default=100.0, help="Warn about display assets above this size. Default 100.")
    parser.add_argument("--portable-copy-mode", default="copy", choices=["copy"], help="Portable export copy mode. Default copy.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    corpus_dir = Path(args.corpus).expanduser().resolve()
    if not corpus_dir.exists() or not corpus_dir.is_dir():
        print(f"Corpus directory not found: {corpus_dir}", file=sys.stderr)
        return 2
    includes = [Path(item).expanduser().resolve() for item in args.include]
    missing = [str(path) for path in includes if not path.exists()]
    if missing:
        print(f"Included video(s) not found: {', '.join(missing)}", file=sys.stderr)
        return 2
    profile = Path(args.profile).expanduser().resolve() if args.profile else None
    revision_profile = Path(args.revision_profile).expanduser().resolve() if args.revision_profile else None
    result = run_corpus(corpus_dir, includes, force=args.force, verbose=args.verbose, profile=profile, revision_profile=revision_profile)
    if args.portable_export or args.zip_export:
        if args.portable_clean or args.portable_clean_dry_run:
            from portable_cleanup import clean_old_exports

            clean_old_exports(Path(result["output_dir"]), dry_run=args.portable_clean_dry_run)
        export = build_portable_package(
            Path(result["output_dir"]),
            Path(args.portable_export_root).expanduser().resolve() if args.portable_export_root else None,
            zip_export=args.zip_export,
            include_raw_media=args.portable_include_raw_media,
            strict=args.portable_strict == "true",
            allow_provenance_absolute_paths=args.portable_allow_provenance_absolute_paths == "true",
            max_file_size_warning_mb=args.portable_max_file_size_warning_mb,
            copy_mode=args.portable_copy_mode,
            export_profile=args.export_profile,
            dedupe=args.portable_dedupe,
            dashboard_consolidation=args.dashboard_consolidation,
            validate_extracted=args.validate_extracted,
            validation_tier=args.validation_tier,
            generation_mode=args.generation_mode,
            cache_mode=args.cache_mode,
            zip_mode=args.zip_mode,
            delta_zip=args.delta_zip,
            base_export=Path(args.base_export).expanduser().resolve() if args.base_export else None,
            reuse_zip_manifest=args.reuse_zip_manifest,
            topology_simplify=args.topology_simplify,
            review_session=args.review_session,
            review_style=args.review_style,
            dashboard_density=args.dashboard_density,
            artifact_reduction=args.artifact_reduction,
            change_summary=args.change_summary,
            review_workspace=args.review_workspace,
            generate_review_checklists=args.generate_review_checklists,
            generate_handoff_summary=args.generate_handoff_summary,
            ci_smoke=args.ci_smoke,
            benchmark_export=args.benchmark_export,
            requested_video=includes[0] if includes else None,
        )
        validation = export["validation"]
        size_summary = export["size_report"].get("summary", {})
        print("Portable export complete.")
        print("")
        print(f"Open first:\n{(Path(export['package_root']) / 'index.html').resolve()}")
        if export.get("zip_path"):
            print(f"\nSend this zip:\n{Path(export['zip_path']).resolve()}")
        print("")
        print(f"Profile:\n{args.export_profile}")
        print(f"\nRaw video included:\n{'yes' if args.portable_include_raw_media else 'no'}")
        print(f"\nValidation:\n{'passed' if validation.get('validation_passed') else 'failed'}")
        print(f"\nBroken links:\n{validation.get('broken_link_count')}")
        print(f"\nMissing assets:\n{validation.get('missing_asset_count')}")
        print(f"\nPackage size:\n{round((size_summary.get('total_package_size_bytes') or 0) / (1024 * 1024), 2)} MB")
        print(f"\nZip size:\n{round((size_summary.get('zip_size_bytes') or 0) / (1024 * 1024), 2) if size_summary.get('zip_size_bytes') is not None else 'not generated'} MB")
    print(f"Corpus analysis bundle written to: {result['output_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
