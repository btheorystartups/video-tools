# Incremental Zip And Delta Export

V68 keeps normal full zip behavior compatible and adds safer delta-aware packaging.

CLI flags: `--zip-mode full|optimized|delta`, `--delta-zip`, `--base-export <path>`, and `--reuse-zip-manifest`.

Generated files: `zip_assembly_report.json`, `zip_delta_manifest.json`, and `export_delta_package_manifest.json`.

The default remains full zip behavior. `delta` writes a sidecar delta zip containing changed/new files, a removed-file manifest, and apply instructions.
