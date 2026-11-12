# Interpretation Safety Filter

The safety filter flags forbidden claims such as true emotion diagnosis, identity verification, face or voice recognition claims, demographic inference, certain viewer-behavior prediction, autonomous editing, media/timeline mutation, blocker resolution, and readiness changes.

Unsafe LLM text is not rendered as authoritative interpretation. The page receives deterministic fallback text, while safety and provenance registries preserve the rejection state for review.
