# Incremental Validation System

Incremental validation is represented by deterministic manifests rather than a background service.

The validation index records artifact path, artifact hash, schema path, dependency scope, cache key, and validation state. Cached validation is reusable only while the artifact hash and schema reference remain unchanged.
