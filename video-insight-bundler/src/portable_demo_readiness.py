"""Evidence-backed walkthrough and visible audit of unresolved HTML fallbacks."""

from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote

from portable_exclusion_policy import should_exclude_path
from stability import write_json
from static_review_notes import notes_panel


class _FallbackParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        for name in ('href', 'src'):
            value = attributes.get(name, '')
            if 'missing_asset_placeholder' in value:
                self.rows.append({'attribute': name, 'fallback': value, 'original_reference': attributes.get('data-original-reference')})


def audit_fallback_links(package_root: Path, source_root: Path, profile: str) -> dict:
    rows = []
    for path in sorted(package_root.rglob('*.html')):
        parser = _FallbackParser()
        parser.feed(path.read_text(encoding='utf-8'))
        rel = path.relative_to(package_root)
        for row in parser.rows:
            raw = unquote((row.get('original_reference') or '').split('#')[0].split('?')[0])
            target = (source_root / rel.parent / raw).resolve() if raw else None
            classification = 'unattributed_placeholder'
            rule = None
            if target and target.is_relative_to(source_root.resolve()):
                if target.is_file():
                    excluded, _, rule = should_exclude_path(target, source_root, export_profile=profile)
                    classification = 'profile_excluded' if excluded else 'available_source_not_packaged'
                else:
                    classification = 'source_reference_missing'
            elif raw:
                classification = 'outside_source_root'
            rows.append({'page': rel.as_posix(), **row, 'classification': classification, 'exclusion_rule': rule})
    counts = {kind: sum(row['classification'] == kind for row in rows) for kind in sorted({row['classification'] for row in rows})}
    report = {'analysis_status': 'complete', 'summary': {'fallback_link_count': len(rows), 'by_classification': counts}, 'links': rows,
              'limitation': 'Working placeholder links are not equivalent to available evidence. Raw-media exclusions are separate and intentional.'}
    (package_root / 'validation').mkdir(parents=True, exist_ok=True)
    write_json(package_root / 'validation/portable_fallback_link_audit.json', report)
    return report


