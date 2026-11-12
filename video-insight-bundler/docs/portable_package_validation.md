# Portable Package Validation

Validation writes root and `validation/` reports. It checks required package files, local link resolution, image/CSS/JS availability, JSON and manifest references, absence of absolute live paths, absence of remote dependencies, raw-media exclusion, checksums, giant board preservation, interpretation preservation, schemas, validation evidence, exclusions, and privacy-risky filenames.

Key reports:

- `portable_package_validation_report.json`
- `validation/portable_integrity_report.json`
- `validation/offline_dashboard_hardening_report.json`
- `validation/portable_privacy_scan_report.json`
- `manifests/asset_dependency_report.json`
- `package_diff_report.json`
- `package_size_report.json`
- `exclusion_manifest.json`
