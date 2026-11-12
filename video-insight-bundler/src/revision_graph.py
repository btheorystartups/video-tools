"""Deterministic editorial revision graph orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from branch_comparison import compare_branches
from editorial_constraints import evaluate_editorial_constraints
from release_readiness import compute_release_readiness
from revision_delta import build_revision_deltas
from revision_visualization import write_revision_visualizations
from stability import canonical_json, sha256_text, utc_now_iso, write_json


CORE_ARTIFACTS = [
    "transcript.json",
    "audio_features.json",
    "acoustic_features.json",
    "topic_analysis.json",
    "rhetorical_analysis.json",
    "scene_segments.json",
    "emotional_arc.json",
    "recommendations.json",
    "reports/quality_report.json",
    "reports/segment_boundary_report.json",
    "consensus/evidence_consensus.json",
    "consensus/transition_confidence.json",
    "consensus/evidence_score_summary.json",
    "consensus/false_positive_boundaries.json",
    "consensus/continuity_analysis.json",
    "discourse/discourse_state.json",
    "discourse/argument_graph.json",
    "discourse/narrative_memory.json",
    "discourse/callback_resolution.json",
    "discourse/editorial_ambiguity.json",
    "discourse/discourse_summary.json",
    "visual_structure/visual_structure.json",
    "visual_structure/shot_boundaries.json",
    "visual_structure/visual_continuity.json",
    "visual_structure/composition_features.json",
    "visual_structure/visual_boundary_alignment.json",
    "sequence/sequence_structure.json",
    "sequence/temporal_rhythm.json",
    "sequence/editorial_pressure.json",
    "sequence/recommendation_dependencies.json",
    "sequence/revision_propagation.json",
    "sequence/counterfactual_simulation.json",
    "sequence/epistemic_stability.json",
    "comparative/multi_video_analysis.json",
    "comparative/style_fingerprint.json",
    "comparative/creator_evolution.json",
    "comparative/structural_pattern_mining.json",
    "comparative/semantic_equivalence_scaffolding.json",
]

MUTATION_CLASS_SCORES = {
    "SAFE_ANALYSIS_ONLY": 1.0,
    "SAFE_METADATA_ONLY": 0.95,
    "SAFE_REPORT_ONLY": 0.92,
    "REQUIRES_HUMAN_REVIEW": 0.72,
    "REQUIRES_RERENDER": 0.45,
    "REQUIRES_REINSERTION": 0.38,
    "REQUIRES_TIMELINE_MUTATION": 0.25,
    "UNSAFE_WITHOUT_BACKUP": 0.05,
}


def load_revision_profile(path: Path | None) -> dict:
    if path is None:
        path = Path(__file__).resolve().parent.parent / "config" / "revision_profile.default.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _short_hash(data: Any) -> str:
    return sha256_text(canonical_json(data))[:16]


def _file_hashes(output_dir: Path) -> dict:
    hashes = {}
    for rel in CORE_ARTIFACTS:
        path = output_dir / rel
        if path.exists() and path.is_file():
            hashes[rel] = sha256_text(path.read_text(encoding="utf-8", errors="replace"))
    return hashes


def _revision_id(seed: dict) -> str:
    return f"REV_{_short_hash(seed)}"


def _candidate_id(seed: dict) -> str:
    return f"CAND_{_short_hash(seed)}"


def _state_summary(bundle, report_data: dict, readiness: dict) -> dict:
    quality = report_data.get("quality_scores", {})
    topic = getattr(bundle, "topic_analysis", None) or {}
    rhetoric = getattr(bundle, "rhetorical_analysis", None) or {}
    acoustic = getattr(bundle, "acoustic_features", None) or {}
    return {
        "transcript_quality": quality.get("transcript_quality"),
        "segmentation_smoothness": quality.get("segmentation_smoothness"),
        "acoustic_completeness": readiness.get("score_components", {}).get("acoustic_completeness"),
        "topic_continuity": readiness.get("score_components", {}).get("topic_continuity"),
        "topic_drift_score": topic.get("topic_drift_score"),
        "rhetorical_balance": rhetoric.get("rhetorical_balance_score"),
        "silence_ratio": acoustic.get("silence_ratio"),
        "recommendation_confidence": quality.get("recommendation_confidence"),
        "argument_completeness": (getattr(bundle, "argument_graph", None) or {}).get("argument_completeness_score"),
        "callback_resolution_quality": (getattr(bundle, "callback_resolution", None) or {}).get("payoff_quality_score"),
        "ambiguity_adjusted_continuity": (getattr(bundle, "discourse_summary", None) or {}).get("ambiguity_adjusted_continuity"),
        "visual_continuity_score": (getattr(bundle, "visual_continuity", None) or {}).get("visual_continuity_score"),
        "visual_boundary_alignment_quality": (getattr(bundle, "visual_structure", None) or {}).get("visual_boundary_alignment_quality"),
        "visual_contradiction_pressure": ((getattr(bundle, "visual_boundary_alignment", None) or {}).get("summary") or {}).get("mean_visual_contradiction"),
    }


def _root_observed_revision(bundle, report_data: dict, constraints: dict, readiness: dict, artifact_hashes: dict) -> dict:
    seed = {
        "source_video_sha256": bundle.media_metadata.get("sha256"),
        "analysis_profile_hash": bundle.profile_hash,
        "artifact_hashes": artifact_hashes,
        "revision_type": "baseline_observation",
    }
    revision_id = _revision_id(seed)
    return {
        "revision_id": revision_id,
        "parent_revision_id": None,
        "root_revision_id": revision_id,
        "revision_label": "Root Observed Analysis",
        "revision_type": "baseline_observation",
        "revision_status": "observed",
        "created_at_utc": utc_now_iso(),
        "source_video_sha256": bundle.media_metadata.get("sha256"),
        "analysis_profile_hash": bundle.profile_hash,
        "input_artifact_hashes": artifact_hashes,
        "inherited_artifacts": sorted(artifact_hashes),
        "changed_artifacts": [],
        "proposed_changes": [],
        "simulated_outputs": {
            "current_transcript_state": bundle.transcript.get("transcription_status"),
            "current_acoustic_state": (getattr(bundle, "acoustic_features", None) or {}).get("analysis_status"),
            "current_topic_state": (getattr(bundle, "topic_analysis", None) or {}).get("analysis_status"),
            "current_rhetorical_state": (getattr(bundle, "rhetorical_analysis", None) or {}).get("analysis_status"),
            "current_segment_count": bundle.scene_segments.get("segment_count"),
            "current_recommendation_count": len((getattr(bundle, "recommendations_json", None) or {}).get("recommendations", [])),
        },
        "score_summary": _state_summary(bundle, report_data, readiness),
        "constraint_summary": constraints.get("summary", {}),
        "release_readiness": readiness,
        "mutation_safety": {
            "mutation_safety_class": "SAFE_ANALYSIS_ONLY",
            "status": "observed_artifacts_only",
            "why": "Root revision records the completed analysis state and performs no mutation.",
        },
        "warnings": bundle.warnings,
        "limitations": [
            "Observed revision reflects generated analysis artifacts, not a production edit state.",
            "Revision graph timestamps are metadata and do not affect deterministic revision IDs.",
        ],
    }


def _top_recommendation(bundle) -> dict:
    rows = (getattr(bundle, "recommendations_json", None) or {}).get("recommendations") or []
    return rows[0] if rows else {}


def _affected_segments(bundle) -> list[str]:
    rec = _top_recommendation(bundle)
    if rec.get("affected_segment_ids"):
        return rec["affected_segment_ids"]
    return [row.get("segment_id") for row in (bundle.scene_segments.get("segments") or [])[:2] if row.get("segment_id")]


def _candidate_seed(bundle, parent_revision_id: str, label: str, changes: list[dict]) -> dict:
    return {
        "source_video_sha256": bundle.media_metadata.get("sha256"),
        "analysis_profile_hash": bundle.profile_hash,
        "parent_revision_id": parent_revision_id,
        "candidate_label": label,
        "proposed_changes": changes,
    }


def _make_candidate(
    bundle,
    root_revision: dict,
    label: str,
    objective: str,
    changes: list[dict],
    affected_metrics: list[str],
    readiness: dict,
    mutation_safety_class: str,
    identity_preservation_score: float,
    render_required: bool,
    reinsertion_required: bool,
    why_not_more_aggressive: str,
    risk_summary: list[str],
    human_review_required: bool,
    rollback_complexity: str,
) -> dict:
    seed = _candidate_seed(bundle, root_revision["revision_id"], label, changes)
    candidate_id = _candidate_id(seed)
    simulated_revision_id = _revision_id({**seed, "candidate_id": candidate_id, "revision_status": "simulated"})
    baseline_score = root_revision["release_readiness"]["release_readiness_score"]
    predicted_score = readiness["release_readiness_score"]
    return {
        "candidate_id": candidate_id,
        "parent_revision_id": root_revision["revision_id"],
        "simulated_revision_id": simulated_revision_id,
        "candidate_label": label,
        "proposal_status": "proposed",
        "objective": objective,
        "proposed_changes": changes,
        "affected_segments": _affected_segments(bundle),
        "affected_metrics": affected_metrics,
        "predicted_score_delta": round(predicted_score - baseline_score, 3),
        "predicted_release_readiness": readiness,
        "mutation_safety_class": mutation_safety_class,
        "mutation_safety_score": MUTATION_CLASS_SCORES.get(mutation_safety_class, 0.2),
        "render_required": render_required,
        "reinsertion_required": reinsertion_required,
        "identity_preservation_score": round(identity_preservation_score, 3),
        "identity_change_risk": round(1.0 - identity_preservation_score, 3),
        "human_review_required": human_review_required,
        "rollback_complexity": rollback_complexity,
        "risk_summary": risk_summary,
        "why_not_more_aggressive": why_not_more_aggressive,
        "evidence": [
            f"Root revision: {root_revision['revision_id']}",
            f"Top recommendation: {_top_recommendation(bundle).get('issue_type', 'none')}",
            "Candidate is proposal-only and does not apply edits.",
        ],
    }


def _candidate_readiness(bundle, report_data: dict, revision_profile: dict, root_constraints: dict, adjustments: dict, safety: float, identity: float) -> dict:
    return compute_release_readiness(
        bundle,
        report_data,
        root_constraints,
        revision_profile,
        mutation_safety_score=safety,
        identity_preservation_score=identity,
        candidate_adjustments=adjustments,
    )


def build_revision_candidates(bundle, report_data: dict, revision_profile: dict, root_revision: dict, root_constraints: dict) -> list[dict]:
    rec = _top_recommendation(bundle)
    top_issue = rec.get("issue_type", "general_review")
    rec_segments = rec.get("affected_segment_ids") or _affected_segments(bundle)
    candidate_specs = [
        (
            "Candidate_A_Minimal",
            "Smallest safe planning change likely to improve readiness without media, timing, or render mutation.",
            [
                {
                    "change_type": "metadata",
                    "field": "revision_recommendation_priority",
                    "description": f"Promote the top evidence-ranked recommendation for human review: {top_issue}.",
                    "affected_artifacts": ["recommendations.json", "reports/revision_graph_summary.md"],
                    "explicit_timing_change": False,
                },
                {
                    "change_type": "recommendation",
                    "field": "next_best_action",
                    "description": "Add a proposal-only next action that preserves source media and timing.",
                    "affected_artifacts": ["revision_graph/revision_recommendations.json"],
                    "explicit_timing_change": False,
                },
            ],
            ["recommendation_confidence", "constraint_pass_rate"],
            {"recommendation_confidence": 0.08, "constraint_pass_rate": 0.07, "warning_severity": 0.02},
            "SAFE_METADATA_ONLY",
            0.985,
            False,
            False,
            "More aggressive changes are deferred because the minimal branch must remain metadata-only and render-free.",
            ["Low risk; still requires human review before treating recommendations as edit instructions."],
            False,
            "low",
        ),
        (
            "Candidate_B_Conservative",
            "Moderate proposal to review boundaries, signposts, and top recommendation areas while preserving source identity.",
            [
                {
                    "change_type": "recommendation",
                    "field": "segment_review_plan",
                    "description": "Create a human review plan for affected segments and weak constraints.",
                    "affected_artifacts": ["revision_graph/revision_candidates.json", "reports/branch_comparison_summary.md"],
                    "explicit_timing_change": False,
                },
                {
                    "change_type": "analysis_only",
                    "field": "constraint_review",
                    "description": "Simulate improved constraint pressure after targeted review annotations.",
                    "affected_artifacts": ["revision_graph/editorial_constraints.json"],
                    "explicit_timing_change": False,
                },
            ],
            ["segmentation_smoothness", "topic_continuity", "rhetorical_balance", "recommendation_confidence"],
            {"segmentation_smoothness": 0.04, "topic_continuity": 0.035, "rhetorical_balance": 0.035, "recommendation_confidence": 0.04, "constraint_pass_rate": 0.035},
            "REQUIRES_HUMAN_REVIEW",
            0.94,
            False,
            False,
            "A stronger rewrite or recut may score higher but could change argument identity without reviewed intent.",
            ["Moderate risk because humans must interpret and approve segment-level changes."],
            True,
            "medium",
        ),
        (
            "Candidate_C_Highest_Readiness",
            "Stronger simulated intervention that may maximize readiness but explicitly carries identity and render risk.",
            [
                {
                    "change_type": "timing",
                    "field": "future_timing_adjustment",
                    "description": "Simulate tightening or restructuring affected segments in a future edit pass.",
                    "affected_artifacts": ["scene_segments.json", "revision_graph/revision_deltas.json"],
                    "explicit_timing_change": True,
                },
                {
                    "change_type": "media",
                    "field": "future_render_review",
                    "description": "Flag that a real edit would require rerender/reinsertion review before application.",
                    "affected_artifacts": ["revision_graph/mutation_safety_contract.json"],
                    "explicit_timing_change": True,
                },
            ],
            ["segmentation_smoothness", "topic_continuity", "rhetorical_balance", "pacing_consistency"],
            {"segmentation_smoothness": 0.07, "topic_continuity": 0.055, "rhetorical_balance": 0.055, "recommendation_confidence": 0.045, "constraint_pass_rate": 0.04},
            "REQUIRES_RERENDER",
            0.76,
            True,
            True,
            "This branch is intentionally not recommended by default because it may change editorial identity and requires render/reinsertion safeguards.",
            ["High identity-change risk.", "Would require explicit backup, rerender validation, and human approval before any application."],
            True,
            "high",
        ),
        (
            "Candidate_D_No_Change",
            "Baseline comparison branch for deterministic diffing.",
            [
                {
                    "change_type": "analysis_only",
                    "field": "no_change_baseline",
                    "description": "Preserve the observed analysis state for branch comparison.",
                    "affected_artifacts": ["revision_graph/branch_comparison_report.json"],
                    "explicit_timing_change": False,
                }
            ],
            [],
            {},
            "SAFE_ANALYSIS_ONLY",
            1.0,
            False,
            False,
            "No-change branch is intentionally non-aggressive and serves as a comparison anchor.",
            ["No mutation risk; no expected readiness improvement."],
            False,
            "low",
        ),
        (
            "Candidate_E_Visual_Reset_Review",
            "Human-review-only visual reset proposal when visual and discourse boundary evidence disagree.",
            [
                {
                    "change_type": "visual_reset_suggestion",
                    "field": "visual_boundary_review_plan",
                    "description": "Flag visually unsupported rhetorical boundaries and visual-only jumps for human review.",
                    "affected_artifacts": ["visual_structure/visual_boundary_alignment.json", "recommendations.json", "revision_graph/revision_candidates.json"],
                    "explicit_timing_change": False,
                },
                {
                    "change_type": "human_review_only_visual_issue",
                    "field": "non_mutating_visual_review",
                    "description": "Classify the issue as review-only unless an external editor explicitly approves a visual intervention.",
                    "affected_artifacts": ["revision_graph/mutation_safety_contract.json"],
                    "explicit_timing_change": False,
                },
            ],
            ["visual_boundary_alignment_quality", "visual_contradiction_pressure", "visual_reset_support"],
            {"visual_boundary_alignment_quality": 0.045, "visual_contradiction_pressure": 0.04, "visual_reset_support": 0.035, "recommendation_confidence": 0.025},
            "REQUIRES_HUMAN_REVIEW",
            0.93,
            False,
            False,
            "Actual visual intervention may require rerendering and is outside this proposal-only local analysis pass.",
            ["Moderate risk because visual reset choices require editorial judgment.", "No media or timeline mutation is performed."],
            True,
            "medium",
        ),
        (
            "Candidate_F_Rerender_Required_Visual_Intervention",
            "Explicitly separated future branch for visual interventions that would require rendering outside this tool.",
            [
                {
                    "change_type": "rerender_required_visual_intervention",
                    "field": "future_visual_insert_or_reset",
                    "description": "Simulate adding or replacing visual support in a future external edit pass.",
                    "affected_artifacts": ["visual_structure/visual_boundary_alignment.json", "revision_graph/revision_deltas.json"],
                    "explicit_timing_change": True,
                }
            ],
            ["visual_continuity_quality", "visual_boundary_alignment_quality"],
            {"visual_boundary_alignment_quality": 0.055, "visual_continuity_quality": 0.04, "visual_reset_support": 0.05},
            "REQUIRES_RERENDER",
            0.74,
            True,
            True,
            "This branch is not a default recommendation because actual visual changes require media mutation outside the analyzer.",
            ["High risk: would require rerender/reinsertion safeguards and explicit human approval.", "The analyzer does not mutate media."],
            True,
            "high",
        ),
    ]
    candidates = []
    for label, objective, changes, metrics, adjustments, safety_class, identity, render_required, reinsertion_required, why, risks, review, rollback in candidate_specs:
        readiness = _candidate_readiness(bundle, report_data, revision_profile, root_constraints, adjustments, MUTATION_CLASS_SCORES[safety_class], identity)
        candidate = _make_candidate(
            bundle,
            root_revision,
            label,
            objective,
            changes,
            metrics,
            readiness,
            safety_class,
            identity,
            render_required,
            reinsertion_required,
            why,
            risks,
            review,
            rollback,
        )
        candidate["affected_segments"] = sorted(set(rec_segments))
        candidates.append(candidate)
    return candidates


def _candidate_states(bundle, root_revision: dict, candidates: list[dict]) -> list[dict]:
    states = []
    for candidate in candidates:
        states.append(
            {
                "revision_id": candidate["simulated_revision_id"],
                "parent_revision_id": root_revision["revision_id"],
                "root_revision_id": root_revision["root_revision_id"],
                "revision_label": candidate["candidate_label"],
                "revision_type": "candidate_simulation",
                "revision_status": "simulated",
                "created_at_utc": utc_now_iso(),
                "source_video_sha256": root_revision["source_video_sha256"],
                "analysis_profile_hash": root_revision["analysis_profile_hash"],
                "input_artifact_hashes": root_revision["input_artifact_hashes"],
                "inherited_artifacts": root_revision["inherited_artifacts"],
                "changed_artifacts": sorted({artifact for change in candidate.get("proposed_changes", []) for artifact in change.get("affected_artifacts", [])}),
                "proposed_changes": candidate["proposed_changes"],
                "simulated_outputs": {
                    "candidate_id": candidate["candidate_id"],
                    "render_required": candidate["render_required"],
                    "reinsertion_required": candidate["reinsertion_required"],
                    "proposal_only": True,
                    "applied": False,
                },
                "score_summary": candidate["predicted_release_readiness"].get("score_components", {}),
                "constraint_summary": {},
                "release_readiness": candidate["predicted_release_readiness"],
                "mutation_safety": {
                    "mutation_safety_class": candidate["mutation_safety_class"],
                    "proposal_only": True,
                    "why": "; ".join(candidate["risk_summary"]),
                },
                "warnings": candidate["risk_summary"],
                "limitations": [
                    "Simulated revision state; no source media, rendered media, or timeline artifact was changed.",
                    "Predicted deltas are deterministic heuristics for human review.",
                ],
            }
        )
    return states


def _mutation_safety_contract(candidates: list[dict]) -> dict:
    contracts = []
    for candidate in candidates:
        safety_class = candidate["mutation_safety_class"]
        forbidden = ["mutate source video", "mutate rendered media", "change Resolve timeline", "call cloud APIs", "mark proposal as applied"]
        if safety_class in {"SAFE_ANALYSIS_ONLY", "SAFE_METADATA_ONLY", "SAFE_REPORT_ONLY"}:
            allowed = ["write proposal artifacts", "write reports", "write static visualizations"]
            preconditions = ["None beyond retaining source artifacts and manifest hashes."]
        elif safety_class == "REQUIRES_HUMAN_REVIEW":
            allowed = ["write proposal artifacts", "prepare human review checklist"]
            preconditions = ["Human editor reviews affected segments and evidence before application."]
        else:
            allowed = ["simulation only in this pass"]
            preconditions = ["Explicit human approval", "Verified backups", "Render/reinsertion plan outside this tool"]
        contracts.append(
            {
                "candidate_id": candidate["candidate_id"],
                "candidate_label": candidate["candidate_label"],
                "mutation_safety_class": safety_class,
                "mutation_safety_score": candidate["mutation_safety_score"],
                "why": candidate["risk_summary"],
                "forbidden_operations": forbidden,
                "allowed_operations": allowed,
                "required_preconditions": preconditions,
                "rollback_requirements": ["Preserve original artifacts; discard proposal artifacts if not accepted."],
                "evidence_required_before_apply": ["Human review approval", "Stable manifest/source SHA match", "Explicit external edit plan"],
                "render_required": candidate["render_required"],
                "reinsertion_required": candidate["reinsertion_required"],
            }
        )
    return {
        "overall_status": "proposal_only_no_mutation_performed",
        "mutation_classes": sorted(MUTATION_CLASS_SCORES),
        "candidate_contracts": contracts,
        "global_forbidden_operations": ["source video mutation", "rendered media mutation", "Resolve timeline mutation", "cloud API calls", "LLM calls"],
    }


def _lineage(root_revision: dict, candidate_states: list[dict]) -> dict:
    return {
        "root_revision_id": root_revision["revision_id"],
        "nodes": [
            {"revision_id": root_revision["revision_id"], "parent_revision_id": None, "label": root_revision["revision_label"], "status": root_revision["revision_status"]}
        ]
        + [
            {"revision_id": state["revision_id"], "parent_revision_id": state["parent_revision_id"], "label": state["revision_label"], "status": state["revision_status"]}
            for state in candidate_states
        ],
        "edges": [{"from_revision_id": root_revision["revision_id"], "to_revision_id": state["revision_id"]} for state in candidate_states],
        "future_support": "Lineage model supports future multi-generation simulated branches.",
    }


def _recommendations(branch_comparison: dict, candidates: list[dict], readiness: dict) -> dict:
    recommended = branch_comparison.get("recommended_branch", {})
    safest = max(candidates, key=lambda row: (row["mutation_safety_score"], row["identity_preservation_score"], -row["predicted_score_delta"]))
    highest = max(candidates, key=lambda row: row["predicted_release_readiness"]["release_readiness_score"])
    identity = max(candidates, key=lambda row: (row["identity_preservation_score"], row["predicted_release_readiness"]["release_readiness_score"]))
    not_recommended = [
        {"candidate_label": row["candidate_label"], "reason": "Requires render/reinsertion or carries higher identity-change risk."}
        for row in candidates
        if row.get("render_required") or row.get("reinsertion_required")
    ]
    next_prompt = "Inspect branch outputs only and prepare a human-reviewed patch only if Candidate_A_Minimal evidence is accepted."
    if readiness.get("release_readiness_class") == "not_ready":
        next_prompt = "Apply no changes; improve transcript, constraints, or segmentation evidence before another simulation pass."
    return {
        "recommended_branch": recommended.get("branch_label"),
        "recommended_revision_id": recommended.get("branch_id"),
        "rationale": [
            "Recommendation balances readiness with identity preservation, mutation safety, review burden, and rollback complexity.",
            "Aggressive simulated branches are not preferred when they require render or reinsertion work.",
        ],
        "next_best_action": "Review the recommended proposal branch and verify evidence manually before considering any external edit.",
        "safest_action": safest["candidate_label"],
        "highest_score_action": highest["candidate_label"],
        "best_identity_preserving_action": identity["candidate_label"],
        "actions_not_recommended": not_recommended,
        "required_human_review": [row["candidate_label"] for row in candidates if row.get("human_review_required")],
        "suggested_next_prompt": next_prompt,
    }


def _write_revision_markdown(output_dir: Path, graph: dict) -> None:
    lines = [
        "# Revision Graph",
        "",
        "Revision graph outputs are planning and simulation artifacts. They do not apply edits, mutate media, change Resolve timelines, or guarantee publication readiness.",
        "",
        f"- Root revision: `{graph['root_revision_id']}`",
        f"- Revision count: `{len(graph['revision_states'])}`",
        f"- Recommended branch: `{graph['revision_recommendations'].get('recommended_branch')}`",
        "",
        "## Branches",
        "",
    ]
    for candidate in graph["revision_candidates"]:
        lines.append(
            f"- `{candidate['candidate_label']}` -> `{candidate['simulated_revision_id']}` "
            f"score `{candidate['predicted_release_readiness']['release_readiness_score']}`, safety `{candidate['mutation_safety_class']}`"
        )
    (output_dir / "revision_graph" / "revision_graph.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_disabled_revision_status(output_dir: Path, reason: str = "Revision graph generation disabled.") -> dict:
    revision_dir = output_dir / "revision_graph"
    revision_dir.mkdir(exist_ok=True)
    data = {
        "status": "skipped",
        "reason": reason,
        "warning": "No revision candidates were generated; no source media or timelines were mutated.",
    }
    write_json(revision_dir / "revision_graph.json", data)
    (revision_dir / "revision_graph.md").write_text(f"# Revision Graph\n\n- Status: `skipped`\n- Reason: {reason}\n", encoding="utf-8")
    return data


def build_revision_graph(bundle, report_data: dict, revision_profile: dict | None = None) -> dict:
    revision_profile = revision_profile or load_revision_profile(None)
    output_dir = bundle.output_dir
    revision_dir = output_dir / "revision_graph"
    revision_dir.mkdir(exist_ok=True)

    artifact_hashes = _file_hashes(output_dir)
    baseline_constraints = evaluate_editorial_constraints(bundle, report_data, revision_profile)
    baseline_readiness = compute_release_readiness(bundle, report_data, baseline_constraints, revision_profile)
    root_revision = _root_observed_revision(bundle, report_data, baseline_constraints, baseline_readiness, artifact_hashes)
    candidates = build_revision_candidates(bundle, report_data, revision_profile, root_revision, baseline_constraints)

    candidate_states = _candidate_states(bundle, root_revision, candidates)
    for state in candidate_states:
        candidate = next(row for row in candidates if row["simulated_revision_id"] == state["revision_id"])
        constraints = evaluate_editorial_constraints(bundle, report_data, revision_profile, candidate)
        state["constraint_summary"] = constraints.get("summary", {})

    deltas = build_revision_deltas(root_revision, candidate_states, candidates)
    lineage = _lineage(root_revision, candidate_states)
    branch_comparison = compare_branches(root_revision, candidates)
    mutation_contract = _mutation_safety_contract(candidates)
    recommendations = _recommendations(branch_comparison, candidates, baseline_readiness)

    graph = {
        "revision_graph_version": "1.0",
        "status": "complete",
        "generated_at_utc": utc_now_iso(),
        "root_revision_id": root_revision["revision_id"],
        "source_video_sha256": bundle.media_metadata.get("sha256"),
        "analysis_profile_hash": bundle.profile_hash,
        "revision_profile": revision_profile.get("profile_name"),
        "revision_states": [root_revision] + candidate_states,
        "revision_candidates": candidates,
        "revision_deltas": deltas["deltas"],
        "revision_lineage": lineage,
        "editorial_constraints": baseline_constraints,
        "release_readiness": baseline_readiness,
        "mutation_safety_contract": mutation_contract,
        "branch_comparison": branch_comparison,
        "revision_recommendations": recommendations,
        "non_mutation_guarantee": "Phase 9 writes proposal/simulation artifacts only; no source media, rendered media, Resolve timeline, database, server, cloud API, or LLM call is used.",
    }

    write_json(revision_dir / "revision_graph.json", graph)
    _write_revision_markdown(output_dir, graph)
    write_json(revision_dir / "revision_states.json", {"revision_states": graph["revision_states"]})
    write_json(revision_dir / "revision_lineage.json", lineage)
    write_json(revision_dir / "revision_candidates.json", {"revision_candidates": candidates})
    write_json(revision_dir / "revision_deltas.json", deltas)
    write_json(revision_dir / "editorial_constraints.json", baseline_constraints)
    write_json(revision_dir / "release_readiness_report.json", baseline_readiness)
    write_json(revision_dir / "mutation_safety_contract.json", mutation_contract)
    write_json(revision_dir / "branch_comparison_report.json", branch_comparison)
    write_json(revision_dir / "revision_recommendations.json", recommendations)

    visualization_status = write_revision_visualizations(output_dir, {
        "root_revision": root_revision,
        "candidates": candidates,
        "release_readiness": baseline_readiness,
        "constraints": baseline_constraints,
        "branch_comparison": branch_comparison,
        "mutation_safety_contract": mutation_contract,
        "recommendations": recommendations,
    })
    graph["visualization_status"] = visualization_status
    write_json(revision_dir / "revision_graph.json", graph)
    return graph