def build_demo_walkthrough(package_root: Path) -> dict:
    path = package_root / 'timeline/temporal_evidence_index.json'
    entries = json.loads(path.read_text(encoding='utf-8')).get('temporal_evidence_entries', []) if path.exists() else []
    for row in entries:
        context = package_root / f"visualizations/timeline/segment_context_{row.get('video_id')}_{row.get('segment_id')}.html"
        if context.is_file():
            label = f"{row.get('timestamp_start', 0):.2f}–{row.get('timestamp_end', 0):.2f} sec"
            text = context.read_text(encoding='utf-8').replace(f"Segment Context {row.get('segment_id')}", f"Segment Context: {label}")
            context.write_text(text, encoding='utf-8')
    # Existing saved analysis HTML predates the readable renderer. Upgrade only
    # its exact segment labels; do not regenerate or reinterpret source analysis.
    for video in {row.get('video_id') for row in entries}:
        timeline = package_root / f'visualizations/timeline/video_timeline_{video}.html'
        if timeline.is_file():
            text = timeline.read_text(encoding='utf-8')
            video_entries = [row for row in entries if row.get('video_id') == video]
            title = Path(str(video_entries[0].get('source_video', '')).replace('\\', '/')).name
            text = text.replace(f'Video Timeline {video}', f'Video Timeline: {escape(title)}')
            for row in video_entries:
                label = f"{row.get('timestamp_start', 0):.2f}–{row.get('timestamp_end', 0):.2f} sec"
                text = text.replace(f"<span>{row.get('segment_id')}</span>", f"<span>{label}</span>")
            timeline.write_text(text, encoding='utf-8')
    candidates = [row for row in entries if not re.fullmatch(r'video_\d+\.[^.]+', Path(str(row.get('source_video', '')).replace('\\', '/')).name, re.I)]
    candidates = [row for row in candidates if (package_root / f"visualizations/timeline/segment_context_{row.get('video_id')}_{row.get('segment_id')}.html").is_file()]
    if not candidates:
        return {'available': False, 'reason': 'No named video with packaged segment context is available.'}
    entry = max(candidates, key=lambda row: (bool(row.get('recommendations')), (row.get('highest_severity_signal') or {}).get('score', 0)))
    video, segment = entry['video_id'], entry['segment_id']
    title = Path(str(entry['source_video']).replace('\\', '/')).name
    start, end = entry.get('timestamp_start', 0), entry.get('timestamp_end', 0)
    links = [('Orient: video timeline', f'visualizations/timeline/video_timeline_{video}.html'),
             (f'Inspect segment: {start:.2f}–{end:.2f} sec', f'visualizations/timeline/segment_context_{video}_{segment}.html'),
             ('Check temporal evidence', 'visualizations/temporal_evidence_index.html'),
             ('Trace recommendation evidence', 'visualizations/recommendation_traceability.html')]
    links = [(label, target) for label, target in links if (package_root / target).is_file()]
    signal = entry.get('highest_severity_signal') or {}
    metric_rows = ''.join(f"<li>{escape(str(row.get('signal')))}: {escape(str(row.get('score')))}</li>" for row in entry.get('strongest_signals') or [])
    trace_path = package_root / 'recommendations/recommendation_traceability.json'
    traces = json.loads(trace_path.read_text(encoding='utf-8')).get('traceability_entries', []) if trace_path.is_file() else []
    matching = [row for row in traces if any(item.get('video_id') == video and item.get('segment_id') == segment for item in row.get('affected_segments') or [])]
    recommendation = matching[0] if matching else {}
    recommendation_html = ''
    if recommendation:
        recommendation_html = f"<section><h2>Recommendation to assess</h2><p>{escape(str(recommendation.get('title')))} ({escape(str(recommendation.get('recommendation_id')))})</p><p>{escape(str(recommendation.get('recommended_next_action') or 'Review the segment in context before deciding.'))}</p><p>Lowest-risk path: {escape(str(recommendation.get('lowest_risk_optimization_path') or 'Record a review decision before editing.'))}</p><p><a href='recommendations/recommendation_traceability.json'>Source recommendation registry</a></p></section>"
    recommendation_html = recommendation_html.replace('<section>', '<section id="segment-recommendation">', 1)
    # Scope the short route to this segment; unfiltered galleries are optional.
    links = links[:2] + [('Check this segment’s recorded evidence', '#segment-evidence')]
    if recommendation:
        links.append(('Assess the segment-matched recommendation', '#segment-recommendation'))
    steps = ''.join(f'<li><a href="{escape(target, quote=True)}">{escape(label)}</a></li>' for label, target in links)
    galleries = ''.join(f'<li><a href="{target}">{label}</a></li>' for label, target in [('Full temporal evidence gallery', 'visualizations/temporal_evidence_index.html'), ('Full recommendation traceability gallery', 'visualizations/recommendation_traceability.html')] if (package_root / target).is_file())
    recommendations = ', '.join(dict.fromkeys(entry.get('recommendations') or []))
    body = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Five-minute evidence walkthrough</title><style>body{{font-family:Arial,sans-serif;max-width:960px;margin:32px auto;padding:0 20px;line-height:1.6}}section{{border:1px solid #ddd;padding:20px;margin:20px 0}}li{{margin:12px 0}}a{{color:#245f86}}button{{padding:10px}}</style></head><body>
<p><a href="index.html">Package home</a></p><h1>Five-minute evidence walkthrough</h1><h2>{escape(title)}</h2>
<p>Finding to inspect: <strong>{escape(str(signal.get('signal')))} / {escape(str(signal.get('severity')))}</strong> at {start:.2f}–{end:.2f} sec.
Recommendations recorded in the source analysis: {escape(recommendations)}.</p>
<p>These are deterministic editorial heuristics, not verified audience outcomes or autonomous editing decisions. This is a saved analysis snapshot; original video playback is intentionally not bundled.</p>
<section><h2>Follow the evidence (about 3 minutes)</h2><ol>{steps}</ol><p>Use Back to return here after opening the timeline or segment context. Compare the segment context with its cited evidence; do not treat a severity label as a conclusion.</p></section>
<section id="segment-evidence"><h2>Recorded segment signals</h2><ul>{metric_rows}</ul><p>Scores are heuristic indicators, not probabilities. Original per-video source references remain provenance; their files are not necessarily bundled.</p><p><a href="timeline/temporal_evidence_index.json">Source temporal evidence registry</a></p></section>{recommendation_html}
<section><h2>Record a decision (about 2 minutes)</h2><ul><li><label><input type="checkbox"> Segment and evidence inspected</label></li><li><label><input type="checkbox"> Recommendation accepted, rejected, or left open with reasons</label></li></ul>
<p>Suggested review question: should this region be tightened or preserved? Record uncertainty and confirm against original media before editing.</p></section>{notes_panel()}
<p><a href="validation/portable_fallback_link_audit.json">Fallback-link audit</a>: missing placeholders are disclosed separately from broken-link validation.</p></body></html>"""
    body = body.replace('</body>', f'<details><summary>Optional corpus-wide galleries</summary><ul>{galleries}</ul></details></body>')
    (package_root / 'demo_walkthrough.html').write_text(body, encoding='utf-8')
    report = {'available': True, 'video_title': title, 'video_id': video, 'segment_id': segment, 'timestamp_start': start, 'timestamp_end': end, 'recommendation_id': recommendation.get('recommendation_id'), 'steps': [{'label': label, 'page': target} for label, target in links], 'notes_persistence': 'explicit_download_only'}
    write_json(package_root / 'demo_walkthrough.json', report)
    return report


def main(argv=None) -> int:
    """Refresh presentation on a completed export without recomputing analysis."""
    import argparse
    from portable_export_package import write_master_index
    from portable_metadata_compaction import main as compact_main
    from reviewer_workspace import build_reviewer_workspace
    from review_session_workflows import build_review_sessions
    from executive_synthesis_engine import build_executive_synthesis
    from synthetic_dashboard_generator import build_synthetic_dashboards
    from pre_rc_readiness_review import build_pre_rc_readiness_review

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--published-root', type=Path)
    parser.add_argument('--zip', action='store_true')
    parser.add_argument('--validate-extracted', action='store_true')
    args = parser.parse_args(argv)
    if args.validate_extracted and not args.zip:
        parser.error('--validate-extracted requires --zip')
    root = args.package.resolve()

    def load(name):
        return json.loads((root / f'{name}.json').read_text(encoding='utf-8'))

    manifest = load('portable_package_manifest')
    if args.published_root:
        manifest['package_root'] = args.published_root.resolve().as_posix()
        manifest['zip_path'] = args.published_root.resolve().with_suffix('.zip').as_posix() if args.zip else manifest.get('zip_path')
    build_demo_walkthrough(root)
    governance = {name: load(name) for name in ('dashboard_governance_registry', 'artifact_importance_registry', 'artifact_orphan_registry', 'review_pathways', 'dashboard_consolidation_report', 'review_coherence_report')}
    governance['topology_page'] = load('governance/dashboard_governance_summary')['topology_page']
    sessions = build_review_sessions(root, governance, load('topology_graph_registry'))
    reduction, changes, validation = load('artifact_reduction_report'), load('change_intelligence_report'), load('portable_package_validation_report')
    dashboards = build_synthetic_dashboards(root, governance, reduction, density=manifest.get('dashboard_density', 'balanced'))
    synthesis = build_executive_synthesis(root, manifest, validation, governance, review_style=manifest.get('review_style', 'balanced'), change_intelligence=changes, reduction=reduction)
    build_reviewer_workspace(root, synthesis, synthesis['review_priority_registry'], sessions, enabled=manifest.get('review_workspace_enabled', False), checklists_enabled=manifest.get('review_checklists_enabled', False), handoff_enabled=manifest.get('handoff_summary_enabled', False))
    pre_rc = build_pre_rc_readiness_review(root, validation, dashboards['dashboard_consistency_validation'], reduction, synthesis['executive_synthesis_report'])
    write_master_index(root, manifest, validation, governance, sessions, synthesis, reduction, changes, pre_rc)
    source = Path(manifest['source_analysis_root'])
    audit = audit_fallback_links(root, source, manifest['export_profile'])
    manifest['fallback_link_summary'] = audit['summary']
    write_json(root / 'portable_package_manifest.json', manifest)
    arguments = ['--package', str(root)]
    if args.zip:
        arguments.append('--zip')
    if args.validate_extracted:
        arguments.append('--validate-extracted')
    return compact_main(arguments)


if __name__ == '__main__':
    raise SystemExit(main())
