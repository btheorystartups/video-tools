# Offline Dashboard Package

Portable dashboards are static and should open from `file://` without Python, a server, internet access, CDN dependencies, source videos, or repository-relative assumptions.

The hardening step rewrites live references to local package-relative paths, mirrors local CSS/JS under `assets/`, and reports remote dependencies in `validation/offline_dashboard_hardening_report.json`.

Open `portable_review_package/index.html` first. It links to the dashboard inventory, graph inventory, board/contact sheet inventory, interpretation/evidence/recommendation/governance artifacts, timelines, schemas, manifests, and validation reports.
