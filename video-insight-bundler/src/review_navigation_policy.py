"""Navigation wrappers and exclusion notices are not analytical findings."""


def is_analytical_review_target(path: str | None) -> bool:
    return bool(path) and path.replace('\\', '/').removeprefix('./') not in {
        'index.html', 'missing_asset_placeholder.html', 'raw_media_excluded.html',
        'demo_walkthrough.html', 'review_session_workbench.html',
    }
