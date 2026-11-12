# Selective Regeneration System

Selective regeneration is modeled as explicit local scopes: adjudication only, dashboards only, queue artifacts only, validation only, and operations only.

Each scope lists affected artifacts and points back to the generation dependency registry and artifact operational index. The system does not infer or execute hidden reruns; a human operator must choose the scope.
