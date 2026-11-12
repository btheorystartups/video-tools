# LLM-Assisted Interpretation System

Phase V54 allows controlled generation-time interpretation text for graph and page explanation. Modes are `disabled`, `deterministic_fallback`, `mock_llm`, and `external_llm_provider_configured`.

LLM output is advisory only. It is prompt-captured, response-captured, safety-scanned, provenance-linked, and replaced by deterministic fallback when unavailable or unsafe. It cannot mutate media, timelines, recommendations, blockers, governance state, or readiness.
