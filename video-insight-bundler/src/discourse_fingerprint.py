"""Recurring discourse signature analysis."""

from __future__ import annotations

from intelligence_common import avg, base_artifact, deterministic_id


def build_discourse_fingerprint(analyses: list[dict]) -> dict:
    rows = []
    for analysis in analyses:
        discourse = analysis.get("discourse_state") or {}
        argument = analysis.get("argument_graph") or {}
        callback = analysis.get("callback_resolution") or {}
        rows.append(
            {
                "discourse_fingerprint_id": deterministic_id("DISCFP", analysis.get("analysis_dir"), discourse.get("discourse_pressure_score"), argument.get("argument_completeness_score")),
                "analysis_dir": analysis.get("analysis_dir"),
                "discourse_pressure_signature": discourse.get("discourse_pressure_score"),
                "argument_completeness_signature": argument.get("argument_completeness_score"),
                "callback_resolution_signature": callback.get("payoff_quality_score"),
                "unresolved_chain_count": len(argument.get("unresolved_chains") or []),
            }
        )
    output = base_artifact(method="deterministic_discourse_fingerprint_v1")
    output.update(
        {
            "discourse_fingerprints": rows,
            "summary": {
                "analysis_count": len(rows),
                "mean_discourse_pressure": avg([row.get("discourse_pressure_signature") for row in rows]),
                "mean_argument_completeness": avg([row.get("argument_completeness_signature") for row in rows]),
            },
        }
    )
    return output
